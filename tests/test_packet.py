# tests/test_packet.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.packet import Packet

class DummyFlow:
    def __init__(self, flow_id):
        self.flow_id = flow_id

def test_packet_init_basic():
    flow = DummyFlow(flow_id="flowA")
    p = Packet(seq=10, size_bytes=1000, flow=flow)

    assert p.seq == 10
    assert p.size_bytes == 1000
    assert p.flow_id == "flowA"

    # Defaults
    assert p.send_time is None
    assert p.is_ack is False
    assert p.ack_for is None


def test_packet_repr_data_packet():
    p = Packet(seq=1, size_bytes=1500, flow=DummyFlow(flow_id=1))
    r = repr(p)

    assert "Packet(" in r
    assert "seq=1" in r
    assert "size=1500" in r
    assert "flow=1" in r
    # No ACK info for non-ACK packets
    assert "ACK for" not in r


def test_packet_ack_fields_and_repr():
    ack = Packet(seq=5, size_bytes=64, flow=DummyFlow(flow_id=2), is_ack=True, ack_for=4)

    assert ack.is_ack is True
    assert ack.ack_for == 4

    r = repr(ack)
    assert "ACK for 4" in r
