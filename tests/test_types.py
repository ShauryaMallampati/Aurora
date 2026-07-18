import pytest

from aurora.types import Scenario


def test_scenario_serializes_square_grid():
    scenario = Scenario(name="example")
    assert scenario.to_dict()["name"] == "example"
    assert scenario.shape == (24, 24)


def test_scenario_roundtrip_rectangular_and_ignitions():
    scenario = Scenario(
        name="example",
        grid_size=(12, 18),
        ignition_points=((2, 2), (8, 14)),
    )
    assert Scenario.from_dict(scenario.to_dict()) == scenario


@pytest.mark.parametrize(
    "scenario, message",
    [
        (Scenario(name="", max_steps=1), "name"),
        (Scenario(name="shape", grid_size=(8, 4)), "grid_size"),
        (Scenario(name="steps", max_steps=0), "max_steps"),
        (Scenario(name="agents", num_agents=0), "num_agents"),
        (Scenario(name="water", water_capacity=0), "water_capacity"),
        (Scenario(name="recharge", recharge_rate=-1), "recharge_rate"),
        (Scenario(name="humidity", humidity=1.2), "humidity"),
        (Scenario(name="wind", wind_intensity=-1), "wind_intensity"),
        (Scenario(name="cadence", strategy_cadence=0), "strategy_cadence"),
        (Scenario(name="ignition", grid_size=8, ignition_points=((9, 1),)), "ignition"),
    ],
)
def test_scenario_validation(scenario, message):
    with pytest.raises(ValueError, match=message):
        scenario.validate()


def test_empty_ignition_points_rejected():
    with pytest.raises(ValueError, match="ignition_points"):
        Scenario(name="empty", ignition_points=()).validate()
