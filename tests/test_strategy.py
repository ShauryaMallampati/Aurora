import numpy as np
import pytest

from aurora.strategy import HeuristicStrategist


def test_two_components_become_two_zones():
    grid = np.zeros((8, 8), dtype=np.uint8)
    grid[1:3, 1:3] = 1
    grid[6, 6] = 1
    plan = HeuristicStrategist().plan(grid, [(0, 0), (7, 7)], (1.0, 0.0), 0)
    assert len(plan.zones) == 2
    assert sorted(zone.size for zone in plan.zones) == [1, 4]


def test_eight_connectivity_merges_diagonal_cells():
    grid = np.zeros((8, 8), dtype=np.uint8)
    grid[2, 2] = grid[3, 3] = 1
    assert len(HeuristicStrategist(4).plan(grid, [(0, 0)], (1.0, 0.0), 0).zones) == 2
    assert len(HeuristicStrategist(8).plan(grid, [(0, 0)], (1.0, 0.0), 0).zones) == 1


def test_assignments_avoid_duplicates_when_possible():
    grid = np.zeros((8, 8), dtype=np.uint8)
    grid[1, 1] = 1
    grid[6, 6] = 1
    plan = HeuristicStrategist().plan(grid, [(0, 0), (7, 7)], (1.0, 0.0), 0)
    assigned = [zone_id for _, zone_id in plan.assignments]
    assert len(set(assigned)) == 2


def test_more_agents_than_zones_reuses_zones_deterministically():
    grid = np.zeros((8, 8), dtype=np.uint8)
    grid[4, 4] = 1
    plan = HeuristicStrategist().plan(grid, [(0, 0), (7, 7), (0, 7)], (1.0, 0.0), 0)
    assert plan.assignments == ((0, 0), (1, 0), (2, 0))


def test_empty_fire_returns_empty_plan():
    plan = HeuristicStrategist().plan(np.zeros((6, 6)), [(0, 0)], (0.0, 0.0), 4)
    assert plan.zones == ()
    assert plan.assignments == ()
    assert "No active" in plan.rationale


def test_plan_is_deterministic():
    grid = np.zeros((8, 8), dtype=np.uint8)
    grid[2:5, 2] = 1
    strategist = HeuristicStrategist()
    first = strategist.plan(grid, [(0, 0)], (1.0, 1.0), 3)
    second = strategist.plan(grid, [(0, 0)], (1.0, 1.0), 3)
    assert first.to_dict() == second.to_dict()


def test_zone_ids_are_renumbered_after_priority_sort():
    grid = np.zeros((10, 10), dtype=np.uint8)
    grid[1, 1] = 1
    grid[7:9, 7:9] = 1
    plan = HeuristicStrategist().plan(grid, [(0, 0)], (1.0, 1.0), 0)
    assert [zone.zone_id for zone in plan.zones] == [0, 1]
    assert plan.zones[0].size == 4


def test_invalid_connectivity_rejected():
    with pytest.raises(ValueError):
        HeuristicStrategist(connectivity=6)


def test_non_2d_fire_state_rejected():
    with pytest.raises(ValueError, match="2-D"):
        HeuristicStrategist().plan(np.zeros(8), [(0, 0)], (1.0, 0.0), 0)


def test_out_of_bounds_agent_rejected():
    with pytest.raises(ValueError, match="outside"):
        HeuristicStrategist().plan(np.zeros((8, 8)), [(9, 0)], (1.0, 0.0), 0)


def test_negative_step_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        HeuristicStrategist().plan(np.zeros((8, 8)), [(0, 0)], (1.0, 0.0), -1)


def test_invalid_wind_vector_rejected():
    with pytest.raises(ValueError, match="two components"):
        HeuristicStrategist().plan(np.zeros((8, 8)), [(0, 0)], (1.0,), 0)
