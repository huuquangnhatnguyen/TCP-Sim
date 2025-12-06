
from simple_single_flow_cubic import simple_single_flow_experiment_Cubic
import random
bandwidth = 10 # Mbps
rtt = 40 # ms
bdp = bandwidth * rtt / 8  # in KB
queue_size = 1 * bdp
num_packets = 10000
sweep_configs = [
    {
        "bandwidth_mbps" : bandwidth,      # Link bandwidth in Mbps
        "prop_delay" : rtt / 2000,
        "queue_size" : int(queue_size),        # Queue size in packets
        "loss_type" : "none",     # Type of loss module: "none", "random", "bursty"
        "loss_params" : {},
        "num_packets" : num_packets,        # Number of packets to send
        "folder": f"logs/exp1_no_loss"
    },
    {
        "bandwidth_mbps" : bandwidth,      # Link bandwidth in Mbps
        "prop_delay" : rtt / 2000,
        "queue_size" : int(queue_size),        # Queue size in packets
        "loss_type" : "random",     # Type of loss module: "none", "random", "bursty"
        "loss_params" : {
            "drop_prob": 0.001    # For random loss with low probability
        },
        "num_packets" : num_packets,        # Number of packets to send
        "folder": f"logs/exp2_random_low_loss"
    },
    {
        "bandwidth_mbps" : bandwidth,      # Link bandwidth in Mbps
        "prop_delay" : rtt / 2000,
        "queue_size" : int(queue_size),        # Queue size in packets
        "loss_type" : "random",     # Type of loss module: "none", "random", "bursty"
        "loss_params" : {
            "drop_prob": 0.1    # For random loss with higher probability
        },
        "num_packets" : num_packets,        # Number of packets to send
        "folder": f"logs/exp3_random_high_loss"
    },
    {
        "bandwidth_mbps" : 20,      # Link bandwidth in Mbps
        "prop_delay" : rtt / 2000,
        "queue_size" : int(20 * rtt / 8),        # Queue size in packets
        "loss_type" : "bursty",     # Type of loss module: "none", "random", "bursty"
        "loss_params" : {
            "p_good": 0.009,
            "p_bad": 0.1,
            "good_duration": 200,
            "bad_duration": 20
        },
        "num_packets" : num_packets,        # Number of packets to send
        "folder": f"logs/exp4_bursty_small_queue"
    },
    {
        "bandwidth_mbps" : 20,      # Link bandwidth in Mbps
        "prop_delay" : rtt / 2000,
        "queue_size" : int(20 * rtt / 8) * 2,        # Queue size in packets
        "loss_type" : "bursty",     # Type of loss module: "none", "random", "bursty"
        "loss_params" : {
            "p_good": 0.009,
            "p_bad": 0.1,
            "good_duration": 200,
            "bad_duration": 20
        },
        "num_packets" : num_packets,        # Number of packets to send
        "folder": f"logs/exp5_bursty_big_queue"
    }
]
if __name__ == "__main__":
    for i, config in enumerate(sweep_configs):
        print(f"Running experiment {i+1} with config: {config}")
        simple_single_flow_experiment_Cubic(config)
