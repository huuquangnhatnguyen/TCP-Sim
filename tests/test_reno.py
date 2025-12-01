from tcp.reno import RenoFlow
import pytest
import simpy
from core.link import Link  # Assuming Link is needed for RenoFlow initialization
from core.logger import LoggerFactory  # Assuming a logger is needed

logger = LoggerFactory()  

def test_reno_flow_initialization():
    env = simpy.Environment()
    link = Link(env, bandwidth_mbps=10, prop_delay=0.1, queue_size=5, logger=logger)  # Dummy link for initialization
    reno_flow = RenoFlow(env, link, flow_id=1)

    assert reno_flow.cwnd == 1
    assert reno_flow.ssthresh == 64
    assert reno_flow.seq == 0
    assert reno_flow.flow_id == 1
    assert reno_flow.unacked == {}
def test_reno_flow_sending_packets():
    env = simpy.Environment()
    link = Link(env, bandwidth_mbps=10, prop_delay=0.1, queue_size=5, logger=logger)
    reno_flow = RenoFlow(env, link, flow_id=1)

    def run_sender():
        yield env.timeout(0.01)  # Allow some time for sending
        assert len(reno_flow.unacked) > 0  # Some packets should be unacked

    env.process(run_sender())
    env.run(until=0.02)
def test_reno_flow_timeout_handling():
    env = simpy.Environment()
    link = Link(env, bandwidth_mbps=10, prop_delay=0.1, queue_size=5, logger=logger)
    reno_flow = RenoFlow(env, link, flow_id=1)

    def run_timer():
        yield env.timeout(reno_flow.rto + 0.1)  # Wait for timeout
        # Here we would check if timeout handling logic is invoked
        # For now, just ensure the timer runs without error

    env.process(run_timer())
    env.run(until=reno_flow.rto + 0.2)
