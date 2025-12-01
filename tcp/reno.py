import simpy
from core.link import Link
from core.packet import Packet
from core.logger import LoggerFactory

class RenoFlow:
    def __init__(self, env: simpy.Environment, link: Link, flow_id: int = 0, logger: LoggerFactory = None):
        self.env = env
        self.link = link

        # Basic Reno state
        self.cwnd = 1               # in packets (start with 1 MSS)
        self.ssthresh = 64          # initial ssthresh (packets)
        self.unacked = {}           # seq -> Packet
        self.seq = 0                # next sequence number

        # For timeouts
        self.rto = 1.0              # retransmission timeout (seconds) - placeholder
        self.flow_id = flow_id      # for logging / debugging

        # Start sender and timer processes
        self.env.process(self.sender())
        self.env.process(self.timer())

        # Logger
        self.logger = logger if logger is not None else LoggerFactory()

    # ------------------------------------------------------------------
    # Core processes
    # ------------------------------------------------------------------
    def sender(self):
        """
        Continuously try to send new packets as long as the congestion window
        allows it. This is a SimPy process.
        """
        while True:
            if self.can_send():
                pkt = Packet(
                    seq=self.seq,
                    size_bytes=1500,   # bytes
                    flow=self
                )
                self.seq += 1
                self.unacked[pkt.seq] = pkt
                pkt.send_time = self.env.now
                self.logger.record_event(self.env.now, "PACKET_SEND", pkt)
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
        self.on_ack(pkt.seq)

    def on_ack(self, ack_seq: int):
        """
        Basic ACK handling with a very simplified cwnd update.
        You will later expand this into full Reno:
          - slow start
          - congestion avoidance (AIMD)
          - duplicate ACKs / fast retransmit / fast recovery
        """
        if ack_seq in self.unacked:
            del self.unacked[ack_seq]

        # Extremely simplified cwnd growth: always in "slow start"
        # until ssthresh; you will refine this later.
        if self.cwnd < self.ssthresh:
            self.cwnd += 1
        else:
            # placeholder for congestion avoidance (e.g., cwnd += 1/cwnd)
            self.cwnd += 1  # just to see growth in tests; not real Reno
        self.logger.record_event(self.env.now, "CWND_UPDATE", self.cwnd)
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
        self.ssthresh = max(self.cwnd // 2, 2)
        self.cwnd = 1
        self.unacked.clear()

        self.logger.record_event(self.env.now, "TIMEOUT", {
            "new_ssthresh": self.ssthresh,
            "new_cwnd": self.cwnd
        })