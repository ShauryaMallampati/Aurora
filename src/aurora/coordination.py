"""Reference multi-agent response policies and deterministic episode execution."""

from __future__ import annotations

import hashlib
import json
from collections import deque
from collections.abc import Iterable
from dataclasses import asdict, dataclass

import numpy as np

from .simulator import BURNING, FireSim
from .strategy import HeuristicStrategist, Strategist, StrategyPlan, Zone
from .types import AgentState, Scenario


@dataclass(frozen=True)
class EpisodeResult:
    """Aggregate metrics from one deterministic response episode."""

    method: str
    scenario: str
    seed: int
    fire_inactive: bool
    steps: int
    initial_burning: int
    final_burning: int
    burned_area: int
    suppressed_area: int
    affected_area: int
    suppressions: int
    water_used: float
    distance_travelled: int
    strategy_updates: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> EpisodeResult:
        """Construct a validated result record from JSON-compatible data."""
        return cls(**payload)


@dataclass(frozen=True)
class EpisodeTrace:
    """Serializable deterministic trajectory for replay verification."""

    schema_version: str
    method: str
    scenario: dict[str, object]
    seed: int
    frames: tuple[dict[str, object], ...]
    result: EpisodeResult

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "method": self.method,
            "scenario": self.scenario,
            "seed": self.seed,
            "frames": list(self.frames),
            "result": self.result.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> EpisodeTrace:
        """Construct a trace from a JSON-compatible mapping."""
        if payload.get("schema_version") != "1.0":
            raise ValueError("unsupported trace schema_version")
        result_payload = payload.get("result")
        if not isinstance(result_payload, dict):
            raise ValueError("trace result must be an object")
        scenario_payload = payload.get("scenario")
        if not isinstance(scenario_payload, dict):
            raise ValueError("trace scenario must be an object")
        frames_payload = payload.get("frames")
        if not isinstance(frames_payload, list):
            raise ValueError("trace frames must be an array")
        # Validate scenario structure before retaining its serialized representation.
        Scenario.from_dict(scenario_payload)
        return cls(
            schema_version="1.0",
            method=str(payload.get("method", "")),
            scenario=scenario_payload,
            seed=int(payload.get("seed", 0)),
            frames=tuple(dict(frame) for frame in frames_payload),
            result=EpisodeResult.from_dict(result_payload),
        )

    def sha256(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _nearest_traversable(
    terrain: np.ndarray, anchor: tuple[int, int], excluded: set[tuple[int, int]]
) -> tuple[int, int]:
    rows, cols = terrain.shape
    start = (min(max(anchor[0], 0), rows - 1), min(max(anchor[1], 0), cols - 1))
    queue: deque[tuple[int, int]] = deque([start])
    visited = {start}
    while queue:
        cell = queue.popleft()
        if terrain[cell] != 3 and cell not in excluded:
            return cell
        for d_row, d_col in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            nxt = cell[0] + d_row, cell[1] + d_col
            if 0 <= nxt[0] < rows and 0 <= nxt[1] < cols and nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    raise ValueError("scenario contains no traversable spawn cell")


def _initial_agents(scenario: Scenario, sim: FireSim) -> list[AgentState]:
    rows, cols = scenario.shape
    anchors = [
        (rows // 2, 1),
        (rows // 2, cols - 2),
        (1, cols // 2),
        (rows - 2, cols // 2),
    ]
    # Add deterministic perimeter anchors for agent counts above four.
    for row in range(1, rows - 1):
        anchors.extend(((row, 1), (row, cols - 2)))
    for col in range(2, cols - 2):
        anchors.extend(((1, col), (rows - 2, col)))

    used: set[tuple[int, int]] = set()
    agents: list[AgentState] = []
    for agent_id in range(scenario.num_agents):
        anchor = anchors[agent_id % len(anchors)]
        try:
            position = _nearest_traversable(sim.terrain, anchor, used)
        except ValueError:
            # If agents outnumber traversable cells, permit deterministic sharing.
            position = _nearest_traversable(sim.terrain, anchor, set())
        used.add(position)
        agents.append(
            AgentState(
                agent_id=agent_id,
                row=position[0],
                col=position[1],
                water=scenario.water_capacity,
                water_capacity=scenario.water_capacity,
            )
        )
    return agents


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _nearest_cell(cells: Iterable[tuple[int, int]], position: tuple[int, int]) -> tuple[int, int]:
    return min(cells, key=lambda cell: (_manhattan(position, cell), cell))


def _reactive_target(
    fire_state: np.ndarray,
    agent: AgentState,
    reserved: set[tuple[int, int]],
) -> tuple[int, int] | None:
    burning = [tuple(map(int, cell)) for cell in np.argwhere(fire_state == BURNING)]
    if not burning:
        return None
    return min(
        burning,
        key=lambda cell: (_manhattan(agent.position, cell) + (4 if cell in reserved else 0), cell),
    )


def _zone_target(
    plan: StrategyPlan, agent: AgentState, fire_state: np.ndarray
) -> tuple[int, int] | None:
    zone_id = plan.target_for(agent.agent_id)
    if zone_id is None:
        return None
    zone: Zone | None = next((item for item in plan.zones if item.zone_id == zone_id), None)
    active = tuple(cell for cell in zone.cells if fire_state[cell] == BURNING) if zone else tuple()
    return _nearest_cell(active, agent.position) if active else None


def _suppression_candidate(fire_state: np.ndarray, agent: AgentState) -> tuple[int, int] | None:
    if agent.water < 1.0:
        return None
    candidates: list[tuple[int, int]] = []
    for d_row, d_col in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        row, col = agent.row + d_row, agent.col + d_col
        if (
            0 <= row < fire_state.shape[0]
            and 0 <= col < fire_state.shape[1]
            and fire_state[row, col] == BURNING
        ):
            candidates.append((row, col))
    return min(candidates) if candidates else None


def _recharge(agent: AgentState, sim: FireSim, rate: float) -> None:
    if rate > 0 and sim.terrain[agent.position] == 2:
        agent.water = min(agent.water_capacity, agent.water + rate)


def _next_step(
    start: tuple[int, int], target: tuple[int, int], terrain: np.ndarray
) -> tuple[int, int]:
    """Return one deterministic shortest-path step around water barriers."""
    if start == target:
        return start
    rows, cols = terrain.shape
    queue: deque[tuple[int, int]] = deque([start])
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while queue:
        cell = queue.popleft()
        for d_row, d_col in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            nxt = cell[0] + d_row, cell[1] + d_col
            if not (0 <= nxt[0] < rows and 0 <= nxt[1] < cols):
                continue
            if terrain[nxt] == 3 or nxt in parent:
                continue
            parent[nxt] = cell
            if nxt == target:
                current = nxt
                while parent[current] != start:
                    predecessor = parent[current]
                    if predecessor is None:
                        break
                    current = predecessor
                return current
            queue.append(nxt)
    return start


def _move(agent: AgentState, target: tuple[int, int], sim: FireSim) -> None:
    chosen = _next_step(agent.position, target, sim.terrain)
    if chosen != agent.position:
        agent.row, agent.col = chosen
        agent.distance_travelled += 1


def _frame(
    step: int, sim: FireSim, agents: list[AgentState], plan: StrategyPlan
) -> dict[str, object]:
    return {
        "step": step,
        "fire_state": sim.fire_state.tolist(),
        "state_counts": sim.state_counts(),
        "agents": [agent.to_dict() for agent in agents],
        "assignments": [list(item) for item in plan.assignments],
    }


def _initial_fire_grid(scenario: Scenario, sim: FireSim) -> np.ndarray | None:
    if scenario.ignition_points is None:
        return None
    grid = np.zeros(sim.grid_size, dtype=np.uint8)
    for point in scenario.ignition_points:
        if sim.terrain[point] == 3:
            raise ValueError(f"ignition point {point} lies on water terrain for seed {sim.seed}")
        grid[point] = BURNING
    return grid


def _execute_episode(
    method: str,
    scenario: Scenario,
    seed: int,
    record_trace: bool,
    *,
    strategist: Strategist | None = None,
    result_method: str | None = None,
) -> tuple[EpisodeResult, tuple[dict[str, object], ...]]:
    if method not in {"no_response", "reactive", "coordinated"}:
        raise ValueError("method must be 'no_response', 'reactive', or 'coordinated'")
    scenario.validate()
    sim = FireSim(
        grid_size=scenario.shape,
        wind_direction=scenario.wind_direction,
        wind_intensity=scenario.wind_intensity,
        humidity=scenario.humidity,
        temperature=scenario.temperature,
        seed=int(seed),
    )
    initial_grid = _initial_fire_grid(scenario, sim)
    if initial_grid is not None:
        sim.reset(initial_grid)
    agents = [] if method == "no_response" else _initial_agents(scenario, sim)
    initial_burning = int(np.count_nonzero(sim.fire_state == BURNING))
    strategy_engine: Strategist = strategist or HeuristicStrategist()
    plan = StrategyPlan(step=0, zones=tuple(), assignments=tuple(), rationale="Not yet computed")
    strategy_updates = 0
    steps_run = 0
    frames: list[dict[str, object]] = []
    if record_trace:
        frames.append(_frame(0, sim, agents, plan))

    for step in range(scenario.max_steps):
        if not sim.is_fire_active():
            break
        steps_run = step + 1
        snapshot = sim.fire_state.copy()
        if method == "coordinated" and (step == 0 or step % scenario.strategy_cadence == 0):
            plan = strategy_engine.plan(
                snapshot,
                (agent.position for agent in agents),
                scenario.wind_direction,
                step,
            )
            strategy_updates += 1

        if method == "no_response":
            sim.step()
            if record_trace:
                frames.append(_frame(steps_run, sim, agents, plan))
            continue

        for agent in agents:
            _recharge(agent, sim, scenario.recharge_rate)

        reserved_targets: set[tuple[int, int]] = set()
        proposals: dict[int, tuple[int, int]] = {}
        for agent in agents:
            immediate = _suppression_candidate(snapshot, agent)
            if immediate is not None:
                proposals[agent.agent_id] = immediate
                reserved_targets.add(immediate)
                continue
            target = (
                _zone_target(plan, agent, snapshot)
                if method == "coordinated"
                else _reactive_target(snapshot, agent, reserved_targets)
            )
            if target is None:
                target = _reactive_target(snapshot, agent, reserved_targets)
            if target is not None:
                reserved_targets.add(target)
                _move(agent, target, sim)

        for agent in agents:
            if agent.agent_id not in proposals:
                candidate = _suppression_candidate(snapshot, agent)
                if candidate is not None:
                    proposals[agent.agent_id] = candidate

        # Apply simultaneously planned suppressions in deterministic agent order.
        claimed: set[tuple[int, int]] = set()
        for agent in agents:
            target = proposals.get(agent.agent_id)
            if target is None or target in claimed or agent.water < 1.0:
                continue
            if sim.suppress(*target):
                claimed.add(target)
                agent.water -= 1.0
                agent.water_spent += 1.0
                agent.suppressions += 1

        sim.step()
        if record_trace:
            frames.append(_frame(steps_run, sim, agents, plan))

    counts = sim.state_counts()
    result = EpisodeResult(
        method=result_method or method,
        scenario=scenario.name,
        seed=int(seed),
        fire_inactive=not sim.is_fire_active(),
        steps=steps_run,
        initial_burning=initial_burning,
        final_burning=counts["burning"],
        burned_area=counts["burned"],
        suppressed_area=counts["suppressed"],
        affected_area=counts["affected"],
        suppressions=sum(agent.suppressions for agent in agents),
        water_used=float(sum(agent.water_spent for agent in agents)),
        distance_travelled=sum(agent.distance_travelled for agent in agents),
        strategy_updates=strategy_updates,
    )
    return result, tuple(frames)


def run_episode(method: str, scenario: Scenario, seed: int) -> EpisodeResult:
    """Run one built-in episode with no response, reactive, or coordinated dispatch."""
    result, _ = _execute_episode(method, scenario, seed, record_trace=False)
    return result


def run_strategy_episode(
    strategist: Strategist,
    scenario: Scenario,
    seed: int,
    *,
    method_name: str = "custom_strategy",
) -> EpisodeResult:
    """Run a user-supplied strategist through the coordinated execution path.

    Custom strategy traces are not serialized because arbitrary Python strategy
    objects do not have a portable reconstruction contract. The returned episode
    result remains deterministic when the supplied strategist is deterministic.
    """
    if not method_name.strip():
        raise ValueError("method_name must be non-empty")
    result, _ = _execute_episode(
        "coordinated",
        scenario,
        seed,
        record_trace=False,
        strategist=strategist,
        result_method=method_name,
    )
    return result


def run_episode_with_trace(method: str, scenario: Scenario, seed: int) -> EpisodeTrace:
    """Run an episode and return a complete deterministic JSON-ready trace."""
    result, frames = _execute_episode(method, scenario, seed, record_trace=True)
    return EpisodeTrace(
        schema_version="1.0",
        method=method,
        scenario=scenario.to_dict(),
        seed=int(seed),
        frames=frames,
        result=result,
    )


def verify_trace(trace: EpisodeTrace) -> bool:
    """Rerun a trace configuration and compare the canonical SHA-256 digest."""
    scenario = Scenario.from_dict(trace.scenario)
    replay = run_episode_with_trace(trace.method, scenario, trace.seed)
    return replay.sha256() == trace.sha256()
