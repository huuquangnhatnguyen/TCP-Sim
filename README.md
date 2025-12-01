**TCP-Sim**

**Project Overview:**: A lightweight, educational TCP simulator implemented in Python using `simpy`. TCP-Sim provides components to model links, queues, packet events, loss models, and TCP sender implementations (e.g., Reno and Cubic). It's intended for experiments, teaching, and rapid prototyping of TCP behaviors under different network conditions.

**Features:**
- **Modular core**: `core/` provides simulation primitives such as `Link`, queues, packets, and an event queue.
- **TCP variants**: `tcp/` contains protocol implementations like `reno.py` and `cubic.py`.
- **Loss models**: `loss/` contains pluggable loss models (random, bursty, congestion-driven) for testing.
- **Experiments**: `experiments/` contains example drivers and sweep scaffolding.
- **Plots & Results**: `plots/` and `results/` hold plotting utilities and output data.

**Requirements:**
- Python 3.8+ (recommended)
- See `requirements.txt` for pinned packages. Install with:

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt
```

**Quick Start / Minimal Example:**
- Run the simple example in `experiments/run_all.py` which starts a `simpy` environment with a `Link` and a `RenoFlow`:

```bash
python experiments/run_all.py
```

This script sets up a 10 Mbps link with 10 ms propagation delay and runs a single Reno flow for 10 seconds. Modify the file to add flows or change parameters.

**Project Layout:**
- `core/`:
  - `link.py`: link model (bandwidth, propagation delay, queuing)
  - `queue.py`: queueing logic and buffer management
  - `packet.py`: packet representation
  - `event_queue.py`: simulation event helpers
  - `logger.py`: lightweight logging utilities for experiments
- `tcp/`:
  - `reno.py`: Reno TCP sender implementation
  - `cubic.py`: Cubic TCP sender implementation
- `loss/`:
  - `random.py`: random packet loss model
  - `bursty.py`: bursty loss model
  - `congestion.py`: congestion-triggered loss model
- `experiments/`:
  - `run_all.py`: simple example runner
  - `config_sweep.py`: (placeholder) intended for parameter sweep scaffolding
- `plots/`: plotting scripts (generate figures from `results/`)
- `results/`: output CSV/JSON/logs produced by experiments

# TCP-Sim

**Project Overview:** A lightweight, educational TCP simulator implemented in Python using `simpy`. TCP-Sim provides components to model links, queues, packet events, loss models, and TCP sender implementations (e.g., Reno and Cubic). It's intended for experiments, teaching, and rapid prototyping of TCP behaviors under different network conditions.

## Features
- **Modular core**: `core/` provides simulation primitives such as `Link`, queues, packets, and an event queue.
- **TCP variants**: `tcp/` contains protocol implementations like `reno.py` and `cubic.py`.
- **Loss models**: `loss/` contains pluggable loss models (random, bursty, congestion-driven) for testing.
- **Experiments**: `experiments/` contains example drivers and sweep scaffolding.
- **Plots & Results**: `plots/` and `results/` hold plotting utilities and output data.

## Requirements
- Python 3.8+ (recommended)
- See `requirements.txt` for pinned packages. Install with:

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt
```

If you plan to run tests, install `pytest` (recommended as a development dependency):

```bash
pip install pytest
```

## Quick Start / Minimal Example
- Run the simple example in `experiments/run_all.py` which starts a `simpy` environment with a `Link` and a `RenoFlow`:

```bash
python experiments/run_all.py
```

This script sets up a 10 Mbps link with 10 ms propagation delay and runs a single Reno flow for 10 seconds. Modify the file to add flows or change parameters.

## Project Layout
- `core/`:
  - `link.py`: link model (bandwidth, propagation delay, queuing)
  - `queue.py`: queueing logic and buffer management
  - `packet.py`: packet representation
  - `event_queue.py`: simulation event helpers
  - `logger.py`: lightweight logging utilities for experiments
- `tcp/`:
  - `reno.py`: Reno TCP sender implementation
  - `cubic.py`: Cubic TCP sender implementation
- `loss/`:
  - `random.py`: random packet loss model
  - `bursty.py`: bursty loss model
  - `congestion.py`: congestion-triggered loss model
- `experiments/`:
  - `run_all.py`: simple example runner
  - `config_sweep.py`: (placeholder) intended for parameter sweep scaffolding
- `plots/`: plotting scripts (generate figures from `results/`)
- `results/`: output CSV/JSON/logs produced by experiments

## How to Run Experiments
- Edit or create a script under `experiments/` to instantiate `simpy.Environment()`, create `Link` and flow objects from `tcp/`, and call `env.run(until=...)`.
- Example (taken from `experiments/run_all.py`):

```python
import simpy
from core.link import Link
from tcp.reno import RenoFlow

env = simpy.Environment()
link = Link(env, bandwidth_mbps=10, prop_delay=10/1000, queue_size=50)
flow = RenoFlow(env, link)
env.run(until=10)
```

## Design Notes & Extensibility
- To add a new TCP variant: create a new module in `tcp/` implementing the sender logic and the same constructor/signature pattern used by `RenoFlow`/`CubicFlow`.
- To add a loss model: implement a model in `loss/` that can be queried by `Link` or the queue to drop packets according to policy.
- To perform parameter sweeps: implement loops or use `argparse` in `experiments/config_sweep.py` to vary link bandwidth, delay, queue size, number of flows, and loss parameters; collect results into `results/` and use `plots/` to visualize.

## Logging & Output
- Use `core/logger.py` utilities to record per-event logs, or write CSV/JSON from experiments directly into `results/` for plotting.

## Running Tests (pytest)

This project does not yet include an automated test suite by default. To add and run tests locally:

- Install `pytest` (see above).
- Create a `tests/` directory at the project root and add test modules named `test_*.py`.
- Example layout:

```
TCP-Sim/
├── core/
├── tcp/
├── loss/
├── experiments/
├── tests/
│   └── test_link.py
└── README.md
```

- Run the full test suite:

```bash
pytest -q
```

- Run tests in the `tests/` directory only:

```bash
pytest tests/
```

- Run a specific test file or test case:

```bash
pytest tests/test_link.py::test_enqueue
```

Writing tests: prefer small, deterministic unit tests for `core/` utilities (e.g., queue behavior, packet serialization) and integration tests that run short `simpy` scenarios.

## Contributing
- Fork the repository, create a feature branch, and submit a pull request with a clear description and tests/examples.
- Please follow existing code style and keep changes focused.


