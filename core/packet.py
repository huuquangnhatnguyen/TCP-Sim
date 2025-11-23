class Packet:
    def __init__(self, seq, size, flow):
        self.seq = seq
        self.size = size
        self.flow = flow
        self.send_time = None
