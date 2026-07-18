"""Matched-scenario benchmark generation and transparent descriptive statistics."""

from __future__ import annotations

import csv
import json
import math
import os
import tempfile
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from statistics import mean, median, stdev

import numpy as np

from .coordination import run_episode
from .scenarios import REFERENCE_SCENARIOS
from .types import Scenario

METHODS = ("no_response", "reactive", "coordinated")
RESPONSE_METHODS = ("reactive", "coordinated")
METRICS = (
    "affected_area",
    "burned_area",
    "suppressed_area",
    "final_burning",
    "steps",
    "suppressions",
    "water_used",
    "distance_travelled",
)


def _stabilize(obj: object) -> object:
    """Round every float in a nested summary structure to a fixed precision.

    Descriptive statistics such as ``statistics.stdev`` differ in the last unit
    in the last place across CPython minor versions and BLAS builds. Those bits
    carry no scientific meaning but would otherwise make the serialized summary
    non-reproducible across the supported Python 3.10-3.13 range, breaking the
    artifact's byte-exact hash contract. Rounding to nine decimals removes the
    noise while preserving every reported value far beyond claim precision.
    """
    if isinstance(obj, float):
        return round(obj, 9)
    if isinstance(obj, dict):
        return {key: _stabilize(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_stabilize(value) for value in obj]
    if isinstance(obj, tuple):
        return [_stabilize(value) for value in obj]
    return obj


def _summary(values: list[float]) -> dict[str, float | int]:
    if not values:
        raise ValueError("summary requires at least one value")
    array = np.asarray(values, dtype=float)
    q25, q75 = np.quantile(array, [0.25, 0.75])
    return {
        "n": len(values),
        "mean": float(mean(values)),
        "std": float(stdev(values)) if len(values) > 1 else 0.0,
        "median": float(median(values)),
        "q25": float(q25),
        "q75": float(q75),
        "min": float(array.min()),
        "max": float(array.max()),
    }


def _wilson_interval(
    successes: int, total: int, z: float = 1.959963984540054
) -> tuple[float, float]:
    if total <= 0:
        raise ValueError("Wilson interval requires a positive total")
    proportion = successes / total
    denominator = 1.0 + (z * z / total)
    center = (proportion + z * z / (2.0 * total)) / denominator
    half_width = (
        z
        * math.sqrt((proportion * (1.0 - proportion) / total) + (z * z / (4.0 * total * total)))
        / denominator
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def _hierarchical_paired_ci(
    by_scenario: dict[str, list[float]], seed: int = 20260710, draws: int = 5000
) -> tuple[float, float]:
    """Bootstrap scenario families, then paired seed-level differences within each family."""
    if not by_scenario or draws <= 0:
        raise ValueError("hierarchical bootstrap requires data and positive draws")
    scenario_names = sorted(by_scenario)
    rng = np.random.default_rng(seed)
    samples = np.empty(draws, dtype=float)
    for draw in range(draws):
        sampled_names = rng.choice(scenario_names, size=len(scenario_names), replace=True)
        values: list[float] = []
        for name in sampled_names:
            group = np.asarray(by_scenario[str(name)], dtype=float)
            values.extend(rng.choice(group, size=len(group), replace=True).tolist())
        samples[draw] = float(np.mean(values))
    low, high = np.quantile(samples, [0.025, 0.975])
    return float(low), float(high)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _validate_inputs(
    seeds: Iterable[int], scenarios: Iterable[Scenario]
) -> tuple[list[int], list[Scenario]]:
    seed_list = [int(seed) for seed in seeds]
    scenario_list = list(scenarios)
    if not seed_list:
        raise ValueError("at least one seed is required")
    if len(set(seed_list)) != len(seed_list):
        raise ValueError("seeds must be unique")
    if not scenario_list:
        raise ValueError("at least one scenario is required")
    for scenario in scenario_list:
        scenario.validate()
    names = [scenario.name for scenario in scenario_list]
    if len(set(names)) != len(names):
        raise ValueError("scenario names must be unique")
    return seed_list, scenario_list


def run_reference_benchmark(
    output_dir: str | Path,
    seeds: Iterable[int] = range(20),
    scenarios: Iterable[Scenario] = REFERENCE_SCENARIOS,
    *,
    bootstrap_seed: int = 20260710,
    bootstrap_draws: int = 5000,
) -> dict[str, object]:
    """Run no-response, reactive, and coordinated methods on matched cases."""
    seed_list, scenario_list = _validate_inputs(seeds, scenarios)
    if bootstrap_draws <= 0:
        raise ValueError("bootstrap_draws must be positive")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for scenario in scenario_list:
        for seed in seed_list:
            for method in METHODS:
                rows.append(run_episode(method, scenario, seed).to_dict())

    fieldnames = list(rows[0])
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="", dir=destination, delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        raw_temporary = Path(handle.name)
    os.replace(raw_temporary, destination / "reference_benchmark.csv")

    by_method: dict[str, list[dict[str, object]]] = defaultdict(list)
    by_scenario_method: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        method = str(row["method"])
        scenario_name = str(row["scenario"])
        by_method[method].append(row)
        by_scenario_method[(scenario_name, method)].append(row)

    summary: dict[str, object] = {
        "benchmark_version": "3.0",
        "analysis_unit": "matched scenario-seed case",
        "bootstrap_unit": "scenario family, then paired seed within family",
        "bootstrap_draws": int(bootstrap_draws),
        "bootstrap_seed": int(bootstrap_seed),
        "num_seeds": len(seed_list),
        "num_scenarios": len(scenario_list),
        "num_cases": len(seed_list) * len(scenario_list),
        "num_episodes_per_method": len(seed_list) * len(scenario_list),
        "total_episodes": len(METHODS) * len(seed_list) * len(scenario_list),
        "scenario_names": [scenario.name for scenario in scenario_list],
        "methods": {},
        "scenarios": {},
        "response_vs_no_response": {},
        "paired_response_comparison": {},
        "interpretation": (
            "The no-response baseline distinguishes response benefit from natural fire burnout. "
            "This remains an abstract software-validation benchmark, not physical validation or "
            "evidence of superiority over learned controllers."
        ),
    }

    for method in METHODS:
        method_rows = by_method[method]
        inactive = sum(bool(row["fire_inactive"]) for row in method_rows)
        low, high = _wilson_interval(inactive, len(method_rows))
        summary["methods"][method] = {
            metric: _summary([float(row[metric]) for row in method_rows]) for metric in METRICS
        }
        summary["methods"][method]["fire_inactive_at_end"] = {
            "count": inactive,
            "n": len(method_rows),
            "rate": inactive / len(method_rows),
            "wilson_95_ci": [low, high],
            "diagnostic_only": True,
        }

    indexed = {(str(row["scenario"]), int(row["seed"]), str(row["method"])): row for row in rows}
    pair_keys = [(scenario.name, seed) for scenario in scenario_list for seed in seed_list]

    for scenario in scenario_list:
        scenario_payload: dict[str, object] = {}
        for method in METHODS:
            scenario_rows = by_scenario_method[(scenario.name, method)]
            scenario_payload[method] = {
                metric: _summary([float(row[metric]) for row in scenario_rows])
                for metric in METRICS
            }
        summary["scenarios"][scenario.name] = scenario_payload

    for method in RESPONSE_METHODS:
        reductions_by_scenario: dict[str, list[float]] = defaultdict(list)
        reductions: list[float] = []
        for scenario_name, seed in pair_keys:
            reduction = float(
                indexed[(scenario_name, seed, "no_response")]["affected_area"]
            ) - float(indexed[(scenario_name, seed, method)]["affected_area"])
            reductions_by_scenario[scenario_name].append(reduction)
            reductions.append(reduction)
        low, high = _hierarchical_paired_ci(
            reductions_by_scenario, seed=bootstrap_seed, draws=bootstrap_draws
        )
        summary["response_vs_no_response"][method] = {
            "avoided_affected_cells": _summary(reductions),
            "hierarchical_paired_bootstrap_95_ci_of_mean": [low, high],
            "n_pairs": len(reductions),
            "fraction_of_cases_with_reduction": sum(value > 0 for value in reductions)
            / len(reductions),
            "scenario_mean_reductions": {
                name: float(mean(values)) for name, values in sorted(reductions_by_scenario.items())
            },
        }

    for metric in METRICS:
        differences_by_scenario: dict[str, list[float]] = defaultdict(list)
        differences: list[float] = []
        for scenario_name, seed in pair_keys:
            difference = float(indexed[(scenario_name, seed, "coordinated")][metric]) - float(
                indexed[(scenario_name, seed, "reactive")][metric]
            )
            differences_by_scenario[scenario_name].append(difference)
            differences.append(difference)
        low, high = _hierarchical_paired_ci(
            differences_by_scenario, seed=bootstrap_seed, draws=bootstrap_draws
        )
        summary["paired_response_comparison"][metric] = {
            "coordinated_minus_reactive": _summary(differences),
            "hierarchical_paired_bootstrap_95_ci_of_mean": [low, high],
            "n_pairs": len(differences),
            "scenario_mean_differences": {
                name: float(mean(values))
                for name, values in sorted(differences_by_scenario.items())
            },
        }

    summary = _stabilize(summary)
    _atomic_write_text(
        destination / "reference_benchmark_summary.json",
        json.dumps(summary, indent=2, allow_nan=False) + "\n",
    )
    return summary
