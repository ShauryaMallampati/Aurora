"""Deterministic wildfire simulator used by the AURORA research toolkit."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

GridSize = tuple[int, int]
UNBURNED = np.uint8(0)
BURNING = np.uint8(1)
BURNED = np.uint8(2)
SUPPRESSED = np.uint8(3)
VALID_FIRE_STATES = {0, 1, 2, 3}


@dataclass(frozen=True)
class WeatherState:
    """Simple weather container for logging and spread calculations."""

    wind_direction: tuple[float, float]
    wind_intensity: float
    humidity: float
    temperature: float


class FireSim:
    """A compact, seeded grid wildfire simulator.

    This model is intended for software and policy prototyping, not physical
    forecasting. For a fixed configuration and seed, construction and every
    reset produce the same terrain, fuel state, ignition state, and random
    sequence.
    """

    def __init__(
        self,
        grid_size: int | Iterable[int] = 50,
        wind_direction: tuple[float, float] = (1.0, 0.0),
        wind_intensity: float = 1.0,
        humidity: float = 0.35,
        temperature: float = 28.0,
        seed: int = 42,
    ) -> None:
        self.grid_size = self._coerce_grid_size(grid_size)
        self.seed = int(seed)
        self.step_count = 0
        self.weather = WeatherState(
            wind_direction=self._coerce_vector(wind_direction),
            wind_intensity=max(0.0, float(wind_intensity)),
            humidity=self._clamp(float(humidity), 0.0, 1.0),
            temperature=float(temperature),
        )
        self.terrain = np.zeros(self.grid_size, dtype=np.uint8)
        self.elevation = np.zeros(self.grid_size, dtype=np.float32)
        self.fuel_density = np.zeros(self.grid_size, dtype=np.float32)
        self.fire_state = np.zeros(self.grid_size, dtype=np.uint8)
        self._burn_age = np.zeros(self.grid_size, dtype=np.uint16)
        self._ever_ignited = np.zeros(self.grid_size, dtype=bool)
        self._build_static_layers()
        self._initial_fuel_density = self.fuel_density.copy()
        self.reset()

    def reset(self, initial_fire_grid: np.ndarray | None = None) -> np.ndarray:
        """Reset all dynamic state, including fuel and the seeded random stream."""
        self.step_count = 0
        self.fire_state.fill(UNBURNED)
        self._burn_age.fill(0)
        self._ever_ignited.fill(False)
        self.fuel_density[...] = self._initial_fuel_density

        if initial_fire_grid is None:
            self._seed_initial_fire()
        else:
            fire_grid = np.asarray(initial_fire_grid)
            if fire_grid.shape != self.grid_size:
                raise ValueError(
                    f"initial_fire_grid shape {fire_grid.shape} does not match {self.grid_size}"
                )
            if not np.issubdtype(fire_grid.dtype, np.integer):
                raise ValueError("initial_fire_grid must contain integer state codes")
            unique = {int(value) for value in np.unique(fire_grid)}
            if not unique.issubset(VALID_FIRE_STATES):
                raise ValueError(f"initial_fire_grid contains unsupported states: {sorted(unique)}")
            fire_grid = fire_grid.astype(np.uint8, copy=False)
            if np.any((fire_grid != UNBURNED) & (self.terrain == 3)):
                raise ValueError("initial_fire_grid cannot place fire states on water terrain")
            self.fire_state[...] = fire_grid
            self._ever_ignited[fire_grid != UNBURNED] = True

        return self.fire_state.copy()

    def suppress(self, row: int, col: int) -> bool:
        """Suppress one actively burning cell and return whether state changed."""
        if not (0 <= row < self.grid_size[0] and 0 <= col < self.grid_size[1]):
            raise IndexError((row, col))
        if self.fire_state[row, col] != BURNING:
            return False
        self.fire_state[row, col] = SUPPRESSED
        self._burn_age[row, col] = 0
        self._ever_ignited[row, col] = True
        return True

    def step(self) -> np.ndarray:
        """Advance the simulation by one step and return a defensive copy."""
        burning_cells = np.argwhere(self.fire_state == BURNING)
        if burning_cells.size == 0:
            self.step_count += 1
            return self.fire_state.copy()

        next_state = self.fire_state.copy()
        next_burn_age = self._burn_age.copy()
        wind_vector = self._normalized_wind_vector()
        newly_ignited: list[tuple[int, int]] = []

        for row_value, col_value in burning_cells:
            row, col = int(row_value), int(col_value)
            next_burn_age[row, col] += 1
            for n_row, n_col in self._neighbor_cells(row, col):
                if next_state[n_row, n_col] != UNBURNED or self.terrain[n_row, n_col] == 3:
                    continue
                probability = self._spread_probability(
                    source=(row, col), target=(n_row, n_col), wind_vector=wind_vector
                )
                attempt_age = int(next_burn_age[row, col])
                if self._transition_uniform((row, col), (n_row, n_col), attempt_age) < probability:
                    next_state[n_row, n_col] = BURNING
                    newly_ignited.append((n_row, n_col))

            burn_duration = 2 + int(round(float(self.fuel_density[row, col]) * 3.0))
            if next_burn_age[row, col] >= burn_duration:
                next_state[row, col] = BURNED

        self.fire_state = next_state
        self._burn_age = next_burn_age
        if newly_ignited:
            points = tuple(zip(*newly_ignited, strict=True))
            self._ever_ignited[points] = True
        burned_mask = self.fire_state == BURNED
        self.fuel_density[burned_mask] = np.minimum(self.fuel_density[burned_mask], 0.12)
        self.step_count += 1
        return self.fire_state.copy()

    def set_wind(self, wind_direction: tuple[float, float], wind_intensity: float) -> None:
        self.weather = WeatherState(
            wind_direction=self._coerce_vector(wind_direction),
            wind_intensity=max(0.0, float(wind_intensity)),
            humidity=self.weather.humidity,
            temperature=self.weather.temperature,
        )

    def set_weather(self, humidity: float | None = None, temperature: float | None = None) -> None:
        self.weather = WeatherState(
            wind_direction=self.weather.wind_direction,
            wind_intensity=self.weather.wind_intensity,
            humidity=self._clamp(
                self.weather.humidity if humidity is None else float(humidity), 0.0, 1.0
            ),
            temperature=self.weather.temperature if temperature is None else float(temperature),
        )

    def get_weather_info(self) -> dict[str, float | tuple[float, float]]:
        return {
            "wind_direction": tuple(float(x) for x in self.weather.wind_direction),
            "wind_intensity": float(self.weather.wind_intensity),
            "humidity": float(self.weather.humidity),
            "temperature": float(self.weather.temperature),
        }

    def get_fire_coverage(self) -> float:
        return float(np.mean(self.fire_state == BURNING))

    def get_fire_intensity(self) -> float:
        burning_mask = self.fire_state == BURNING
        if not np.any(burning_mask):
            return 0.0
        fuel_component = float(np.mean(self.fuel_density[burning_mask]))
        weather_component = (
            0.2 * self.weather.wind_intensity
            + 0.01 * max(0.0, self.weather.temperature - 20.0)
            + 0.3 * (1.0 - self.weather.humidity)
        )
        return fuel_component + weather_component

    def is_fire_active(self) -> bool:
        return bool(np.any(self.fire_state == BURNING))

    def affected_area(self) -> int:
        """Number of cells that have ever ignited, including later suppression."""
        return int(np.count_nonzero(self._ever_ignited))

    def state_counts(self) -> dict[str, int]:
        return {
            "burning": int(np.count_nonzero(self.fire_state == BURNING)),
            "burned": int(np.count_nonzero(self.fire_state == BURNED)),
            "suppressed": int(np.count_nonzero(self.fire_state == SUPPRESSED)),
            "affected": self.affected_area(),
        }

    def _build_static_layers(self) -> None:
        rows, cols = np.indices(self.grid_size)
        height, width = self.grid_size
        y = rows / max(1, height - 1)
        x = cols / max(1, width - 1)
        terrain_rng = np.random.default_rng(self.seed)
        noise = terrain_rng.normal(0.0, 0.08, size=self.grid_size)
        elevation = (
            0.45
            + 0.22 * np.sin(2.0 * np.pi * x)
            + 0.18 * np.cos(2.0 * np.pi * y)
            + 0.10 * np.sin(4.0 * np.pi * (x + y))
            + noise
        )
        elevation = (elevation - elevation.min()) / max(1e-6, elevation.max() - elevation.min())
        self.elevation = (elevation * 100.0).astype(np.float32)
        fuel = (
            0.55
            + 0.18 * np.cos(3.0 * np.pi * x)
            + 0.16 * np.sin(3.0 * np.pi * y)
            - 0.10 * elevation
            + terrain_rng.normal(0.0, 0.05, size=self.grid_size)
        )
        self.fuel_density = np.clip(fuel, 0.05, 1.0).astype(np.float32)
        self.terrain.fill(1)
        river_center = width * (0.18 + 0.12 * np.sin(2.0 * np.pi * y))
        river_mask = np.abs(cols - river_center) <= 1.4
        road_mask = (np.abs(rows - height // 2) <= 1) | (np.abs(cols - width // 3) <= 1)
        sparse_mask = (self.fuel_density < 0.18) & ~river_mask
        self.terrain[road_mask] = 2
        self.terrain[river_mask] = 3
        self.terrain[sparse_mask] = 0
        self.fuel_density[self.terrain == 2] *= 0.30
        self.fuel_density[self.terrain == 3] = 0.0

    def _seed_initial_fire(self) -> None:
        height, width = self.grid_size
        center = (height // 2, width // 2)
        candidate_offsets = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        for d_row, d_col in candidate_offsets:
            row = min(max(center[0] + d_row, 0), height - 1)
            col = min(max(center[1] + d_col, 0), width - 1)
            if self.terrain[row, col] == 3:
                continue
            self.fire_state[row, col] = BURNING
            self._ever_ignited[row, col] = True
        if not np.any(self.fire_state == BURNING):
            valid = np.argwhere(self.terrain != 3)
            if valid.size:
                row, col = map(int, valid[len(valid) // 2])
                self.fire_state[row, col] = BURNING
                self._ever_ignited[row, col] = True

    def _transition_uniform(
        self, source: tuple[int, int], target: tuple[int, int], attempt_age: int = 1
    ) -> float:
        """Common-random-number draw keyed by seed, time, and directed edge.

        The draw depends on source burn age rather than global time or call order.
        Matched policies therefore see the same latent spread sequence for a
        directed edge whenever the same source reaches the same burn age.
        """
        payload = (
            f"{self.seed}:{attempt_age}:{source[0]}:{source[1]}:{target[0]}:{target[1]}"
        ).encode("ascii")
        value = int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big")
        return value / float(1 << 64)

    def _spread_probability(
        self, source: tuple[int, int], target: tuple[int, int], wind_vector: np.ndarray
    ) -> float:
        s_row, s_col = source
        t_row, t_col = target
        direction = np.array([t_row - s_row, t_col - s_col], dtype=np.float32)
        norm = float(np.linalg.norm(direction))
        if norm:
            direction /= norm
        slope = float(self.elevation[t_row, t_col] - self.elevation[s_row, s_col]) / 100.0
        fuel = float(self.fuel_density[t_row, t_col])
        road_penalty = 0.20 if self.terrain[t_row, t_col] == 2 else 0.0
        wind_bonus = (
            max(0.0, float(np.dot(direction, wind_vector))) * self.weather.wind_intensity * 0.25
        )
        humidity_penalty = self.weather.humidity * 0.20
        temperature_bonus = max(0.0, self.weather.temperature - 20.0) * 0.01
        slope_bonus = max(-0.08, min(0.15, slope * 0.30))
        probability = 0.05 + (fuel * 0.42) + wind_bonus + slope_bonus + temperature_bonus
        return self._clamp(probability - humidity_penalty - road_penalty, 0.0, 0.95)

    def _neighbor_cells(self, row: int, col: int) -> Iterable[tuple[int, int]]:
        max_row, max_col = self.grid_size
        for d_row in (-1, 0, 1):
            for d_col in (-1, 0, 1):
                if d_row == 0 and d_col == 0:
                    continue
                n_row, n_col = row + d_row, col + d_col
                if 0 <= n_row < max_row and 0 <= n_col < max_col:
                    yield n_row, n_col

    def _normalized_wind_vector(self) -> np.ndarray:
        vector = np.asarray(self.weather.wind_direction, dtype=np.float32)
        norm = float(np.linalg.norm(vector))
        return np.zeros(2, dtype=np.float32) if norm == 0.0 else vector / norm

    @staticmethod
    def _coerce_grid_size(grid_size: int | Iterable[int]) -> GridSize:
        if isinstance(grid_size, int):
            if grid_size <= 0:
                raise ValueError("grid_size must be positive")
            return grid_size, grid_size
        values = tuple(int(v) for v in grid_size)
        if len(values) != 2 or values[0] <= 0 or values[1] <= 0:
            raise ValueError(f"invalid grid_size: {grid_size!r}")
        return values[0], values[1]

    @staticmethod
    def _coerce_vector(vector: tuple[float, float] | Iterable[float]) -> tuple[float, float]:
        values = tuple(float(v) for v in vector)
        if len(values) != 2:
            raise ValueError(f"wind_direction must have two components, got {vector!r}")
        return values[0], values[1]

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))
