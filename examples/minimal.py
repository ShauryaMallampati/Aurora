from aurora.coordination import run_episode
from aurora.scenarios import REFERENCE_SCENARIOS

result = run_episode("coordinated", REFERENCE_SCENARIOS[0], seed=7)
print(result.to_dict())
