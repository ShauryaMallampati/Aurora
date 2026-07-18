"""Run a short deterministic episode through the optional PettingZoo adapter."""

from aurora.adapters.pettingzoo import WildfireParallelEnv
from aurora.scenarios import REFERENCE_SCENARIOS

env = WildfireParallelEnv(REFERENCE_SCENARIOS[1], seed=7)
observations, infos = env.reset(seed=7)
for _ in range(12):
    if not env.agents:
        break
    # Stay in place; this example demonstrates interface mechanics rather than a policy.
    observations, rewards, terminations, truncations, infos = env.step(
        {agent: 0 for agent in env.agents}
    )
print({"steps": env._step_count, "affected_area": env.sim.affected_area()})
