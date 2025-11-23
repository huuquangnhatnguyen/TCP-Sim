import simpy
from core.link import Link
from core.packet import Packet

class RenoFlow:
    def __init__(self, env, link):
        self.env = env
        self.link = link
        self.cwnd = 1
        self.ssthresh = 64 # initial ssthresh
        self.unacked = {}
        self.seq = 0

        self.env.process(self.sender())
        self.env.process(self.timer())

    def sender(self):
        while True:
            if self.can_send():
                pkt = Packet(self.seq, size=1500, flow=self)
                self.seq += 1
                self.unacked[pkt.seq] = pkt
                pkt.send_time = self.env.now
                self.link.enqueue(pkt)
            yield self.env.timeout(0.001)  # pacing

    def on_ack(self, ack_seq):
        # Reno cwnd increase logic
        # Update RTT estimate
        # Remove from unacked
        pass

    def timer(self):
        while True:
            yield self.env.timeout(self.rto)
            if self.has_outstanding():
                self.handle_timeout()
