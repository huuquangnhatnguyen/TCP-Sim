import simpy
import os
import sys
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.link import Link
from core.logger import LoggerFactory

logger = LoggerFactory()
# Dummy classes for testing
class DummyFlow:
    def __init__(self, env):
        self.env = env
        self.received = []  # list of (packet, arrival_time)
    def on_packet_arrival(self, pkt):
        self.received.append((pkt, self.env.now))
# Dummy packet class
class DummyPacket:
    def __init__(self, size_bytes, flow):
        self.size_bytes = size_bytes
        self.flow = flow
# Dummy loss module that drops packets larger than a threshold
class DummyLossModule:
    def __init__(self):
        self.loss_type = "DUMMY"
    def should_drop(self, packet):
        return packet.size_bytes > 1500

def test_link_enqueue_dequeue():
    env = simpy.Environment()
    link = Link(env, bandwidth_mbps=10, prop_delay=0.1, queue_size=2, logger=logger)
    # Create dummy packets
    flow = DummyFlow(env=env)
    pkt1 = DummyPacket(size_bytes=1000, flow=flow)
    pkt2 = DummyPacket(size_bytes=2000, flow=flow)
    pkt3 = DummyPacket(size_bytes=1500, flow=flow)
    # Trying enqueueing packets
    result1 = env.process(link.enqueue(pkt1))
    result2 = env.process(link.enqueue(pkt2))
    result3 = env.process(link.enqueue(pkt3))
    env.run(until=1)
    # Two packets successfully enqueued since queue size is 2
    assert result1.value is True
    assert result2.value is True
    # Third packet should be dropped due to full queue
    assert result3.value is False

def test_link_with_loss_module():
    env = simpy.Environment()
    # Initialize link with a dummy loss module
    loss_module = DummyLossModule()
    link = Link(env, bandwidth_mbps=10, prop_delay=0.1, queue_size=5, loss_module=loss_module, logger=logger)
    flow = DummyFlow(env=env)
    pkt1 = DummyPacket(size_bytes=1000, flow=flow)  # Should not be dropped
    pkt2 = DummyPacket(size_bytes=2000, flow=flow)  # Should be dropped
    # Enqueue packets
    result1 = env.process(link.enqueue(pkt1))
    result2 = env.process(link.enqueue(pkt2))
    env.run(until=1)
    assert result1.value is True
    assert result2.value is False

def test_link_transmission_time():
    env = simpy.Environment()
    link = Link(env, bandwidth_mbps=10, prop_delay=0.1, queue_size=5, logger=logger)
    flow = DummyFlow(env=env)
    pkt = DummyPacket(size_bytes=1000, flow=flow)  # 1000 bytes
    start_time = env.now
    result = env.process(link.enqueue(pkt))
    # Calculate expected transmission time
    expected_tx_time = (1000 * 8) / (10 * 1e6) + 0.1  # in seconds
    # Run the environment for enough time to process the packet
    env.run(until=start_time + expected_tx_time + 0.1)
    # Check that the packet has been processed (i.e., time has advanced correctly)
    assert len(flow.received) == 1
    received_pkt, arrival_time = flow.received[0]
    assert received_pkt is pkt
    assert arrival_time == pytest.approx(start_time + expected_tx_time, rel=1e-6)