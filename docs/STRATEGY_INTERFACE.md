# Strategy Interface

A strategy maps a start-of-step snapshot and responder positions to a `StrategyPlan`. It does not mutate the simulator.

## Protocol

```python
from typing import Protocol

class Strategist(Protocol):
    def plan(self, fire_state, agent_positions, wind_direction, step):
        ...
```

The returned `StrategyPlan` contains:

- the planning step;
- zero or more connected-component zones;
- deterministic `(agent_id, zone_id)` assignments;
- a human-readable rationale.

## Execute a custom strategy

```python
from aurora import run_strategy_episode
from aurora.scenarios import REFERENCE_SCENARIOS
from aurora.strategy import HeuristicStrategist

result = run_strategy_episode(
    HeuristicStrategist(),
    REFERENCE_SCENARIOS[0],
    seed=12,
    method_name="candidate_controller",
)
```

## Required behavior

A custom strategist should:

- be deterministic for identical inputs if reproducible comparisons are required;
- treat `fire_state` as read-only;
- use stable tie breaking;
- return only valid zone identifiers;
- avoid network or global mutable state during benchmark runs;
- document any additional information it uses.

The coordinator retains responsibility for movement, water, simultaneous suppression resolution, environmental transition, and result accounting.

See `examples/custom_strategy.py` for an executable implementation.
