"""Self-validation routines with explicit PASS/FAIL outcomes."""

from __future__ import annotations

import json
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .coordination import run_episode_with_trace, verify_trace
from .simulator import BURNED, BURNING, SUPPRESSED, FireSim
from .types import Scenario


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def validate_core(output_path: str | Path | None = None) -> dict[str, object]:
    checks: list[CheckResult] = []

    def run_check(name: str, operation) -> None:
        try:
            detail = operation()
            checks.append(CheckResult(name, "PASS", str(detail)))
        except Exception as exc:  # pragma: no cover - defensive boundary
            checks.append(CheckResult(name, "FAIL", f"{type(exc).__name__}: {exc}"))

    scenario = Scenario(name="validation", grid_size=(16, 20), max_steps=20)

    def deterministic_replay() -> str:
        first = run_episode_with_trace("coordinated", scenario, seed=11)
        second = run_episode_with_trace("coordinated", scenario, seed=11)
        if first.sha256() != second.sha256() or not verify_trace(first):
            raise AssertionError("seeded trajectory digests differed")
        return first.sha256()

    def reset_integrity() -> str:
        sim = FireSim(grid_size=(12, 14), seed=4)
        initial_fuel = sim.fuel_density.copy()
        initial_state = sim.fire_state.copy()
        for _ in range(5):
            sim.step()
        sim.reset()
        if not np.array_equal(sim.fire_state, initial_state):
            raise AssertionError("reset did not restore initial fire state")
        if not np.array_equal(sim.fuel_density, initial_fuel):
            raise AssertionError("reset did not restore fuel")
        return "fire and fuel reset; transition randomness is counter-based"

    def state_semantics() -> str:
        sim = FireSim(grid_size=12, seed=2)
        row, col = map(int, np.argwhere(sim.fire_state == BURNING)[0])
        if not sim.suppress(row, col):
            raise AssertionError("suppression failed")
        if sim.fire_state[row, col] != SUPPRESSED:
            raise AssertionError("suppression was not represented separately")
        if np.count_nonzero(sim.fire_state == BURNED) != 0:
            raise AssertionError("suppression was counted as natural burn")
        return "burning, burned, and suppressed states are distinct"

    run_check("deterministic_trace_replay", deterministic_replay)
    run_check("reset_integrity", reset_integrity)
    run_check("state_semantics", state_semantics)
    checks.append(CheckResult("numpy_available", "PASS", f"NumPy {np.__version__}"))
    checks.append(CheckResult("python_version", "PASS", platform.python_version()))
    status = "PASS" if checks and all(check.status == "PASS" for check in checks) else "FAIL"
    report = {
        "status": status,
        "python": sys.version,
        "platform": platform.platform(),
        "checks": [asdict(check) for check in checks],
    }
    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
