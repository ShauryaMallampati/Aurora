# Public API

## Scenarios

```python
from aurora import Scenario

scenario = Scenario(
    name="custom",
    grid_size=(24, 32),
    wind_direction=(1.0, 0.2),
    wind_intensity=1.5,
    humidity=0.25,
    temperature=34.0,
    max_steps=80,
    num_agents=3,
    water_capacity=7.0,
    recharge_rate=1.0,
    strategy_cadence=4,
    ignition_points=((10, 12), (14, 20)),
)
scenario.validate()
```

`Scenario.to_dict()` and `Scenario.from_dict()` provide a JSON-compatible, validated representation.

## Direct simulation

```python
from aurora import FireSim

sim = FireSim(grid_size=(24, 32), seed=11)
while sim.is_fire_active() and sim.step_count < 80:
    sim.step()
print(sim.state_counts())
```

Important methods:

- `reset(initial_fire_grid=None)` — restores all dynamic state;
- `step()` — advances one deterministic transition;
- `suppress(row, col)` — suppresses one active cell;
- `state_counts()` — reports burning, naturally burned, suppressed, and affected cells;
- `affected_area()` — counts cells that have ever ignited.

## Built-in episodes

```python
from aurora import run_episode
from aurora.scenarios import REFERENCE_SCENARIOS

result = run_episode("reactive", REFERENCE_SCENARIOS[0], seed=3)
print(result.to_dict())
```

Methods are `no_response`, `reactive`, and `coordinated`.

## Custom strategies

```python
from aurora import run_strategy_episode
from aurora.scenarios import REFERENCE_SCENARIOS
from aurora.strategy import HeuristicStrategist

result = run_strategy_episode(
    HeuristicStrategist(),
    REFERENCE_SCENARIOS[0],
    seed=3,
    method_name="custom",
)
```

A strategist implements the `Strategist` protocol and returns a `StrategyPlan`. See `docs/STRATEGY_INTERFACE.md` and `examples/custom_strategy.py`.

## Trace and replay

```python
from aurora import run_episode_with_trace, verify_trace
from aurora.scenarios import REFERENCE_SCENARIOS

trace = run_episode_with_trace("coordinated", REFERENCE_SCENARIOS[0], seed=3)
assert verify_trace(trace)
payload = trace.to_dict()
digest = trace.sha256()
```

`EpisodeTrace.from_dict()` validates schema version and required structures before replay.

## Benchmark

```python
from aurora.benchmark import run_reference_benchmark

summary = run_reference_benchmark("benchmark_output", seeds=range(20))
```

## Fault study

```python
from aurora.diagnostics import run_fault_ablation

summary = run_fault_ablation(
    "fault_output",
    seeds=range(20),
    bootstrap_draws=2000,
)
```

## Interoperability study

```python
from aurora.interoperability import run_interface_case_study

summary = run_interface_case_study("interface_output", seeds=range(20))
```

## PettingZoo adapter

```python
from aurora.adapters import WildfireParallelEnv
```

The adapter requires `aurora-wildfire[interfaces]`. See `docs/PETTINGZOO.md`.
