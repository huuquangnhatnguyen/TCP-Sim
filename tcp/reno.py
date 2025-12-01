import simpy
from core.link import Link
from core.packet import Packet
from core.logger import LoggerFactory

class RenoFlow:
    def __init__(self, env: simpy.Environment, link: Link, flow_id: int = 0, logger: LoggerFactory = None, num_packets: int = 10):
        # Logger
        self.logger = logger if logger is not None else LoggerFactory()
        self.env = env
        self.link = link
        self.state = "SLOW_START"   # Current state of the Reno algorithm
        self.num_packets = num_packets

        # Basic Reno state
        self.cwnd = 1               # in packets (start with 1 MSS)
        self.ssthresh = 64          # initial ssthresh (packets)
        self.unacked = {}           # seq -> Packet
        self.seq = 0                # next sequence number

        # ACKs
        self.last_ack = -1          
        self.dup_ack_count = 0      # count of duplicate ACKs
        self._ca_ack_count = 0      # ACKs received during congestion avoidance
        self.next_seq = 0           # next seq number to send
        self.valid_ack_count = 0    # total "correct" ACKs received

        # For timeouts
        self.rto = 1.0              # retransmission timeout (seconds) - placeholder
        self.flow_id = flow_id      # for logging / debugging

        # Start sender and timer processes
        self.env.process(self.sender())
        self.env.process(self.timer())

        

    # ------------------------------------------------------------------
    # Core processes
    # ------------------------------------------------------------------
    def sender(self):
        """
        Continuously try to send new packets as long as the congestion window
        allows it. This is a SimPy process.
        """
        while True:
            if self.can_send() and self.seq < self.num_packets:
                pkt = Packet(
                    seq=self.seq,
                    size_bytes=1500,   # bytes
                    flow=self
                )
                self.seq += 1
                self.unacked[pkt.seq] = pkt
                pkt.send_time = self.env.now
                self.logger.record_packet_sent(self.env.now, self.flow_id, pkt.seq)
                self.logger.record_queue(self.env.now, self.flow_id, len(self.link.queue.items))
                # IMPORTANT: enqueue is a SimPy generator; we must yield it
                result_event = yield self.env.process(self.link.enqueue(pkt))
                # If you care about drop info:
                # success = result_event  # because we "return" True/False in enqueue
                # For now, we ignore that and rely on events/logging later.

            # Pacing: small delay before the next send attempt
            yield self.env.timeout(0.001)

    def timer(self):
        """
        Very simple retransmission timer loop.
        For now, it just periodically checks if there are outstanding packets
        and calls handle_timeout(). This is a placeholder.
        """
        while True:
            yield self.env.timeout(self.rto)
            if self.has_outstanding():
                self.handle_timeout()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def on_packet_arrival(self, pkt: Packet):
        """
        Called by Link.run when a data packet arrives at the destination.
        For now, we immediately treat this as the ACK for that packet.
        Later you can explicitly model ACK packets if desired.
        """
        if pkt.seq == self.next_seq:
            self.next_seq += 1
            self.on_ack(pkt.seq)
            self.valid_ack_count += 1
        else:
            # Out-of-order packet, send duplicate ACK for last in-order packet
            self.on_ack(self.next_seq - 1)
            
        self.logger.record_ack(self.env.now, self.flow_id, self.next_seq - 1)
    def on_ack(self, ack_seq: int):
        """
        Basic ACK handling with a very simplified cwnd update.
        You will later expand this into full Reno:
          - slow start
          - congestion avoidance (AIMD)
          - duplicate ACKs / fast retransmit / fast recovery
        """
        if ack_seq < self.last_ack:
            return # Old ACK, ignore
        # =======
        # NEW ACK 
        # =======
        if ack_seq > self.last_ack:
            for seq in list(self.unacked.keys()):
                if seq <= ack_seq:
                    pkt = self.unacked.pop(seq)
                    # Optional: RTT sample logging
                    # if self.logger and pkt.send_time is not None:
                    #     rtt_sample = self.env.now - pkt.send_time
                    #     self.logger.record_event(
                    #         time=self.env.now,
                    #         event_type="rtt_sample",
                    #         details={"flow": self.flow_id, "seq": seq, "rtt": rtt_sample}
                    #     )

            # reset dupACK counter
            self.dup_ack_count = 0

            # Congestion control logic
            if self.state == "SLOW_START":
                self.cwnd += 1
                # exit slow start into CA
                if self.cwnd >= self.ssthresh:
                    self.state = "CONGESTION_AVOID"
            elif self.state == "CONGESTION_AVOID":
                self._ca_ack_count += 1
                if self._ca_ack_count >= self.cwnd:
                    self.cwnd += 1
                    self._ca_ack_count = 0
            elif self.state == "FAST_RECOVERY":
                self.cwnd = self.ssthresh
                self.state = "CONGESTION_AVOID"
            
            self.last_ack = ack_seq
            self.logger.record_event(self.env.now, "CWND_UPDATE", self.cwnd)
            self.logger.record_cwnd(self.env.now, self.flow_id, self.cwnd)
            return

        # ==============
        # DUPLICATE ACK
        # ==============

        if ack_seq == self.last_ack:
            self.dup_ack_count += 1

            # Triple DUP ACKs: Fast Retransmit
            if self.dup_ack_count == 3 and self.state != "FAST_RECOVERY":
                self.handle_retransmit(ack_seq)
            elif self.state == "FAST_RECOVERY":
                self.cwnd += 1  # inflate cwnd
                self.logger.record_event(self.env.now, "CWND_UPDATE", self.cwnd)
                self.logger.record_cwnd(self.env.now, self.flow_id, self.cwnd)


    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def can_send(self) -> bool:
        """
        Return True if we are allowed to send another packet,
        based on cwnd and number of unacked packets.
        """
        return len(self.unacked) < self.cwnd

    def has_outstanding(self) -> bool:
        """Return True if there are unacknowledged packets."""
        return bool(self.unacked)

    def handle_timeout(self):
        """
        Very simple timeout handler: reset cwnd to 1 and cut ssthresh.
        You will later refine this with full Reno behavior.
        """
        # Classic Reno-style reaction (simplified)
        self.ssthresh = max(self.cwnd // 2, 1)
        self.cwnd = 1
        self.state = "SLOW_START"
        self.logger.record_event(self.env.now, "TIMEOUT", {
            "new_ssthresh": self.ssthresh,
            "new_cwnd": self.cwnd
        })
        if self.unacked:
            # Retransmit the earliest unacked packet
            first_seq = min(self.unacked.keys())
            pkt = self.unacked[first_seq]
            pkt.send_time = self.env.now
            self.logger.record_event(self.env.now, "RETRANSMIT", pkt)
            self.env.process(self.link.enqueue(pkt))
            


    def handle_retransmit(self, dup_ack_seq: int):
        """
        Handle fast retransmit and enter fast recovery.
        """
        # Set ssthresh
        self.ssthresh = max(self.cwnd // 2, 1)
        # Enter fast recovery
        self.cwnd = self.ssthresh + 3  # inflate cwnd
        self.state = "FAST_RECOVERY"
        self.logger.record_event(self.env.now, "FAST_RECOVERY_ENTER", {
            "new_ssthresh": self.ssthresh,
            "new_cwnd": self.cwnd
        })
        # Retransmit the missing packet
        if dup_ack_seq in self.unacked:
            pkt = self.unacked[dup_ack_seq]
            pkt.send_time = self.env.now
            self.logger.record_event(self.env.now, "FAST_RETRANSMIT", pkt)
            self.env.process(self.link.enqueue(pkt))