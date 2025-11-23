import simpy
class Link:
    def __init__(self, env, bandwidth_mbps, prop_delay, queue_size):
        self.env = env
        self.queue = simpy.Store(env, capacity=queue_size)
        self.bandwidth = bandwidth_mbps
        self.prop_delay = prop_delay
        self.env.process(self.run())

    def run(self):
        while True:
            pkt = yield self.queue.get()
            tx_time = (pkt.size * 8) / (self.bandwidth * 1e6)
            yield self.env.timeout(tx_time + self.prop_delay)
            pkt.flow.on_packet_arrival(pkt)
