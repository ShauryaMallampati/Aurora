"""Shared data structures for AURORA."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

GridShape = int | tuple[int, int]


@dataclass(frozen=True)
class Scenario:
    """A validated deterministic scenario configuration.

    ``grid_size`` accepts either one integer for a square grid or ``(rows, cols)``
    for a rectangular grid. ``ignition_points`` can be used to define one or more
    explicit initial burning cells; when omitted, :class:`aurora.simulator.FireSim`
    uses its deterministic central ignition cluster.
    """

    name: str
    grid_size: GridShape = 24
    wind_direction: tuple[float, float] = (1.0, 0.0)
    wind_intensity: float = 1.0
    humidity: float = 0.35
    temperature: float = 30.0
    max_steps: int = 80
    num_agents: int = 2
    water_capacity: float = 8.0
    recharge_rate: float = 1.5
    strategy_cadence: int = 5
    ignition_points: tuple[tuple[int, int], ...] | None = None

    @property
    def shape(self) -> tuple[int, int]:
        if isinstance(self.grid_size, int):
            return self.grid_size, self.grid_size
        return int(self.grid_size[0]), int(self.grid_size[1])

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        rows, cols = self.shape
        if rows < 8 or cols < 8:
            raise ValueError("grid_size dimensions must each be at least 8")
        if self.max_steps <= 0:
            raise ValueError("max_steps must be positive")
        if self.num_agents <= 0:
            raise ValueError("num_agents must be positive")
        if self.water_capacity <= 0:
            raise ValueError("water_capacity must be positive")
        if self.recharge_rate < 0:
            raise ValueError("recharge_rate must be non-negative")
        if self.strategy_cadence <= 0:
            raise ValueError("strategy_cadence must be positive")
        if not 0.0 <= self.humidity <= 1.0:
            raise ValueError("humidity must lie in [0, 1]")
        if self.wind_intensity < 0.0:
            raise ValueError("wind_intensity must be non-negative")
        if len(self.wind_direction) != 2:
            raise ValueError("wind_direction must contain two components")
        if self.ignition_points is not None:
            if not self.ignition_points:
                raise ValueError("ignition_points must be None or non-empty")
            for row, col in self.ignition_points:
                if not (0 <= row < rows and 0 <= col < cols):
                    raise ValueError(f"ignition point {(row, col)} lies outside {self.shape}")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if isinstance(self.grid_size, tuple):
            payload["grid_size"] = list(self.grid_size)
        if self.ignition_points is not None:
            payload["ignition_points"] = [list(point) for point in self.ignition_points]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Scenario:
        data = dict(payload)
        if isinstance(data.get("grid_size"), list):
            data["grid_size"] = tuple(int(value) for value in data["grid_size"])
        if isinstance(data.get("wind_direction"), list):
            data["wind_direction"] = tuple(float(value) for value in data["wind_direction"])
        if data.get("ignition_points") is not None:
            data["ignition_points"] = tuple(
                (int(point[0]), int(point[1])) for point in data["ignition_points"]
            )
        scenario = cls(**data)
        scenario.validate()
        return scenario


@dataclass
class AgentState:
    """Mutable state of one response agent."""

    agent_id: int
    row: int
    col: int
    water: float
    water_capacity: float
    distance_travelled: int = 0
    suppressions: int = 0
    water_spent: float = 0.0

    @property
    def position(self) -> tuple[int, int]:
        return self.row, self.col

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
