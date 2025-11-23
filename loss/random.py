import random

def maybe_drop_random(self, pkt, p):
    if random.random() < p:
        return True
    return False
