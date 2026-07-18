# PettingZoo Parallel Environment

AURORA provides an optional `pettingzoo.ParallelEnv` adapter with one responder per agent.

## Install

```bash
python -m pip install '.[interfaces]'
```

## Basic use

```python
from aurora.adapters import WildfireParallelEnv
from aurora.scenarios import REFERENCE_SCENARIOS

env = WildfireParallelEnv(REFERENCE_SCENARIOS[0], seed=7)
observations, infos = env.reset()

while env.agents:
    actions = {agent: 0 for agent in env.agents}  # stay
    observations, rewards, terminations, truncations, infos = env.step(actions)
```

## Actions

| Code | Meaning |
|---:|---|
| 0 | stay |
| 1–4 | move up, down, left, right |
| 5 | suppress current cell |
| 6–9 | suppress up, down, left, right |

All proposals are computed from one start-of-step snapshot and then applied deterministically. Duplicate suppression targets are applied once.

## Observations

Each agent observes:

- `fire_state` — integer grid with unburned, burning, naturally burned, and suppressed states;
- `terrain` — traversable, recharge, and water-barrier grid;
- `position` — responder row and column;
- `water` — remaining water;
- `step` — current step.

`env.state()` returns a centralized vector for centralized-training workflows.

## Reward

The default shared reward is the negative increase in affected cells during the transition. It is a minimal interoperability default, **not** a validated operational objective.

## Equivalence evidence

The bundled interface study compares direct-engine and adapter no-op trajectories after every transition across 8 scenarios × 20 seeds. The release result is 160/160 exact per-step matches, 160/160 final digest matches, and 160/160 affected-area matches.

Run it with:

```bash
python experiments/scripts/run_interface_case_study.py \
  --output-dir interface_output --num-seeds 20
```

This verifies adapter transparency under inert control; it does not prove equivalence for every possible external policy.
