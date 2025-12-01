import random

def maybe_drop_random(self, pkt, p):
    if random.random() < p:
        return True
    return False

class RandomLoss:
    def __init__(self, drop_prob: float):
        self.drop_prob = drop_prob
        self.loss_type = "RANDOM"

    def should_drop(self, packet):
        return maybe_drop_random(self, packet, self.drop_prob)