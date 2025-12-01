import random

class BurstyLoss:
    def __init__(self, p_good: float, p_bad: float, avg_good_duration: int, avg_bad_duration: int):
        self.state = 'GOOD'  # Initial state
        self.p_good = p_good
        self.p_bad = p_bad
        self.avg_good_duration = avg_good_duration
        self.avg_bad_duration = avg_bad_duration
        self.loss_type = "BURSTY_LOSS"
        
    def update_state(self):
        
        if self.state == 'GOOD':
            if random.random() < 1 / self.avg_good_duration:
                self.state = 'BAD'
        else:
            if random.random() < 1 / self.avg_bad_duration:
                self.state = 'GOOD'

    def should_drop(self, packet):
        self.update_state()
        if self.state == 'GOOD':
            return random.random() < self.p_good
        else:
            return random.random() < self.p_bad