# import simpy
# from core.env import SimulationEnvironment
# from core.link import Link
# from tcp.reno import RenoFlow

# env = simpy.Environment()

# link = Link(env, bandwidth_mbps=10, prop_delay=10/1000, queue_size=50)
# flow = RenoFlow(env, link)

# env.run(until=10)  # seconds


# def dummy_process(env):
#     """
#     Simple SimPy process to verify that the environment and
#     process scheduling work as expected.
#     """
#     print(f"[{env.now:.6f}] dummy_process: starting")
#     for i in range(5):
#         # Wait 1 simulated second
#         yield env.timeout(1.0)
#         print(f"[{env.now:.6f}] dummy_process: tick {i+1}")


# def main():
#     # Create our wrapped simulation environment
#     sim = SimulationEnvironment(seed=42)
#     env = sim.env  # underlying SimPy environment

#     # Start the dummy process
#     env.process(dummy_process(env))

#     # Create a bottleneck link
#     # Note: we are not attaching a loss module yet
#     link = Link(
#         env=env,
#         bandwidth_mbps=10,
#         prop_delay=10 / 1000,   # 10 ms one-way
#         queue_size=50,
#         loss_module=None
#     )

#     # Create a Reno flow over this link
#     flow = RenoFlow(env, link)

#     # 4) Run the simulation for 10 seconds of simulated time.
#     #    For now, we don't write logs to CSV; set write_logs=True later.
#     sim.run(until=10, write_logs=False)

#     print("Simulation finished.")


# if __name__ == "__main__":
#     main()

# main.py

from core.env import SimulationEnvironment
from core.link import Link
from tcp.reno import RenoFlow


def dummy_process(env):
    """
    Simple SimPy process to verify that the environment and
    process scheduling work as expected.
    """
    print(f"[{env.now:.6f}] dummy_process: starting")
    for i in range(5):
        yield env.timeout(1.0)
        print(f"[{env.now:.6f}] dummy_process: tick {i+1}")


def main():
    # Create our wrapped simulation environment
    sim = SimulationEnvironment(seed=42)
    env = sim.env  # underlying SimPy environment

    # Sanity-check process
    env.process(dummy_process(env))

    # Create a bottleneck link (no loss module yet)
    link = Link(
        env=env,
        bandwidth_mbps=10,
        prop_delay=10 / 1000,  # 10 ms one-way
        queue_size=50,
        loss_module=None,
    )

    # Create a single Reno flow over this link
    flow = RenoFlow(env, link, flow_id=0)

    # Run for 10 seconds of simulated time
    sim.run(until=10.0)

    print("Simulation finished.")


if __name__ == "__main__":
    main()
