"""Implement and run a user-supplied deterministic strategist."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from aurora import Scenario, StrategyPlan, run_strategy_episode
from aurora.strategy import HeuristicStrategist


class LargestFrontFirst:
    """Assign every responder to the largest detected 8-connected front."""

    def __init__(self) -> None:
        self._detector = HeuristicStrategist(connectivity=8)

    def plan(
        self,
        fire_state: np.ndarray,
        agent_positions: Iterable[tuple[int, int]],
        wind_direction: tuple[float, float],
        step: int,
    ) -> StrategyPlan:
        positions = tuple(agent_positions)
        base = self._detector.plan(fire_state, positions, wind_direction, step)
        assignments = (
            tuple((agent_id, 0) for agent_id in range(len(positions))) if base.zones else tuple()
        )
        return StrategyPlan(
            step=step,
            zones=base.zones,
            assignments=assignments,
            rationale="Assign all responders to the highest-priority connected front.",
            source="example_largest_front_first",
        )


scenario = Scenario(name="custom-example", grid_size=20, max_steps=40, num_agents=3)
result = run_strategy_episode(LargestFrontFirst(), scenario, seed=7, method_name="largest_front")
print(result.to_dict())
