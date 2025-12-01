# core/env.py

import simpy
import random


class SimulationEnvironment:
    """
    Simple wrapper around simpy.Environment.
    This will be the main handle used by main.py and experiments.
    """

    def __init__(self, seed: int | None = None):
        self.env = simpy.Environment()

        # Optional RNG seeding for reproducibility
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def run(self, until: float):
        """Run the simulation until the given time (seconds)."""
        self.env.run(until=until)
