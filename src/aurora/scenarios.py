"""Curated scenario profiles and JSON configuration helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from .types import Scenario

REFERENCE_SCENARIOS = (
    Scenario(
        name="calm_humid",
        wind_direction=(1.0, 0.0),
        wind_intensity=0.6,
        humidity=0.58,
        temperature=24.0,
    ),
    Scenario(
        name="warm_crosswind",
        wind_direction=(0.0, 1.0),
        wind_intensity=1.1,
        humidity=0.38,
        temperature=31.0,
    ),
    Scenario(
        name="hot_dry",
        wind_direction=(1.0, 1.0),
        wind_intensity=1.4,
        humidity=0.22,
        temperature=38.0,
    ),
    Scenario(
        name="strong_northwind",
        wind_direction=(-1.0, 0.0),
        wind_intensity=1.8,
        humidity=0.30,
        temperature=34.0,
    ),
    Scenario(
        name="constrained_water",
        wind_direction=(1.0, 0.5),
        wind_intensity=1.7,
        humidity=0.24,
        temperature=37.0,
        water_capacity=3.0,
        recharge_rate=0.5,
        max_steps=60,
    ),
    Scenario(
        name="dual_front",
        grid_size=(24, 30),
        wind_direction=(0.5, 1.0),
        wind_intensity=1.5,
        humidity=0.28,
        temperature=35.0,
        max_steps=70,
        num_agents=3,
        water_capacity=6.0,
        ignition_points=((8, 20), (16, 22)),
    ),
    Scenario(
        name="single_responder",
        wind_direction=(-0.5, 1.0),
        wind_intensity=1.6,
        humidity=0.25,
        temperature=36.0,
        num_agents=1,
        water_capacity=5.0,
        recharge_rate=0.5,
        max_steps=60,
    ),
    Scenario(
        name="large_grid_high_wind",
        grid_size=32,
        wind_direction=(1.0, -0.5),
        wind_intensity=2.0,
        humidity=0.20,
        temperature=39.0,
        num_agents=3,
        water_capacity=6.0,
        max_steps=80,
    ),
)


def save_scenarios(path: str | Path, scenarios: Iterable[Scenario]) -> Path:
    destination = Path(path)
    payload = {"schema_version": "1.0", "scenarios": [item.to_dict() for item in scenarios]}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return destination


def load_scenarios(path: str | Path) -> tuple[Scenario, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        raise ValueError("unsupported scenario manifest schema_version")
    scenarios = tuple(Scenario.from_dict(item) for item in payload.get("scenarios", []))
    if not scenarios:
        raise ValueError("scenario manifest contains no scenarios")
    names = [item.name for item in scenarios]
    if len(set(names)) != len(names):
        raise ValueError("scenario names must be unique")
    return scenarios
