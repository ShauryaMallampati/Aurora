"""PettingZoo parallel-environment adapter for AURORA.

The adapter is intentionally small and transparent. It exposes one responder per
PettingZoo agent while preserving AURORA's simultaneous action semantics and
counter-based environmental randomness.
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    from gymnasium import spaces
    from pettingzoo import ParallelEnv
except ImportError as exc:  # pragma: no cover - exercised in packaging tests
    raise ImportError(
        "The PettingZoo adapter requires the optional 'interfaces' extra: "
        "pip install 'aurora-wildfire[interfaces]'"
    ) from exc

from ..coordination import _initial_agents, _initial_fire_grid, _recharge
from ..simulator import BURNING, FireSim
from ..types import AgentState, Scenario

# stay, up, down, left, right, suppress-here, suppress-up, suppress-down,
# suppress-left, suppress-right
_ACTION_DELTAS: dict[int, tuple[int, int] | None] = {
    0: None,
    1: (-1, 0),
    2: (1, 0),
    3: (0, -1),
    4: (0, 1),
    5: (0, 0),
    6: (-1, 0),
    7: (1, 0),
    8: (0, -1),
    9: (0, 1),
}


class WildfireParallelEnv(ParallelEnv):
    """PettingZoo ``ParallelEnv`` wrapper around one AURORA scenario.

    Actions 0--4 are stay/up/down/left/right. Actions 5--9 suppress the
    current/up/down/left/right cell. Movement and suppression proposals are
    computed from one start-of-step snapshot and then applied deterministically.
    Every responder receives the same reward: minus the number of newly affected
    cells in that step. This reward is a minimal adapter default, not an
    operational objective or benchmark claim.
    """

    metadata = {"name": "aurora_wildfire_v0", "render_modes": []}

    def __init__(self, scenario: Scenario, seed: int = 0) -> None:
        scenario.validate()
        self.scenario = scenario
        self.base_seed = int(seed)
        self.possible_agents = [f"responder_{index}" for index in range(scenario.num_agents)]
        self.agents: list[str] = []
        self._sim: FireSim | None = None
        self._responders: dict[str, AgentState] = {}
        self._step_count = 0
        self._previous_affected = 0
        rows, cols = self.scenario.shape
        observation_space = spaces.Dict(
            {
                "fire_state": spaces.MultiDiscrete(np.full((rows, cols), 4, dtype=np.int64)),
                "terrain": spaces.MultiDiscrete(np.full((rows, cols), 4, dtype=np.int64)),
                "position": spaces.MultiDiscrete(np.asarray([rows, cols], dtype=np.int64)),
                "water": spaces.Box(
                    low=np.asarray([0.0], dtype=np.float32),
                    high=np.asarray([self.scenario.water_capacity], dtype=np.float32),
                    dtype=np.float32,
                ),
                "step": spaces.Discrete(self.scenario.max_steps + 1),
            }
        )
        self._observation_spaces = {agent: observation_space for agent in self.possible_agents}
        self._action_spaces = {agent: spaces.Discrete(10) for agent in self.possible_agents}

    @property
    def sim(self) -> FireSim:
        if self._sim is None:
            raise RuntimeError("reset() must be called before accessing the simulator")
        return self._sim

    def observation_space(self, agent: str):
        try:
            return self._observation_spaces[agent]
        except KeyError as exc:
            raise KeyError(agent) from exc

    def action_space(self, agent: str):
        try:
            return self._action_spaces[agent]
        except KeyError as exc:
            raise KeyError(agent) from exc

    def reset(
        self, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[dict[str, dict[str, np.ndarray | int]], dict[str, dict[str, object]]]:
        del options
        episode_seed = self.base_seed if seed is None else int(seed)
        self._sim = FireSim(
            grid_size=self.scenario.shape,
            wind_direction=self.scenario.wind_direction,
            wind_intensity=self.scenario.wind_intensity,
            humidity=self.scenario.humidity,
            temperature=self.scenario.temperature,
            seed=episode_seed,
        )
        initial_grid = _initial_fire_grid(self.scenario, self._sim)
        if initial_grid is not None:
            self._sim.reset(initial_grid)
        responders = _initial_agents(self.scenario, self._sim)
        self._responders = {
            name: responder
            for name, responder in zip(self.possible_agents, responders, strict=True)
        }
        self.agents = self.possible_agents[:]
        self._step_count = 0
        self._previous_affected = self._sim.affected_area()
        observations = {agent: self._observe(agent) for agent in self.agents}
        infos = {agent: self._info(agent) for agent in self.agents}
        return observations, infos

    def step(self, actions: dict[str, int]):
        current_agents = self.agents[:]
        if not current_agents:
            raise RuntimeError("step() called after the episode ended; call reset()")
        missing = set(current_agents) - set(actions)
        extra = set(actions) - set(current_agents)
        if missing or extra:
            raise ValueError(f"actions must match active agents; missing={missing}, extra={extra}")
        snapshot = self.sim.fire_state.copy()
        for name in current_agents:
            _recharge(self._responders[name], self.sim, self.scenario.recharge_rate)

        movement_proposals: dict[str, tuple[int, int]] = {}
        suppression_proposals: dict[str, tuple[int, int]] = {}
        for name in current_agents:
            action = int(actions[name])
            if not self.action_space(name).contains(action):
                raise ValueError(f"invalid action {action} for {name}")
            responder = self._responders[name]
            delta = _ACTION_DELTAS[action]
            if delta is None:
                continue
            target = responder.row + delta[0], responder.col + delta[1]
            if action <= 4:
                if (
                    0 <= target[0] < self.scenario.shape[0]
                    and 0 <= target[1] < self.scenario.shape[1]
                    and self.sim.terrain[target] != 3
                ):
                    movement_proposals[name] = target
            elif (
                0 <= target[0] < self.scenario.shape[0]
                and 0 <= target[1] < self.scenario.shape[1]
                and snapshot[target] == BURNING
                and responder.water >= 1.0
            ):
                suppression_proposals[name] = target

        for name in current_agents:
            target = movement_proposals.get(name)
            if target is not None:
                responder = self._responders[name]
                if target != responder.position:
                    responder.row, responder.col = target
                    responder.distance_travelled += 1

        claimed: set[tuple[int, int]] = set()
        for name in current_agents:
            target = suppression_proposals.get(name)
            responder = self._responders[name]
            if target is None or target in claimed or responder.water < 1.0:
                continue
            if self.sim.suppress(*target):
                claimed.add(target)
                responder.water -= 1.0
                responder.water_spent += 1.0
                responder.suppressions += 1

        self.sim.step()
        self._step_count += 1
        affected = self.sim.affected_area()
        shared_reward = float(-(affected - self._previous_affected))
        self._previous_affected = affected
        terminated = not self.sim.is_fire_active()
        truncated = self._step_count >= self.scenario.max_steps and not terminated

        observations = {agent: self._observe(agent) for agent in current_agents}
        rewards = {agent: shared_reward for agent in current_agents}
        terminations = {agent: terminated for agent in current_agents}
        truncations = {agent: truncated for agent in current_agents}
        infos = {agent: self._info(agent) for agent in current_agents}
        if terminated or truncated:
            self.agents = []
        return observations, rewards, terminations, truncations, infos

    def _observe(self, agent: str) -> dict[str, np.ndarray | int]:
        responder = self._responders[agent]
        return {
            "fire_state": self.sim.fire_state.astype(np.int64, copy=True),
            "terrain": self.sim.terrain.astype(np.int64, copy=True),
            "position": np.asarray(responder.position, dtype=np.int64),
            "water": np.asarray([responder.water], dtype=np.float32),
            "step": self._step_count,
        }

    def _info(self, agent: str) -> dict[str, object]:
        responder = self._responders[agent]
        return {
            "affected_area": self.sim.affected_area(),
            "fire_active": self.sim.is_fire_active(),
            "suppressions": responder.suppressions,
            "distance_travelled": responder.distance_travelled,
        }

    def state(self) -> np.ndarray:
        """Return a compact global state for centralized-training workflows."""
        positions = np.asarray(
            [self._responders[name].position for name in self.possible_agents], dtype=np.float32
        ).reshape(-1)
        water = np.asarray(
            [self._responders[name].water for name in self.possible_agents], dtype=np.float32
        )
        return np.concatenate(
            [
                self.sim.fire_state.astype(np.float32, copy=False).reshape(-1),
                self.sim.terrain.astype(np.float32, copy=False).reshape(-1),
                positions,
                water,
                np.asarray([self._step_count], dtype=np.float32),
            ]
        )

    def render(self):
        return None

    def close(self) -> None:
        return None
