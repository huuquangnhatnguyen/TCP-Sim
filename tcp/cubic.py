import simpy
from core.link import Link
from core.packet import Packet
from core.logger import LoggerFactory
import math


class CubicFlow:
    """
    Simplified TCP CUBIC flow for your simulator.

    - Uses Reno-like slow start initially (cwnd doubling each RTT).
    - After that, cwnd evolution in congestion avoidance is governed by the
      CUBIC function W_cubic(t).
    - Loss reaction uses CUBIC's multiplicative decrease with beta.
    """

    def __init__(
        self,
        env: simpy.Environment,
        link: Link,
        flow_id: int = 0,
        logger: LoggerFactory = None,
        num_packets: int = 10000,
        rto: float = 1.0,
    ):
        # Wiring
        self.env = env
        self.link = link
        self.flow_id = flow_id
        self.logger = logger if logger is not None else LoggerFactory()

        # Flow size / termination
        self.num_packets = num_packets
        self.rto = rto

        # Congestion control state
        self.state = "SLOW_START"     # "SLOW_START" | "CUBIC_CA" | "FAST_RECOVERY"
        self.cwnd = 1.0               # float; in packets
        self.ssthresh = 64.0          # threshold to exit slow start
        self.unacked = {}             # seq -> Packet
        self.seq = 0                  # next seq to send

        # ACK / receiver state (same idea as RenoFlow)
        self.last_ack = -1            # last cumulatively ACKed seq
        self.dup_ack_count = 0
        self.next_seq = 0             # next expected in-order seq
        self.valid_ack_count = 0      # in-order delivered packets
        self.received_seqs = set()    # buffer of received seqs

        # CUBIC parameters
        self.C = 0.4
        self.beta = 0.7
        self.W_max = 0.0              # cwnd just before last loss
        self.epoch_start = None       # env.now when cubic epoch started
        self.K = 0.0                  # computed from W_max

        # Start processes
        self.env.process(self.sender())
        self.env.process(self.timer())

    # ------------------------------------------------------------------
    # Core processes
    # ------------------------------------------------------------------
    def sender(self):
        """Continuously send while cwnd allows and we still have packets to send."""
        while True:
            # Optional: stop when all sent & all acked
            if self.seq >= self.num_packets and not self.unacked:
                self.logger.record_event(self.env.now, "SENDER_DONE", {
                    "flow": self.flow_id,
                    "last_seq": self.seq - 1
                })
                break

            if self.can_send() and self.seq < self.num_packets:
                pkt = Packet(
                    seq=self.seq,
                    size_bytes=1500,
                    flow=self,
                )
                self.seq += 1
                self.unacked[pkt.seq] = pkt
                pkt.send_time = self.env.now

                self.logger.record_packet_sent(self.env.now, self.flow_id, pkt.seq)
                self.logger.record_queue(self.env.now, self.flow_id,
                                         len(self.link.queue.items))

                yield self.env.process(self.link.enqueue(pkt))

            # pacing
            yield self.env.timeout(0.001)

    def timer(self):
        """Retransmission timer: timeout when oldest unacked packet age >= RTO."""
        while True:
            yield self.env.timeout(self.rto / 2.0)

            oldest = self.oldest_unacked_send_time()
            if oldest is None:
                continue

            if self.env.now - oldest >= self.rto:
                self.handle_timeout()

    # ------------------------------------------------------------------
    # Receiver & ACK side (cumulative ACKs with OOO buffering)
    # ------------------------------------------------------------------
    def on_packet_arrival(self, pkt: Packet):
        """
        Receiver-side cumulative ACK with simple out-of-order buffering.

        - Track every seq in received_seqs.
        - Advance next_seq while we have contiguous data.
        - ACK last in-order seq: ack_seq = next_seq - 1.
        """
        self.received_seqs.add(pkt.seq)

        advanced = False
        while self.next_seq in self.received_seqs:
            self.next_seq += 1
            advanced = True

        if advanced:
            self.valid_ack_count = max(self.valid_ack_count, self.next_seq)

        ack_seq = self.next_seq - 1
        self.on_ack(ack_seq)
        self.logger.record_ack(self.env.now, self.flow_id, ack_seq)

        # if self.valid_ack_count >= self.num_packets:
        #     self.logger.record_event(self.env.now, "STOP_CONDITION_REACHED", {
        #         "flow": self.flow_id,
        #         "acked": self.valid_ack_count
        #     })
        #     self.env.exit()

    def on_ack(self, ack_seq: int):
        """CUBIC ACK handler (new ACK vs dupACK)."""
        if ack_seq < self.last_ack:
            return

        # -------------------------
        # NEW ACK
        # -------------------------
        if ack_seq > self.last_ack:
            # Remove acked packets and log RTT
            for seq in list(self.unacked.keys()):
                if seq <= ack_seq:
                    pkt = self.unacked.pop(seq)
                    if pkt.send_time is not None:
                        rtt_sample = self.env.now - pkt.send_time
                        self.logger.record_event(
                            time=self.env.now,
                            event_type="rtt_sample",
                            details={"flow": self.flow_id,
                                     "seq": seq,
                                     "rtt": rtt_sample},
                        )

            self.dup_ack_count = 0

            # Congestion control
            if self.state == "SLOW_START":
                self.cwnd += 1.0
                if self.cwnd >= self.ssthresh:
                    self.state = "CUBIC_CA"
                    self.epoch_start = None  # start a new cubic epoch on first CA ACK
                    self.logger.record_event(self.env.now, "CC_STATE_CHANGE", {
                        "flow": self.flow_id, "new_state": self.state
                    })
            elif self.state in ("CUBIC_CA", "FAST_RECOVERY"):
                # In CUBIC, cwnd in CA is governed by cubic function of time
                self.cubic_update_on_new_ack()

                # If we were in FR and this ACK covers the loss, go back to CA
                if self.state == "FAST_RECOVERY":
                    self.state = "CUBIC_CA"
                    self.logger.record_event(self.env.now, "CC_STATE_CHANGE", {
                        "flow": self.flow_id, "new_state": self.state
                    })

            self.last_ack = ack_seq
            self.logger.record_cwnd(self.env.now, self.flow_id, self.cwnd)
            return

        # -------------------------
        # DUPLICATE ACK
        # -------------------------
        if ack_seq == self.last_ack:
            self.dup_ack_count += 1

            if self.dup_ack_count == 3 and self.state != "FAST_RECOVERY":
                self.handle_fast_retransmit(ack_seq)
            elif self.state == "FAST_RECOVERY":
                # In FR, additional dupACKs slightly inflate cwnd
                self.cwnd += 1.0
                self.logger.record_cwnd(self.env.now, self.flow_id, self.cwnd)

    # ------------------------------------------------------------------
    # CUBIC core: update cwnd on new ACK in CA/FR
    # ------------------------------------------------------------------
    def cubic_update_on_new_ack(self):
        """
        Simplified CUBIC window update on each new ACK.

        W_cubic(t) = C (t - K)^3 + W_max, t in seconds since epoch_start.
        """
        now = self.env.now

        # Initialize cubic epoch
        if self.epoch_start is None:
            self.epoch_start = now
            # At start of epoch, W_max is "cwnd just before last loss".
            # If this is first epoch, use current cwnd.
            if self.W_max == 0.0:
                self.W_max = self.cwnd
            # Compute K = cubic_root(W_max * (1 - beta) / C)
            self.K = 0.0
            if self.W_max > 0.0:
                self.K = (self.W_max * (1.0 - self.beta) / self.C) ** (1.0 / 3.0)

        t = now - self.epoch_start
        # CUBIC window
        W_cubic = self.C * (t - self.K) ** 3 + self.W_max
        if W_cubic < 1.0:
            W_cubic = 1.0

        # Simple, stable update rule for cwnd:
        # move cwnd gradually towards W_cubic (no more than +1 per ACK)
        if W_cubic > self.cwnd:
            delta = min(W_cubic - self.cwnd, 1.0)
            self.cwnd += delta
        # If W_cubic < cwnd, we do not reduce cwnd here; reductions happen on loss.

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def can_send(self) -> bool:
        """Check sending permission using integer cwnd."""
        return len(self.unacked) < int(self.cwnd)

    def oldest_unacked_send_time(self):
        if not self.unacked:
            return None
        times = [pkt.send_time for pkt in self.unacked.values() if pkt.send_time is not None]
        return min(times) if times else None

    # ------------------------------------------------------------------
    # Loss handling: timeout + fast retransmit
    # ------------------------------------------------------------------
    def handle_timeout(self):
        """CUBIC timeout reaction: more severe than dupACK loss."""
        if not self.unacked:
            return

        old_cwnd = self.cwnd
        old_state = self.state

        # CUBIC: multiplicative decrease
        self.W_max = self.cwnd
        self.cwnd = max(self.cwnd * self.beta, 1.0)
        self.ssthresh = self.cwnd
        self.state = "SLOW_START"
        self.dup_ack_count = 0
        self.epoch_start = None    # new cubic epoch after timeout

        self.logger.record_event(self.env.now, "TIMEOUT_CUBIC", {
            "flow": self.flow_id,
            "old_cwnd": old_cwnd,
            "old_state": old_state,
            "W_max": self.W_max,
            "new_cwnd": self.cwnd,
            "new_state": self.state
        })
        self.logger.record_cwnd(self.env.now, self.flow_id, self.cwnd)

        # Retransmit earliest unacked
        first_seq = min(self.unacked.keys())
        pkt = self.unacked[first_seq]
        pkt.send_time = self.env.now
        self.logger.record_event(self.env.now, "RETRANSMIT_TIMEOUT", {
            "flow": self.flow_id, "seq": first_seq
        })
        self.env.process(self.link.enqueue(pkt))

    def handle_fast_retransmit(self, dup_ack_seq: int):
        """
        Fast retransmit / fast recovery for CUBIC.
        dup_ack_seq is last ACKed seq; missing packet is smallest seq > dup_ack_seq.
        """
        old_cwnd = self.cwnd

        # CUBIC loss reaction (multiplicative decrease)
        self.W_max = self.cwnd
        self.cwnd = max(self.cwnd * self.beta, 1.0)
        self.ssthresh = self.cwnd
        self.state = "FAST_RECOVERY"
        self.dup_ack_count = 0
        self.epoch_start = None     # new epoch after loss

        self.logger.record_event(self.env.now, "FAST_RECOVERY_ENTER_CUBIC", {
            "flow": self.flow_id,
            "W_max": self.W_max,
            "old_cwnd": old_cwnd,
            "new_cwnd": self.cwnd,
            "ssthresh": self.ssthresh
        })
        self.logger.record_cwnd(self.env.now, self.flow_id, self.cwnd)

        # Find missing seq: smallest unacked > dup_ack_seq
        missing_seq = None
        for seq in sorted(self.unacked.keys()):
            if seq > dup_ack_seq:
                missing_seq = seq
                break

        if missing_seq is None:
            self.logger.record_event(self.env.now, "FAST_RETX_NO_CANDIDATE", {
                "flow": self.flow_id,
                "dup_ack_seq": dup_ack_seq
            })
            return

        pkt = self.unacked[missing_seq]
        pkt.send_time = self.env.now
        self.logger.record_event(self.env.now, "FAST_RETRANSMIT_CUBIC", {
            "flow": self.flow_id, "seq": missing_seq
        })
        self.env.process(self.link.enqueue(pkt))
