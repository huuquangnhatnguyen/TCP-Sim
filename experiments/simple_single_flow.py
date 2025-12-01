import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.env import SimulationEnvironment
from core.link import Link
from tcp.reno import RenoFlow as TCPSenderReno
from core.logger import LoggerFactory

from loss.random import RandomLoss
from loss.bursty import BurstyLoss

def build_loss_module(loss_type, params):
    if loss_type == "none":
        return None
    elif loss_type == "random":
        return RandomLoss(drop_prob=params["drop_prob"])
    elif loss_type == "bursty":
        return BurstyLoss(
            p_good=params["p_good"],
            p_bad=params["p_bad"],
            good_duration=params["good_duration"],
            bad_duration=params["bad_duration"]
        )
    else:
        raise ValueError(f"Unknown loss type: {loss_type}")

def simple_single_flow_experiment(config):
    """
    A simple experiment that sets up a single TCP flow over a link with
    specified parameters, runs the simulation, and collects basic statistics.
    """
    
    # Create simulation environment
    sim_env = SimulationEnvironment()
    env = sim_env.env

    # Set up logging
    logger = LoggerFactory()

    # Create a link with specified parameters
    bandwidth_mbps = config["bandwidth_mbps"]      # Link bandwidth in Mbps
    prop_delay = config["prop_delay"]        # Propagation delay in seconds
    queue_size = config["queue_size"]          # Queue size in packets
    loss_module = build_loss_module(config["loss_type"], config["loss_params"])

    link = Link(
        env,
        bandwidth_mbps=bandwidth_mbps,
        prop_delay=prop_delay,
        queue_size=queue_size,
        loss_module=loss_module,
        logger=logger
    )

    # Create a single TCP Reno sender
    flow = TCPSenderReno(
        env,
        link,
        flow_id=1,
        logger=logger
    )

    # Run the simulation for a specified duration
    sim_env.run(until=config["sim_duration"])

    # After simulation, we can analyze logs or print summary statistics
    logger.write_all_logs()

if __name__ == "__main__":
    # Example configuration for the experiment
        
    config = {
        "bandwidth_mbps" : 10,      # Link bandwidth in Mbps
        "prop_delay" : 0.05,        # Propagation delay in seconds
        "queue_size" : 20  ,        # Queue size in packets
        "loss_type" : "random",     # Type of loss module: "none", "random", "bursty"
        "loss_params" : {
            "drop_prob": 0.01     # For random loss
        },
        "sim_duration" : 10        # Simulation duration in seconds
    }

    simple_single_flow_experiment(config)
    print("Done.")