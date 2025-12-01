class Packet:
    def __init__(self, seq, size_bytes, flow, *, is_ack=False, ack_for=None):
        # basic payload attributes
        self.seq = seq
        self.size_bytes = size_bytes

        # flow identification for logging
        self.flow_id = getattr(flow, 'flow_id', None)

        # reference to the flow that created this packet
        self.flow = flow 
        # additional attributes for sending and acknowledgment
        self.send_time = None  
        self.ack_for = ack_for
        self.is_ack = is_ack
    
    def __repr__(self):
        base = f"Packet(seq={self.seq}, size={self.size_bytes}, flow={self.flow_id}"
        if self.is_ack:
            base += f", ACK for {self.ack_for}"
        return base + ")"