import simpy
from core.link import Link
from core.packet import Packet
from core.logger import LoggerFactory


class RenoFlow:
    def __init__(
        self,
        env: simpy.Environment,
        link: Link,
        flow_id: int = 0,
        logger: LoggerFactory = None,
        num_packets: int = 10000,
        rto: float = 1.0,
    ):
        # Basic wiring
        self.env = env
        self.link = link
        self.flow_id = flow_id
        self.logger = logger if logger is not None else LoggerFactory()

        # Flow size / termination
        self.num_packets = num_packets
        self.rto = rto

        # Sender state
        self.state = "SLOW_START"      # "SLOW_START" | "CONGESTION_AVOID" | "FAST_RECOVERY"
        self.cwnd = 1                  # congestion window in packets
        self.ssthresh = 64             # initial slow-start threshold in packets
        self.unacked = {}              # seq -> Packet
        self.seq = 0                   # next sequence number to send

        # ACK / receiver state
        self.last_ack = -1             # last cumulatively ACKed seq
        self.dup_ack_count = 0
        self._ca_ack_count = 0         # for cwnd += 1/cwnd in CA (integer approx)

        self.next_seq = 0              # next expected in-order seq at receiver
        self.valid_ack_count = 0       # number of in-order delivered packets
        self.received_seqs = set()     # receiver buffer: seq numbers that have arrived

        # Start processes
        self.env.process(self.sender())
        self.env.process(self.timer())

    # ------------------------------------------------------------------
    # Core processes
    # ------------------------------------------------------------------
    def sender(self):
        """
        Continuously send while cwnd allows and we still have packets to send.
        """
        while True:
            # stop trying to send once we've sent all data
            if self.seq >= self.num_packets and not self.unacked:
                # nothing left in-flight and nothing left to send
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

                # Logging
                self.logger.record_packet_sent(self.env.now, self.flow_id, pkt.seq)
                self.logger.record_queue(self.env.now, self.flow_id, len(self.link.queue.items))

                # enqueue is a SimPy process
                yield self.env.process(self.link.enqueue(pkt))

            # pacing
            yield self.env.timeout(0.001)

    def timer(self):
        """
        Retransmission timer:
        Periodically check the oldest unacked packet; only timeout if its age >= RTO.
        """
        while True:
            yield self.env.timeout(self.rto / 2.0)

            oldest = self.oldest_unacked_send_time()
            if oldest is None:
                # nothing outstanding
                continue

            if self.env.now - oldest >= self.rto:
                self.handle_timeout()

    # ------------------------------------------------------------------
    # Receiver & ACK handling
    # ------------------------------------------------------------------
    def on_packet_arrival(self, pkt: Packet):
        """
        Receiver-side cumulative ACK with simple out-of-order buffering.

        - Every received seq is recorded in self.received_seqs.
        - We then advance next_seq while we have contiguous data.
        - We ACK last in-order seq: ack_seq = next_seq - 1.
        """

        # Record that this seq has arrived
        self.received_seqs.add(pkt.seq)

        # Advance next_seq over contiguous run
        advanced = False
        while self.next_seq in self.received_seqs:
            self.next_seq += 1
            advanced = True

        # Update delivered count if we extended in-order prefix
        if advanced:
            # next_seq is "first missing", so in-order delivered = next_seq
            # (or next_seq packets delivered if 0-based)
            self.valid_ack_count = max(self.valid_ack_count, self.next_seq)

        ack_seq = self.next_seq - 1  # last in-order seq (may be same as before → dupACK)

        # Let Reno process this ACK
        self.on_ack(ack_seq)
        self.logger.record_ack(self.env.now, self.flow_id, ack_seq)

    def on_ack(self, ack_seq: int):
        """
        Reno ACK handler:
          - Distinguish new ACK vs dupACK
          - Implement SS, CA, and FR transitions
          - Maintain cwnd and ssthresh
        """
        # Ignore ACKs that go backwards
        if ack_seq < self.last_ack:
            return

        # -------------------------------------------------
        # NEW ACK (ack_seq > last_ack)
        # -------------------------------------------------
        if ack_seq > self.last_ack:
            # Remove all newly ACKed packets and log RTT samples
            for seq in list(self.unacked.keys()):
                if seq <= ack_seq:
                    pkt = self.unacked.pop(seq)
                    if self.logger and pkt.send_time is not None:
                        rtt_sample = self.env.now - pkt.send_time
                        self.logger.record_event(
                            time=self.env.now,
                            event_type="rtt_sample",
                            details={"flow": self.flow_id, "seq": seq, "rtt": rtt_sample},
                        )

            # reset DUPACK counter
            self.dup_ack_count = 0

            # Congestion control behavior
            if self.state == "SLOW_START":
                self.cwnd += 1
                # exit slow start into congestion avoidance
                if self.cwnd >= self.ssthresh:
                    self.state = "CONGESTION_AVOID"
                    self.logger.record_event(self.env.now, "RENO_STATE_CHANGE", {
                        "flow": self.flow_id,
                        "new_state": self.state
                    })

            elif self.state == "CONGESTION_AVOID":
                # cwnd += 1 per RTT ≈ 1/cwnd per ACK (integer approximation)
                self._ca_ack_count += 1
                if self._ca_ack_count >= self.cwnd:
                    self.cwnd += 1
                    self._ca_ack_count = 0

            elif self.state == "FAST_RECOVERY":
                # An ACK that covers the lost packet: exit FR
                self.cwnd = self.ssthresh
                self.state = "CONGESTION_AVOID"
                self.logger.record_event(self.env.now, "RENO_STATE_CHANGE", {
                    "flow": self.flow_id,
                    "new_state": self.state
                })

            self.last_ack = ack_seq
            self.logger.record_cwnd(self.env.now, self.flow_id, self.cwnd)
            return

        # -------------------------------------------------
        # DUPLICATE ACK (ack_seq == last_ack)
        # -------------------------------------------------
        if ack_seq == self.last_ack:
            self.dup_ack_count += 1

            # Triple dupACK → fast retransmit if not already in FR
            if self.dup_ack_count == 3 and self.state != "FAST_RECOVERY":
                self.handle_retransmit(ack_seq)

            elif self.state == "FAST_RECOVERY":
                # Additional dupACKs in FR inflate cwnd by 1
                self.cwnd += 1
                self.logger.record_cwnd(self.env.now, self.flow_id, self.cwnd)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def can_send(self) -> bool:
        """
        True if we can send another packet based on cwnd and unacked packets.
        """
        return len(self.unacked) < self.cwnd

    def oldest_unacked_send_time(self):
        """
        Return the send time of the oldest unacked packet, or None.
        """
        if not self.unacked:
            return None
        times = [pkt.send_time for pkt in self.unacked.values() if pkt.send_time is not None]
        return min(times) if times else None

    # ------------------------------------------------------------------
    # Loss recovery: timeout and fast retransmit
    # ------------------------------------------------------------------
    def handle_timeout(self):
        """
        Reno-style timeout handler:
          - Only if there are outstanding packets.
          - ssthresh = cwnd/2
          - cwnd = 1
          - state = SLOW_START
          - retransmit earliest unacked packet.
        """
        if not self.unacked:
            return

        old_cwnd = self.cwnd
        old_ssthresh = self.ssthresh
        old_state = self.state

        self.ssthresh = max(self.cwnd // 2, 1)
        self.cwnd = 1
        self.state = "SLOW_START"
        self.dup_ack_count = 0
        self._ca_ack_count = 0

        self.logger.record_event(self.env.now, "TIMEOUT", {
            "flow": self.flow_id,
            "old_cwnd": old_cwnd,
            "old_ssthresh": old_ssthresh,
            "old_state": old_state,
            "new_ssthresh": self.ssthresh,
            "new_cwnd": self.cwnd,
            "new_state": self.state,
        })
        self.logger.record_cwnd(self.env.now, self.flow_id, self.cwnd)

        # Retransmit the earliest unacked packet
        first_seq = min(self.unacked.keys())
        pkt = self.unacked[first_seq]
        pkt.send_time = self.env.now
        self.logger.record_event(self.env.now, "RETRANSMIT_TIMEOUT", {
            "flow": self.flow_id,
            "seq": first_seq
        })
        self.env.process(self.link.enqueue(pkt))

    def handle_retransmit(self, dup_ack_seq: int):
        """
        Reno fast retransmit / fast recovery:
          - dup_ack_seq is the last cumulatively ACKed seq.
          - The missing packet is the smallest seq > dup_ack_seq still in unacked.
        """
        self.ssthresh = max(self.cwnd // 2, 1)
        self.cwnd = self.ssthresh + 3
        self.state = "FAST_RECOVERY"

        self.logger.record_event(self.env.now, "FAST_RECOVERY_ENTER", {
            "flow": self.flow_id,
            "new_ssthresh": self.ssthresh,
            "new_cwnd": self.cwnd
        })
        self.logger.record_cwnd(self.env.now, self.flow_id, self.cwnd)

        # Find the missing packet: smallest unacked seq > dup_ack_seq
        missing_seq = None
        for seq in sorted(self.unacked.keys()):
            if seq > dup_ack_seq:
                missing_seq = seq
                break

        if missing_seq is None:
            # Should rarely happen; indicates inconsistent state
            self.logger.record_event(self.env.now, "FAST_RETRANSMIT_NO_CANDIDATE", {
                "flow": self.flow_id,
                "dup_ack_seq": dup_ack_seq
            })
            return

        pkt = self.unacked[missing_seq]
        pkt.send_time = self.env.now
        self.logger.record_event(self.env.now, "FAST_RETRANSMIT", {
            "flow": self.flow_id,
            "seq": missing_seq
        })
        self.env.process(self.link.enqueue(pkt))
