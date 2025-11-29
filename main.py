import simpy
from core.link import Link
from tcp.reno import RenoFlow

env = simpy.Environment()

link = Link(env, bandwidth_mbps=10, prop_delay=10/1000, queue_size=50)
flow = RenoFlow(env, link)

env.run(until=10)  # seconds
