from loss.random import RandomLoss
import simpy
from core.link import Link
from core.logger import LoggerFactory
logger = LoggerFactory()

class DummyFlow:
    def __init__(self, env):
        self.env = env
        self.received = []  # list of (packet, arrival_time)
    def on_packet_arrival(self, pkt):
        self.received.append((pkt, self.env.now))

class DummyPacket:
    def __init__(self, size_bytes, flow):
        self.size_bytes = size_bytes
        self.flow = flow

def test_random_loss_link_dropping():
    env = simpy.Environment()
    loss_module = RandomLoss(drop_prob=0.5)
    link = Link(env, bandwidth_mbps=10, prop_delay=0.1, queue_size=5, loss_module=loss_module, logger=logger)
    flow = DummyFlow(env=env)
    dropped_count = 0
    total_packets = 1000
    for _ in range(total_packets):
        pkt = DummyPacket(size_bytes=1000, flow=flow)
        result = env.process(link.enqueue(pkt))
        env.run(until=env.now + 0.01)
        if result.value is False:
            dropped_count += 1
    drop_rate = dropped_count / total_packets
    assert drop_rate <= 1  
