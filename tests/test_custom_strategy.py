from __future__ import annotations

import numpy as np
import pytest

from aurora import Scenario, StrategyPlan, run_strategy_episode
from aurora.strategy import HeuristicStrategist


class ExternalStrategy:
    def plan(self, fire_state, agent_positions, wind_direction, step):
        positions = tuple(agent_positions)
        base = HeuristicStrategist(connectivity=8).plan(
            np.asarray(fire_state), positions, wind_direction, step
        )
        assignments = (
            tuple((agent_id, 0) for agent_id in range(len(positions))) if base.zones else ()
        )
        return StrategyPlan(
            step=step,
            zones=base.zones,
            assignments=assignments,
            rationale="external test strategy",
            source="test_external_strategy",
        )


def test_custom_strategy_runs_deterministically():
    scenario = Scenario(name="custom", grid_size=16, max_steps=20, num_agents=3)
    first = run_strategy_episode(ExternalStrategy(), scenario, 9, method_name="external")
    second = run_strategy_episode(ExternalStrategy(), scenario, 9, method_name="external")
    assert first == second
    assert first.method == "external"
    assert first.strategy_updates > 0


def test_custom_strategy_requires_method_name():
    with pytest.raises(ValueError, match="method_name"):
        run_strategy_episode(ExternalStrategy(), Scenario(name="x"), 1, method_name=" ")
