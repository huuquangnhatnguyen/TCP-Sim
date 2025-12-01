import simpy
class Link:
    def __init__(self, 
                 env: simpy.Environment, 
                 bandwidth_mbps: float, 
                 prop_delay: float, 
                 queue_size: int,
                 loss_module=None):
        
        self.env = env
        self.bandwidth = bandwidth_mbps
        self.prop_delay = prop_delay
        self.loss_module = loss_module
        # Initialize the queue with a specified capacity
        self.queue = simpy.Store(env, capacity=queue_size)
        # Start the link process
        self.env.process(self.run())

    def enqueue(self, packet):
        """Attempt to enqueue a packet onto the link. Returns True if successful, False if dropped."""
        if self.loss_module and self.loss_module.should_drop(packet):
            return False  # Packet is dropped due to loss module

        if len(self.queue.items) < self.queue.capacity:
            yield self.queue.put(packet)
            return True  # Packet successfully enqueued
        else:
            return False  # Packet is dropped due to full queue

    def run(self):
        while True:
            # Get the next packet from the queue
            pkt = yield self.queue.get()
            # Calculate transmission time based on bandwidth
            tx_time = (pkt.size_bytes * 8) / (self.bandwidth * 1e6)
            yield self.env.timeout(tx_time + self.prop_delay)
            # Deliver the packet to its destination
            pkt.flow.on_packet_arrival(pkt)
