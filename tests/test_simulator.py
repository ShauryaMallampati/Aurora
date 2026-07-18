import numpy as np
import pytest

from aurora.simulator import BURNED, BURNING, SUPPRESSED, FireSim


def _first_nonwater(sim: FireSim) -> tuple[int, int]:
    return tuple(map(int, np.argwhere(sim.terrain != 3)[0]))


def _first_water(sim: FireSim) -> tuple[int, int]:
    return tuple(map(int, np.argwhere(sim.terrain == 3)[0]))


def test_seeded_simulators_match():
    first = FireSim(grid_size=18, seed=3)
    second = FireSim(grid_size=18, seed=3)
    for _ in range(5):
        assert np.array_equal(first.step(), second.step())


def test_different_seeds_change_static_layers():
    first = FireSim(grid_size=18, seed=3)
    second = FireSim(grid_size=18, seed=4)
    assert not np.array_equal(first.elevation, second.elevation)


def test_rectangular_grid_supported():
    sim = FireSim(grid_size=(12, 18), seed=1)
    assert sim.grid_size == (12, 18)
    assert sim.fire_state.shape == (12, 18)


def test_reset_rejects_wrong_shape():
    sim = FireSim(grid_size=12)
    with pytest.raises(ValueError, match="shape"):
        sim.reset(np.zeros((10, 10), dtype=np.uint8))


def test_reset_accepts_custom_fire_grid():
    sim = FireSim(grid_size=12)
    grid = np.zeros((12, 12), dtype=np.uint8)
    point = _first_nonwater(sim)
    grid[point] = BURNING
    state = sim.reset(grid)
    assert state[point] == BURNING
    assert sim.affected_area() == 1


def test_reset_rejects_unsupported_state():
    sim = FireSim(grid_size=12)
    grid = np.zeros((12, 12), dtype=np.uint8)
    grid[_first_nonwater(sim)] = 9
    with pytest.raises(ValueError, match="unsupported"):
        sim.reset(grid)


def test_reset_rejects_fire_on_water():
    sim = FireSim(grid_size=12)
    grid = np.zeros((12, 12), dtype=np.uint8)
    grid[_first_water(sim)] = BURNING
    with pytest.raises(ValueError, match="water"):
        sim.reset(grid)


def test_reset_restores_fuel_state_and_rng():
    sim = FireSim(grid_size=16, seed=7)
    initial_fire = sim.fire_state.copy()
    initial_fuel = sim.fuel_density.copy()
    first_sequence = [sim.step() for _ in range(5)]
    sim.reset()
    assert np.array_equal(sim.fire_state, initial_fire)
    assert np.array_equal(sim.fuel_density, initial_fuel)
    second_sequence = [sim.step() for _ in range(5)]
    assert all(np.array_equal(a, b) for a, b in zip(first_sequence, second_sequence, strict=True))


def test_suppression_is_not_counted_as_natural_burn():
    sim = FireSim(grid_size=12, seed=2)
    point = tuple(map(int, np.argwhere(sim.fire_state == BURNING)[0]))
    affected_before = sim.affected_area()
    assert sim.suppress(*point)
    assert sim.fire_state[point] == SUPPRESSED
    assert np.count_nonzero(sim.fire_state == BURNED) == 0
    assert sim.affected_area() == affected_before


def test_suppress_nonburning_cell_is_noop():
    sim = FireSim(grid_size=12)
    point = tuple(map(int, np.argwhere(sim.fire_state == 0)[0]))
    assert sim.suppress(*point) is False


def test_suppress_out_of_bounds_rejected():
    sim = FireSim(grid_size=12)
    with pytest.raises(IndexError):
        sim.suppress(-1, 0)


def test_water_never_ignites():
    sim = FireSim(grid_size=20, seed=9, wind_intensity=2.0, humidity=0.0, temperature=45.0)
    for _ in range(30):
        sim.step()
    assert np.all(sim.fire_state[sim.terrain == 3] == 0)


def test_weather_is_clamped_and_serializable():
    sim = FireSim(grid_size=10, humidity=2.0)
    assert sim.get_weather_info()["humidity"] == 1.0
    sim.set_weather(humidity=-1.0, temperature=35.0)
    info = sim.get_weather_info()
    assert info["humidity"] == 0.0
    assert info["temperature"] == 35.0


def test_negative_wind_intensity_is_clamped():
    sim = FireSim(grid_size=10, wind_intensity=-2.0)
    assert sim.get_weather_info()["wind_intensity"] == 0.0
    sim.set_wind((0.0, 1.0), -4.0)
    assert sim.get_weather_info()["wind_intensity"] == 0.0


def test_no_fire_step_is_safe():
    sim = FireSim(grid_size=10)
    sim.fire_state.fill(0)
    before = sim.step_count
    state = sim.step()
    assert not np.any(state == BURNING)
    assert sim.step_count == before + 1


def test_step_returns_defensive_copy():
    sim = FireSim(grid_size=10)
    state = sim.step()
    state.fill(99)
    assert not np.any(sim.fire_state == 99)


def test_state_counts_are_consistent():
    sim = FireSim(grid_size=12)
    counts = sim.state_counts()
    assert counts["burning"] == np.count_nonzero(sim.fire_state == BURNING)
    assert counts["affected"] >= counts["burning"]


@pytest.mark.parametrize("bad", [0, -1, (4,), (8, 0), (8, 8, 8)])
def test_invalid_grid_sizes_rejected(bad):
    with pytest.raises((ValueError, TypeError)):
        FireSim(grid_size=bad)


def test_invalid_wind_vector_rejected():
    with pytest.raises(ValueError, match="two components"):
        FireSim(grid_size=10, wind_direction=(1.0,))


def test_transition_randomness_is_independent_of_call_order():
    sim = FireSim(grid_size=12, seed=9)
    first = sim._transition_uniform((1, 1), (1, 2))
    _ = sim._transition_uniform((3, 3), (4, 4))
    second = sim._transition_uniform((1, 1), (1, 2))
    assert first == second
    assert sim._transition_uniform((1, 1), (1, 2), attempt_age=2) != first
