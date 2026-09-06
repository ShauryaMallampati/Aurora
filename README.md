# AURORA

**Reproducible experiments for multi-agent wildfire-response strategies.**

[![Tests](https://github.com/ShauryaMallampati/Aurora/actions/workflows/tests.yml/badge.svg)](https://github.com/ShauryaMallampati/Aurora/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Quick start](docs/QUICKSTART.md) · [Python API](docs/API.md) · [Research evidence](docs/RESEARCH.md) · [Credits](CREDITS.md)

AURORA is a Python framework for comparing response strategies in an abstract wildfire grid simulator. It provides deterministic runs, replayable traces, and controlled fault injection so you can examine how simulator design affects experimental results.

> AURORA is research and teaching software. It is not calibrated for real fires and must not be used for forecasting, incident command, aviation control, dispatch, or any safety-critical decision.

## What you can do

- **Compare strategies fairly:** run matched scenarios and seeds with event-keyed environmental randomness and synchronous agent actions.
- **Record and replay runs:** inspect versioned traces and verify their digests.
- **Study simulation faults:** measure random-stream drift, retained reset state, timing leaks, and conflated fire-state labels.
- **Bring your own strategy:** use the Python strategy API or the optional PettingZoo parallel environment.
- **Reproduce the evidence:** run the bundled benchmarks, tests, and artifact checks.

## Get started

Requires **Python 3.10–3.13**. From a terminal:

```bash
git clone https://github.com/ShauryaMallampati/Aurora.git
cd Aurora
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

Run a seeded episode, replay it, and validate the installation:

```bash
aurora demo --method coordinated --scenario warm_crosswind --seed 7 --trace trace.json
aurora replay trace.json
aurora validate
```

Replay and validation should report `PASS`. Use `aurora scenarios` to list the bundled scenarios or `aurora --help` to explore the CLI.

## Use from Python

```python
from aurora.coordination import run_episode_with_trace, verify_trace
from aurora.scenarios import REFERENCE_SCENARIOS

trace = run_episode_with_trace("coordinated", REFERENCE_SCENARIOS[1], seed=7)
assert verify_trace(trace)
print(trace.result.to_dict())
```

Explore a [custom strategy](examples/custom_strategy.py) or the [PettingZoo example](examples/pettingzoo_parallel.py). The PettingZoo adapter requires `python -m pip install '.[interfaces]'`.

## Development and verification

```bash
python -m pip install -e '.[dev,figures,interfaces]'
python -m ruff check src tests examples experiments artifact
python -m pytest
python artifact/scripts/run_artifact.py --mode smoke --output-dir artifact_output_smoke
```

For the complete benchmark, fault study, interface study, and release checks:

```bash
python artifact/scripts/run_artifact.py --mode full --output-dir artifact_output_full
```

The v0.4.0 evidence contract includes 115 tests, a 480-episode benchmark, a 160-case fault study, a 160-case interface study, and 21 numeric claim checks. See the [artifact guide](artifact/README.md) for expected results and resumable runs.

## Documentation

| Start with | Guide |
|---|---|
| Installation and first run | [Quick start](docs/QUICKSTART.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) |
| Python integration | [API](docs/API.md) · [Custom strategies](docs/STRATEGY_INTERFACE.md) · [PettingZoo](docs/PETTINGZOO.md) |
| Experiment design | [Scenarios](docs/SCENARIOS.md) · [Configuration](docs/CONFIGURATION.md) · [Benchmarks](docs/BENCHMARK.md) |
| Research and reuse | [Evidence](docs/RESEARCH.md) · [Fault injection](docs/FAULT_INJECTION.md) · [Reuse patterns](docs/REUSE.md) |
| Reproducing results | [Reproducibility](REPRODUCIBILITY.md) · [Artifact evaluation](artifact/README.md) |
| Project history | [Changelog](CHANGELOG.md) · [Migration from earlier versions](docs/MIGRATION.md) |

## Credits

AURORA was created by **Shaurya Mallampati** and **Ankit Mohanty**.

See [CREDITS.md](CREDITS.md) for attribution and [third-party notices](THIRD_PARTY_NOTICES.md) for dependency acknowledgments.

## Citation

If you use AURORA in your research, cite both authors using [CITATION.cff](CITATION.cff):

```text
Mallampati, Shaurya, and Mohanty, Ankit. AURORA: Experimental Isolation for Multi-Agent Wildfire Simulation, v0.4.0, 2026.
https://github.com/ShauryaMallampati/Aurora
```

See the [archiving guide](docs/ARCHIVING.md) for version-specific citation and DOI guidance.

## Contributing and support

Contributions are welcome. Read the [contributing guide](CONTRIBUTING.md), [code of conduct](CODE_OF_CONDUCT.md), and [governance](GOVERNANCE.md). Use [GitHub issues](https://github.com/ShauryaMallampati/Aurora/issues) for bugs and questions; see [security reporting](SECURITY.md) for vulnerabilities.

Released under the [MIT License](LICENSE).
