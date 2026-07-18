"""Structured, deterministic strategy generation for wildfire-response agents."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Protocol

import numpy as np


class Strategist(Protocol):
    """Protocol implemented by deterministic, learned, or external strategists."""

    def plan(
        self,
        fire_state: np.ndarray,
        agent_positions: Iterable[tuple[int, int]],
        wind_direction: tuple[float, float],
        step: int,
    ) -> StrategyPlan: ...


@dataclass(frozen=True)
class Zone:
    """A connected burning region summarized for assignment."""

    zone_id: int
    cells: tuple[tuple[int, int], ...]
    centroid: tuple[float, float]
    size: int
    downwind_score: float
    priority: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StrategyPlan:
    """Machine-checkable strategy plan produced from simulator state."""

    step: int
    zones: tuple[Zone, ...]
    assignments: tuple[tuple[int, int], ...]
    rationale: str
    source: str = "deterministic_heuristic"
    schema_version: str = "1.0"

    def target_for(self, agent_id: int) -> int | None:
        for current_agent, zone_id in self.assignments:
            if current_agent == agent_id:
                return zone_id
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "zones": [zone.to_dict() for zone in self.zones],
            "assignments": [list(item) for item in self.assignments],
            "rationale": self.rationale,
            "source": self.source,
            "schema_version": self.schema_version,
        }


class HeuristicStrategist:
    """Create reproducible zone priorities and non-duplicated assignments.

    This component is deliberately deterministic. It provides the same structured
    interface that a language-model strategist may implement, while keeping the
    core package testable offline and avoiding claims about unverified LLM quality.
    """

    def __init__(self, connectivity: int = 4) -> None:
        if connectivity not in (4, 8):
            raise ValueError("connectivity must be 4 or 8")
        self.connectivity = connectivity

    def plan(
        self,
        fire_state: np.ndarray,
        agent_positions: Iterable[tuple[int, int]],
        wind_direction: tuple[float, float],
        step: int,
    ) -> StrategyPlan:
        grid = np.asarray(fire_state)
        if grid.ndim != 2:
            raise ValueError("fire_state must be a 2-D array")
        if int(step) < 0:
            raise ValueError("step must be non-negative")
        if len(tuple(wind_direction)) != 2:
            raise ValueError("wind_direction must have two components")
        positions = tuple((int(r), int(c)) for r, c in agent_positions)
        for position in positions:
            if not (0 <= position[0] < grid.shape[0] and 0 <= position[1] < grid.shape[1]):
                raise ValueError(f"agent position {position} lies outside fire_state")
        zones = self._zones(grid, wind_direction)
        assignments = self._assign(zones, positions)
        rationale = (
            "Prioritize larger connected fronts and their downwind exposure, "
            "then assign agents to distinct zones when possible."
            if zones
            else "No active fire cells were detected."
        )
        return StrategyPlan(
            step=int(step),
            zones=zones,
            assignments=assignments,
            rationale=rationale,
        )

    def _zones(
        self, fire_state: np.ndarray, wind_direction: tuple[float, float]
    ) -> tuple[Zone, ...]:
        burning = fire_state == 1
        visited = np.zeros_like(burning, dtype=bool)
        components: list[list[tuple[int, int]]] = []
        rows, cols = burning.shape
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if self.connectivity == 8:
            directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        for row, col in np.argwhere(burning):
            row, col = int(row), int(col)
            if visited[row, col]:
                continue
            stack = [(row, col)]
            visited[row, col] = True
            component: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                component.append(current)
                for d_row, d_col in directions:
                    n_row, n_col = current[0] + d_row, current[1] + d_col
                    if (
                        0 <= n_row < rows
                        and 0 <= n_col < cols
                        and burning[n_row, n_col]
                        and not visited[n_row, n_col]
                    ):
                        visited[n_row, n_col] = True
                        stack.append((n_row, n_col))
            components.append(component)

        wind = np.asarray(wind_direction, dtype=float)
        norm = float(np.linalg.norm(wind))
        wind = wind / norm if norm else np.zeros(2, dtype=float)
        center = np.array([(rows - 1) / 2.0, (cols - 1) / 2.0])
        scale = max(rows, cols)

        zones: list[Zone] = []
        for zone_id, cells in enumerate(components):
            array = np.asarray(cells, dtype=float)
            centroid_array = array.mean(axis=0)
            downwind = float(np.dot((centroid_array - center) / scale, wind))
            priority = float(len(cells) + max(0.0, downwind) * max(2.0, len(cells) * 0.5))
            zones.append(
                Zone(
                    zone_id=zone_id,
                    cells=tuple(sorted(cells)),
                    centroid=(float(centroid_array[0]), float(centroid_array[1])),
                    size=len(cells),
                    downwind_score=downwind,
                    priority=priority,
                )
            )
        zones.sort(key=lambda zone: (-zone.priority, zone.zone_id))
        # Re-number after sorting so serialized priorities are stable and intuitive.
        return tuple(
            Zone(
                zone_id=index,
                cells=zone.cells,
                centroid=zone.centroid,
                size=zone.size,
                downwind_score=zone.downwind_score,
                priority=zone.priority,
            )
            for index, zone in enumerate(zones)
        )

    @staticmethod
    def _assign(
        zones: tuple[Zone, ...], positions: tuple[tuple[int, int], ...]
    ) -> tuple[tuple[int, int], ...]:
        if not zones:
            return tuple()
        remaining = set(range(len(zones)))
        assignments: list[tuple[int, int]] = []
        for agent_id, position in enumerate(positions):
            candidates = remaining or set(range(len(zones)))
            selected = min(
                candidates,
                key=lambda zone_index: (
                    abs(position[0] - zones[zone_index].centroid[0])
                    + abs(position[1] - zones[zone_index].centroid[1])
                    - 0.25 * zones[zone_index].priority,
                    zone_index,
                ),
            )
            assignments.append((agent_id, selected))
            remaining.discard(selected)
        return tuple(assignments)
