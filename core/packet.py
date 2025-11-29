class Packet:
    def __init__(self, seq, size_bytes, flow_id,*, is_ack=False, ack_for=None):
        # basic payload attributes
        self.seq = seq
        self.size_bytes = size_bytes
        self.flow_id = flow_id
        # additional attributes for sending and acknowledgment
        self.send_time = None  
        self.ack_for = ack_for
        self.is_ack = is_ack
    
    def __repr__(self):
        base = f"Packet(seq={self.seq}, size={self.size_bytes}, flow={self.flow_id}"
        if self.is_ack:
            base += f", ACK for {self.ack_for}"
        return base + ")"