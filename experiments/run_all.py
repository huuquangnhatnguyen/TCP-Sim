# import simpy
# from core.link import Link
# from tcp.reno import RenoFlow
# import random

# env = simpy.Environment()
# rtt_list = [100, 150, 200]
# bandwidth_list = [10, 50, 100]
# packet_loss_list = [0.0, 0.01, 0.05]
# buffer_size_list = [10, 50, 100]
# sim_duration_list = [10, 20, 30]
# sweep_configs = []
# for _ in range(5):  # Generate 5 random configurations
#     config = {
#         "rtt_ms": random.choice(rtt_list),
#         "bandwidth_mbps": random.choice(bandwidth_list),
#         "drop_prob": random.choice(packet_loss_list),
#         "queue_size": random.choice(buffer_size_list),
#         "sim_duration": random.choice(sim_duration_list),
#     }
#     sweep_configs.append(config)
    
# def get_sweep_configs():
#     return sweep_configs    