
from simple_single_flow import simple_single_flow_experiment
import random

rtt_list = [100, 150, 200]
bandwidth_list = [10, 50, 100]
packet_loss_list = [0.0, 0.01, 0.05]
p_good_list = [0.001, 0.01]
p_bad_list = [0.1, 0.3]
queue_size_list = [1, 50, 100]
sim_duration_list = [10, 20, 30]
loss_types = ["none", "random", "bursty"]
prop_delay = 0.05  # Fixed propagation delay for all experiments
sweep_configs = []
for _ in range(10):  # Generate 10 random configurations
    config = {
        "prop_delay": prop_delay,
        "sim_duration": random.choice(rtt_list),
        "bandwidth_mbps": random.choice(bandwidth_list),
        "queue_size": random.choice(queue_size_list),
        "sim_duration": random.choice(sim_duration_list),
        "loss_type": random.choice(loss_types),
        "loss_params": {
            "drop_prob": random.choice(packet_loss_list),
            "p_good": random.choice(p_good_list),
            "p_bad": random.choice(p_bad_list),
            "good_duration": 5,
            "bad_duration": 2
        }
    }
    sweep_configs.append(config)
    
if __name__ == "__main__":
    for i, config in enumerate(sweep_configs):
        print(f"Running experiment {i+1} with config: {config}")
        simple_single_flow_experiment(config)
