from __future__ import annotations

import numpy as np
import pytest
from pettingzoo.test import parallel_api_test

from aurora.adapters.pettingzoo import WildfireParallelEnv
from aurora.scenarios import REFERENCE_SCENARIOS


def test_pettingzoo_parallel_api_contract():
    scenario = REFERENCE_SCENARIOS[0]
    env = WildfireParallelEnv(scenario, seed=3)
    parallel_api_test(env, num_cycles=40)


def test_pettingzoo_reset_and_actions_are_deterministic():
    scenario = REFERENCE_SCENARIOS[1]
    actions = []
    for step in range(12):
        actions.append(
            {f"responder_{index}": (step + index) % 10 for index in range(scenario.num_agents)}
        )

    def run_once():
        env = WildfireParallelEnv(scenario, seed=19)
        observations, _ = env.reset(seed=19)
        trajectory = [observations["responder_0"]["fire_state"].tobytes()]
        for action in actions:
            if not env.agents:
                break
            observations, rewards, terminations, truncations, infos = env.step(action)
            trajectory.append(observations["responder_0"]["fire_state"].tobytes())
            assert set(rewards) == set(action)
            assert set(terminations) == set(action)
            assert set(truncations) == set(action)
            assert set(infos) == set(action)
        return trajectory, env.state().copy()

    first_trajectory, first_state = run_once()
    second_trajectory, second_state = run_once()
    assert first_trajectory == second_trajectory
    assert np.array_equal(first_state, second_state)


def test_pettingzoo_rejects_missing_or_invalid_actions():
    env = WildfireParallelEnv(REFERENCE_SCENARIOS[0], seed=1)
    env.reset()
    with pytest.raises(ValueError, match="actions must match"):
        env.step({env.agents[0]: 0})
    with pytest.raises(ValueError, match="invalid action"):
        env.step({agent: 99 for agent in env.agents})


def test_pettingzoo_requires_reset_and_rejects_post_terminal_step():
    scenario = REFERENCE_SCENARIOS[0]
    env = WildfireParallelEnv(scenario)
    with pytest.raises(RuntimeError, match="reset"):
        _ = env.sim
    observations, _ = env.reset()
    assert set(observations) == set(env.possible_agents)
    for _ in range(scenario.max_steps + 1):
        if not env.agents:
            break
        env.step({agent: 0 for agent in env.agents})
    assert env.agents == []
    with pytest.raises(RuntimeError, match="after the episode ended"):
        env.step({})


def test_adapter_lazy_export_and_unknown_attribute():
    import aurora.adapters as adapters

    assert adapters.WildfireParallelEnv is WildfireParallelEnv
    with pytest.raises(AttributeError):
        adapters.__getattr__("NotAnAdapter")


def test_adapter_spaces_and_state_shape():
    scenario = REFERENCE_SCENARIOS[0]
    env = WildfireParallelEnv(scenario, seed=8)
    env.reset()
    agent = env.agents[0]
    assert env.observation_space(agent).contains(env._observe(agent))
    assert env.action_space(agent).contains(0)
    expected = 2 * scenario.shape[0] * scenario.shape[1] + 3 * scenario.num_agents + 1
    assert env.state().shape == (expected,)
    with pytest.raises(KeyError):
        env.observation_space("missing")
    with pytest.raises(KeyError):
        env.action_space("missing")
    assert env.render() is None
    assert env.close() is None


def test_adapter_movement_and_suppression_update_metrics():
    scenario = REFERENCE_SCENARIOS[0]
    env = WildfireParallelEnv(scenario, seed=2)
    env.reset(seed=2)
    agent = env.agents[0]
    responder = env._responders[agent]
    before = responder.position
    # Select the first traversable neighboring move, if one exists.
    action_for_delta = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}
    chosen = 0
    for action, delta in action_for_delta.items():
        target = before[0] + delta[0], before[1] + delta[1]
        if (
            0 <= target[0] < scenario.shape[0]
            and 0 <= target[1] < scenario.shape[1]
            and env.sim.terrain[target] != 3
        ):
            chosen = action
            break
    env.step({name: (chosen if name == agent else 0) for name in env.agents})
    if chosen:
        assert responder.distance_travelled == 1

    # Force a burning cell at the responder and verify simultaneous suppression accounting.
    if not env.agents:
        env.reset(seed=2)
        agent = env.agents[0]
        responder = env._responders[agent]
    env.sim.fire_state[responder.position] = 1
    water_before = responder.water
    observations, rewards, _, _, infos = env.step(
        {name: (5 if name == agent else 0) for name in env.agents}
    )
    assert observations[agent]["step"] >= 1
    assert rewards[agent] <= 0
    assert infos[agent]["suppressions"] == 1
    assert responder.water == water_before - 1.0
