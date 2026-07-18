import numpy as np
import pytest

from aurora.coordination import (
    _initial_agents,
    _next_step,
    run_episode,
    run_episode_with_trace,
    verify_trace,
)
from aurora.simulator import FireSim
from aurora.types import Scenario


def test_episode_result_is_reproducible():
    scenario = Scenario(name="small", grid_size=16, max_steps=25)
    assert (
        run_episode("coordinated", scenario, 5).to_dict()
        == run_episode("coordinated", scenario, 5).to_dict()
    )


def test_trace_is_reproducible_and_verifiable():
    scenario = Scenario(name="trace", grid_size=(12, 16), max_steps=10)
    trace = run_episode_with_trace("coordinated", scenario, 3)
    assert trace.sha256() == run_episode_with_trace("coordinated", scenario, 3).sha256()
    assert verify_trace(trace)
    assert trace.frames[0]["step"] == 0


def test_methods_have_matched_initial_conditions():
    scenario = Scenario(name="matched", grid_size=16, max_steps=10, num_agents=2)
    reactive = run_episode("reactive", scenario, 2)
    coordinated = run_episode("coordinated", scenario, 2)
    assert reactive.initial_burning == coordinated.initial_burning
    assert reactive.steps <= scenario.max_steps
    assert coordinated.steps <= scenario.max_steps


def test_coordinated_method_updates_strategy():
    scenario = Scenario(name="cadence", grid_size=16, max_steps=12, strategy_cadence=3)
    result = run_episode("coordinated", scenario, 6)
    assert result.strategy_updates >= 1


def test_reactive_method_has_no_strategy_updates():
    scenario = Scenario(name="reactive", grid_size=16, max_steps=12)
    result = run_episode("reactive", scenario, 6)
    assert result.strategy_updates == 0


def test_actual_water_use_matches_successful_suppressions():
    scenario = Scenario(name="water", grid_size=16, max_steps=20, recharge_rate=5.0)
    result = run_episode("reactive", scenario, 4)
    assert result.water_used == result.suppressions


def test_affected_area_includes_burned_burning_and_suppressed_without_double_counting():
    result = run_episode("reactive", Scenario(name="states", grid_size=16, max_steps=10), 4)
    assert result.affected_area >= result.burned_area + result.final_burning
    assert result.affected_area >= result.suppressed_area


def test_rectangular_scenario_runs():
    scenario = Scenario(name="rectangular", grid_size=(12, 20), max_steps=8)
    result = run_episode("coordinated", scenario, 1)
    assert result.scenario == "rectangular"


def test_explicit_multiple_ignitions_run():
    scenario = Scenario(
        name="multi",
        grid_size=(16, 20),
        ignition_points=((3, 15), (12, 16)),
        max_steps=10,
        num_agents=3,
    )
    result = run_episode("coordinated", scenario, 5)
    assert result.initial_burning == 2


def test_many_agents_spawn_on_valid_cells():
    scenario = Scenario(name="agents", grid_size=(12, 18), num_agents=10, max_steps=1)
    sim = FireSim(grid_size=scenario.shape, seed=1)
    agents = _initial_agents(scenario, sim)
    assert len(agents) == 10
    assert all(sim.terrain[agent.position] != 3 for agent in agents)
    assert len({agent.position for agent in agents}) == 10


def test_shortest_path_detours_around_water():
    terrain = np.ones((5, 5), dtype=np.uint8)
    terrain[2, 1:4] = 3
    first = _next_step((1, 2), (3, 2), terrain)
    assert first in {(1, 1), (1, 3)}
    assert terrain[first] != 3


def test_unreachable_target_leaves_agent_in_place():
    terrain = np.ones((5, 5), dtype=np.uint8)
    terrain[1, 2] = terrain[2, 1] = terrain[2, 3] = terrain[3, 2] = 3
    assert _next_step((2, 2), (0, 0), terrain) == (2, 2)


def test_invalid_method_rejected():
    with pytest.raises(ValueError, match="method"):
        run_episode("oracle", Scenario(name="invalid"), 1)


def test_invalid_scenario_rejected():
    with pytest.raises(ValueError, match="grid_size"):
        run_episode("reactive", Scenario(name="bad", grid_size=4), 1)


def test_ignition_on_water_rejected_for_actual_seed():
    sim = FireSim(grid_size=12, seed=3)
    water = tuple(map(int, np.argwhere(sim.terrain == 3)[0]))
    scenario = Scenario(name="bad_ignition", grid_size=12, ignition_points=(water,))
    with pytest.raises(ValueError, match="water"):
        run_episode("reactive", scenario, 3)


def test_trace_json_roundtrip():
    from aurora.coordination import EpisodeTrace

    trace = run_episode_with_trace(
        "coordinated", Scenario(name="roundtrip", grid_size=12, max_steps=5), 8
    )
    restored = EpisodeTrace.from_dict(trace.to_dict())
    assert restored == trace
    assert restored.sha256() == trace.sha256()
