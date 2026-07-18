# AURORA

**AURORA is a deterministic benchmark, replay, and fault-injection framework for experimentally isolated comparisons of multi-agent wildfire-response strategies.** It combines an intentionally abstract grid simulator with event-keyed environmental randomness, synchronous multi-agent timing, complete reset semantics, causal state labels, replayable traces, matched benchmarks, a custom strategy API, and an optional PettingZoo parallel environment.

> **Safety boundary:** AURORA is research and teaching software. It is not calibrated for real fires and must not be used for forecasting, incident command, aviation control, dispatch, or any safety-critical decision.

## Why AURORA exists

A simulation can produce a reproducible-looking but invalid strategy comparison when:

- policy branching shifts a shared environmental random stream;
- later agents observe earlier agents' actions within the same nominal step;
- reset retains depleted fuel or hidden state;
- suppressed cells are counted as naturally burned;
- a final score cannot be traced to a versioned trajectory;
- benchmark values live only in an undocumented notebook.

AURORA treats these as executable systems requirements rather than documentation promises.

## Publication evidence

The bundled controlled study uses 8 scenario families and 20 seeds (160 matched cases):

| Controlled comparison | Correct design | Injected fault |
|---|---:|---:|
| Irrelevant policy draw changes trajectory | 0/160 | 160/160 with shared RNG |
| Reset changes matched rerun | 0/160 | 160/160 with retained fuel |
| Sequential timing leak in adversarial states | 0/1,000 | 1,000/1,000 |

Conflating suppressed cells with natural burnout:

- overstates natural burned area by **7.403 cells on average** (scenario-cluster bootstrap 95% interval **[4.761, 9.931]**);
- changes the reactive-benefit sign in **83/160** cases;
- changes the coordinated-benefit sign in **81/160** cases;
- changes the reactive-versus-coordinated ranking in **47/160 (29.4%)** cases.

The PettingZoo adapter and direct engine match after every no-op transition in **160/160** scenario-seed cases. These are controlled software results, not claims about defect prevalence in external simulators or real wildfire effectiveness.

## Install

Core package:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install .
```

Development, figures, and external interfaces:

```bash
python -m pip install -e '.[dev,figures,interfaces]'
```

## Five-minute verification

```bash
aurora --help
aurora scenarios
aurora demo --method coordinated --scenario warm_crosswind --seed 7 --trace trace.json
aurora replay trace.json
aurora validate --output validation.json
python examples/custom_strategy.py
python examples/pettingzoo_parallel.py
python -m pytest
```

## JSys Artifact Evaluation

Smoke workflow:

```bash
python artifact/scripts/run_artifact.py --mode smoke --output-dir artifact_output_smoke
```

Full workflow after installing `.[dev,figures,interfaces]`:

```bash
python artifact/scripts/run_artifact.py --mode full --output-dir artifact_output_full
```

The full workflow runs validation, record/replay, tests with branch coverage, examples, the 480-episode benchmark, the 160-case fault study, the 160-case interface study, hash checks, and 21 numeric claim checks. Interrupted or separately scheduled generation can be verified with:

```bash
python artifact/scripts/run_artifact.py \
  --mode full --reuse-existing --output-dir artifact_output_full
```

See [`artifact/README.md`](artifact/README.md) for the complete evaluator protocol.

## Python API

### Deterministic trace and replay

```python
from aurora.coordination import run_episode_with_trace, verify_trace
from aurora.scenarios import REFERENCE_SCENARIOS

trace = run_episode_with_trace("coordinated", REFERENCE_SCENARIOS[1], seed=7)
assert verify_trace(trace)
print(trace.result.to_dict())
print(trace.sha256())
```

### Custom strategy

```python
from aurora import run_strategy_episode
from aurora.scenarios import REFERENCE_SCENARIOS
from aurora.strategy import HeuristicStrategist

result = run_strategy_episode(
    HeuristicStrategist(),
    REFERENCE_SCENARIOS[0],
    seed=5,
    method_name="my_strategy",
)
print(result)
```

### PettingZoo parallel interface

```python
from aurora.adapters import WildfireParallelEnv
from aurora.scenarios import REFERENCE_SCENARIOS

env = WildfireParallelEnv(REFERENCE_SCENARIOS[0], seed=4)
observations, infos = env.reset()
while env.agents:
    observations, rewards, terminations, truncations, infos = env.step(
        {agent: 0 for agent in env.agents}
    )
```

## Quality status

- **115 automated tests** pass; independently re-run on macOS/Python 3.10 and in the audited Linux/Python 3.13 environment.
- **93.70% branch-aware coverage**.
- Python 3.10–3.13 is declared and CI-configured.
- Ruff linting passes for source, tests, examples, experiment scripts, and artifact scripts.
- Source distribution and pure-Python wheel build and install cleanly.
- Freshly regenerated benchmark, fault-study, and interface-study artifacts match the release hashes exactly.
- The three long evidence stages completed in approximately 12.4 s, 29.3 s, and 4.5 s in the audited environment; timings are hardware dependent.

## Documentation

- [`docs/QUICKSTART.md`](docs/QUICKSTART.md) — installation and first verified run
- [`docs/API.md`](docs/API.md) — public Python API
- [`docs/FAULT_INJECTION.md`](docs/FAULT_INJECTION.md) — controlled fault study and interpretation
- [`docs/PETTINGZOO.md`](docs/PETTINGZOO.md) — parallel environment interface
- [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) — scenario and benchmark configuration
- [`docs/SCENARIOS.md`](docs/SCENARIOS.md) — bundled scenario families
- [`docs/STRATEGY_INTERFACE.md`](docs/STRATEGY_INTERFACE.md) — adding a strategy
- [`docs/BENCHMARK.md`](docs/BENCHMARK.md) — benchmark design and statistical contract
- [`docs/REUSE.md`](docs/REUSE.md) — concrete research and teaching reuse patterns
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) — common installation/runtime issues
- [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) — end-to-end evidence contract

## Publication target

Version **0.4.0** is a publication candidate for the **Journal of Systems Research (JSys)** as a **Tools/Benchmark paper** in the Real-Time and Cyber-Physical Systems area. The anonymous paper is in `paper/`; the single-blind Artifact Evaluation materials are in `artifact/`.

Before submission, the exact audited release must be pushed, public CI must pass, an anonymous review snapshot must be created, and author/funding/conflict metadata must be confirmed by the authors.

## License and support

AURORA is released under the MIT License. See `LICENSE`, `THIRD_PARTY_NOTICES.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `GOVERNANCE.md`, `SECURITY.md`, and `SUPPORT.md`.
