"""Interoperability validation for optional external interfaces."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from collections.abc import Iterable
from pathlib import Path

from .adapters.pettingzoo import WildfireParallelEnv
from .coordination import _initial_fire_grid
from .scenarios import REFERENCE_SCENARIOS
from .simulator import FireSim
from .types import Scenario


def _digest(sim: FireSim) -> str:
    return hashlib.sha256(
        sim.fire_state.tobytes() + sim.fuel_density.tobytes() + sim._burn_age.tobytes()
    ).hexdigest()


def _direct_sim(scenario: Scenario, seed: int) -> FireSim:
    sim = FireSim(
        grid_size=scenario.shape,
        wind_direction=scenario.wind_direction,
        wind_intensity=scenario.wind_intensity,
        humidity=scenario.humidity,
        temperature=scenario.temperature,
        seed=seed,
    )
    initial = _initial_fire_grid(scenario, sim)
    if initial is not None:
        sim.reset(initial)
    return sim


def run_interface_case_study(
    output_dir: str | Path,
    *,
    scenarios: Iterable[Scenario] = REFERENCE_SCENARIOS,
    seeds: Iterable[int] = range(20),
) -> dict[str, object]:
    """Compare no-op PettingZoo trajectories with the direct simulation engine."""
    scenario_list = list(scenarios)
    seed_list = [int(seed) for seed in seeds]
    if not scenario_list or not seed_list:
        raise ValueError("interface study requires scenarios and seeds")
    rows: list[dict[str, object]] = []
    for scenario in scenario_list:
        scenario.validate()
        for seed in seed_list:
            direct = _direct_sim(scenario, seed)
            env = WildfireParallelEnv(scenario, seed=seed)
            env.reset(seed=seed)
            per_step_match = True
            steps = 0
            while steps < scenario.max_steps and direct.is_fire_active():
                direct.step()
                env.step({agent: 0 for agent in env.agents})
                steps += 1
                if _digest(direct) != _digest(env.sim):
                    per_step_match = False
                    break
                if not env.agents:
                    break
            rows.append(
                {
                    "scenario": scenario.name,
                    "seed": seed,
                    "steps": steps,
                    "per_step_exact_match": per_step_match,
                    "final_digest_match": _digest(direct) == _digest(env.sim),
                    "affected_area_match": direct.affected_area() == env.sim.affected_area(),
                }
            )
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="", dir=destination, delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(handle.name)
    os.replace(temporary, destination / "interface_cases.csv")
    total = len(rows)
    summary = {
        "study_version": "1.0",
        "num_scenarios": len(scenario_list),
        "num_seeds": len(seed_list),
        "num_cases": total,
        "per_step_exact_matches": sum(bool(row["per_step_exact_match"]) for row in rows),
        "final_digest_matches": sum(bool(row["final_digest_match"]) for row in rows),
        "affected_area_matches": sum(bool(row["affected_area_match"]) for row in rows),
        "interpretation": (
            "Stay actions through the PettingZoo ParallelEnv leave fire dynamics unchanged; "
            "the adapter and direct engine are compared after every transition."
        ),
    }
    (destination / "interface_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary
