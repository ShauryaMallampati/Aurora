"""Controlled fault-injection experiments for reproducibility research.

The variants in this module are intentionally incorrect and exist only to
measure how common implementation shortcuts can bias multi-agent simulation
experiments. Production episodes continue to use :mod:`aurora.coordination`.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

import numpy as np

from .coordination import (
    EpisodeResult,
    _initial_agents,
    _initial_fire_grid,
    _move,
    _reactive_target,
    _recharge,
    _suppression_candidate,
    run_episode,
)
from .scenarios import REFERENCE_SCENARIOS
from .simulator import BURNING, FireSim
from .types import AgentState, Scenario


@dataclass(frozen=True)
class FaultCase:
    """One matched scenario-seed outcome from the controlled fault study."""

    scenario: str
    seed: int
    keyed_rng_diverged: bool
    shared_rng_diverged: bool
    sequential_observation_diverged: bool
    correct_reset_diverged: bool
    incomplete_reset_diverged: bool
    reactive_burned_correct: int
    reactive_burned_conflated: int
    coordinated_burned_correct: int
    coordinated_burned_conflated: int
    reactive_benefit_sign_changed: bool
    coordinated_benefit_sign_changed: bool
    response_ranking_changed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class _SharedRNGFireSim(FireSim):
    """Intentionally flawed simulator that consumes a call-order RNG stream."""

    def __init__(self, *args, **kwargs) -> None:
        seed = int(kwargs.get("seed", 42))
        self._shared_rng = np.random.default_rng(seed)
        super().__init__(*args, **kwargs)

    def _transition_uniform(
        self, source: tuple[int, int], target: tuple[int, int], attempt_age: int = 1
    ) -> float:
        del source, target, attempt_age
        return float(self._shared_rng.random())

    def consume_policy_draws(self, count: int) -> None:
        if count > 0:
            self._shared_rng.random(count)


def _build_sim(scenario: Scenario, seed: int, cls: type[FireSim] = FireSim) -> FireSim:
    sim = cls(
        grid_size=scenario.shape,
        wind_direction=scenario.wind_direction,
        wind_intensity=scenario.wind_intensity,
        humidity=scenario.humidity,
        temperature=scenario.temperature,
        seed=seed,
    )
    initial_grid = _initial_fire_grid(scenario, sim)
    if initial_grid is not None:
        sim.reset(initial_grid)
    return sim


def _state_digest(sim: FireSim) -> str:
    payload = b"|".join(
        (
            sim.fire_state.tobytes(),
            sim.fuel_density.tobytes(),
            sim._burn_age.tobytes(),  # diagnostic intentionally checks hidden state
            sim._ever_ignited.tobytes(),
        )
    )
    return hashlib.sha256(payload).hexdigest()


def _run_no_response_with_noise(
    scenario: Scenario,
    seed: int,
    *,
    shared_environment_rng: bool,
    policy_draws_per_step: int,
) -> str:
    sim_cls = _SharedRNGFireSim if shared_environment_rng else FireSim
    sim = _build_sim(scenario, seed, sim_cls)
    policy_rng = np.random.default_rng(seed + 1_000_003)
    for _ in range(scenario.max_steps):
        if not sim.is_fire_active():
            break
        if shared_environment_rng:
            assert isinstance(sim, _SharedRNGFireSim)
            sim.consume_policy_draws(policy_draws_per_step)
        elif policy_draws_per_step:
            # Correct design: policy-local randomness cannot shift environmental draws.
            policy_rng.random(policy_draws_per_step)
        sim.step()
    return _state_digest(sim)


def _result_from_state(
    method: str,
    scenario: Scenario,
    seed: int,
    sim: FireSim,
    agents: list[AgentState],
    steps: int,
) -> EpisodeResult:
    counts = sim.state_counts()
    return EpisodeResult(
        method=method,
        scenario=scenario.name,
        seed=seed,
        fire_inactive=not sim.is_fire_active(),
        steps=steps,
        initial_burning=0,
        final_burning=counts["burning"],
        burned_area=counts["burned"],
        suppressed_area=counts["suppressed"],
        affected_area=counts["affected"],
        suppressions=sum(agent.suppressions for agent in agents),
        water_used=float(sum(agent.water_spent for agent in agents)),
        distance_travelled=sum(agent.distance_travelled for agent in agents),
        strategy_updates=0,
    )


def _run_reactive_observation_variant(
    scenario: Scenario, seed: int, *, sequential_observation: bool
) -> tuple[EpisodeResult, str]:
    """Run reactive dispatch with correct snapshots or a flawed mutable view."""
    sim = _build_sim(scenario, seed)
    agents = _initial_agents(scenario, sim)
    initial_burning = int(np.count_nonzero(sim.fire_state == BURNING))
    steps_run = 0

    for step in range(scenario.max_steps):
        if not sim.is_fire_active():
            break
        steps_run = step + 1
        for agent in agents:
            _recharge(agent, sim, scenario.recharge_rate)

        if sequential_observation:
            # Intentionally incorrect: each agent observes and mutates live state.
            reserved: set[tuple[int, int]] = set()
            for agent in agents:
                live = sim.fire_state
                immediate = _suppression_candidate(live, agent)
                if immediate is not None and agent.water >= 1.0 and sim.suppress(*immediate):
                    agent.water -= 1.0
                    agent.water_spent += 1.0
                    agent.suppressions += 1
                    reserved.add(immediate)
                    continue
                target = _reactive_target(live, agent, reserved)
                if target is not None:
                    reserved.add(target)
                    _move(agent, target, sim)
                immediate = _suppression_candidate(sim.fire_state, agent)
                if immediate is not None and agent.water >= 1.0 and sim.suppress(*immediate):
                    agent.water -= 1.0
                    agent.water_spent += 1.0
                    agent.suppressions += 1
                    reserved.add(immediate)
        else:
            snapshot = sim.fire_state.copy()
            reserved_targets: set[tuple[int, int]] = set()
            proposals: dict[int, tuple[int, int]] = {}
            for agent in agents:
                immediate = _suppression_candidate(snapshot, agent)
                if immediate is not None:
                    proposals[agent.agent_id] = immediate
                    reserved_targets.add(immediate)
                    continue
                target = _reactive_target(snapshot, agent, reserved_targets)
                if target is not None:
                    reserved_targets.add(target)
                    _move(agent, target, sim)
            for agent in agents:
                if agent.agent_id not in proposals:
                    candidate = _suppression_candidate(snapshot, agent)
                    if candidate is not None:
                        proposals[agent.agent_id] = candidate
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

    result = _result_from_state("reactive", scenario, seed, sim, agents, steps_run)
    result = EpisodeResult(**{**result.to_dict(), "initial_burning": initial_burning})
    return result, _state_digest(sim)


def sequential_observation_microcase() -> dict[str, int]:
    """Return a minimal example in which live-state observation changes semantics."""
    fire = np.zeros((8, 8), dtype=np.uint8)
    fire[3, 3] = BURNING
    fire[4, 4] = BURNING
    agents = [
        AgentState(0, 3, 2, 2.0, 2.0),
        AgentState(1, 3, 4, 2.0, 2.0),
    ]

    proposals = [_suppression_candidate(fire.copy(), agent) for agent in agents]
    synchronous = len({proposal for proposal in proposals if proposal is not None})

    mutable = fire.copy()
    sequential = 0
    for agent in agents:
        target = _suppression_candidate(mutable, agent)
        if target is not None:
            mutable[target] = 3
            sequential += 1
    return {"synchronous_unique_suppressions": synchronous, "sequential_suppressions": sequential}


def run_information_leakage_stress_cases(
    num_cases: int = 1000, seed: int = 20260711
) -> dict[str, object]:
    """Exercise adversarial two-agent states designed to expose live-state leakage.

    Each case contains a shared burning cell reachable by both responders and an
    alternate burning cell reachable only by the second responder. Under
    synchronous planning both agents choose from the same snapshot, while the
    intentionally flawed sequential variant lets the second responder react to
    the first responder's suppression.
    """
    if num_cases <= 0:
        raise ValueError("num_cases must be positive")
    rng = np.random.default_rng(seed)
    divergent = 0
    extra_suppressions: list[int] = []
    for _ in range(num_cases):
        fire = np.zeros((10, 10), dtype=np.uint8)
        row = int(rng.integers(1, 8))
        col = int(rng.integers(2, 7))
        shared = (row, col)
        alternate = (row + 1, col + 1)
        fire[shared] = BURNING
        fire[alternate] = BURNING
        # Add harmless distractors to vary the state while preserving the trap.
        for _ in range(int(rng.integers(0, 4))):
            point = (int(rng.integers(0, 10)), int(rng.integers(0, 10)))
            agent_positions = ((row, col - 1), (row, col + 1))
            if point not in {shared, alternate, *agent_positions} and all(
                abs(point[0] - ar) + abs(point[1] - ac) > 1 for ar, ac in agent_positions
            ):
                fire[point] = BURNING
        agents = [
            AgentState(0, row, col - 1, 2.0, 2.0),
            AgentState(1, row, col + 1, 2.0, 2.0),
        ]

        snapshot = fire.copy()
        proposals = [_suppression_candidate(snapshot, agent) for agent in agents]
        claimed: set[tuple[int, int]] = set()
        for target in proposals:
            if target is not None and target not in claimed:
                claimed.add(target)
        synchronous_count = len(claimed)

        mutable = fire.copy()
        sequential_targets: set[tuple[int, int]] = set()
        for agent in agents:
            target = _suppression_candidate(mutable, agent)
            if target is not None:
                mutable[target] = 3
                sequential_targets.add(target)
        sequential_count = len(sequential_targets)
        delta = sequential_count - synchronous_count
        extra_suppressions.append(delta)
        if claimed != sequential_targets:
            divergent += 1

    return {
        "count": divergent,
        "n": num_cases,
        "rate": divergent / num_cases,
        "wilson_95_ci": _wilson(divergent, num_cases),
        "mean_extra_suppressions_in_flawed_variant": float(mean(extra_suppressions)),
        "construction": (
            "Adversarial two-agent states with one shared target and one alternate "
            "target visible only after the first live-state mutation."
        ),
    }


def _initial_state_for_reset(scenario: Scenario, seed: int) -> tuple[FireSim, np.ndarray]:
    sim = _build_sim(scenario, seed)
    return sim, sim.fire_state.copy()


def _advance(sim: FireSim, steps: int) -> None:
    for _ in range(steps):
        if not sim.is_fire_active():
            break
        sim.step()


def _reset_divergence(scenario: Scenario, seed: int, *, incomplete: bool) -> bool:
    sim, initial = _initial_state_for_reset(scenario, seed)
    steps = min(12, scenario.max_steps)
    _advance(sim, steps)
    if incomplete:
        # Intentionally incorrect reset: fuel depletion is retained.
        sim.step_count = 0
        sim.fire_state.fill(0)
        sim._burn_age.fill(0)
        sim._ever_ignited.fill(False)
        sim.fire_state[...] = initial
        sim._ever_ignited[initial != 0] = True
    else:
        sim.reset(initial)
    _advance(sim, steps)

    fresh, fresh_initial = _initial_state_for_reset(scenario, seed)
    fresh.reset(fresh_initial)
    _advance(fresh, steps)
    return _state_digest(sim) != _state_digest(fresh)


def _sign(value: float) -> int:
    return 1 if value > 0 else (-1 if value < 0 else 0)


def _wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if total <= 0:
        raise ValueError("total must be positive")
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * np.sqrt((p * (1 - p) / total) + z * z / (4 * total * total)) / denominator
    return [float(max(0.0, center - half)), float(min(1.0, center + half))]


def _cluster_bootstrap_mean_ci(
    values_by_scenario: dict[str, list[float]], *, seed: int, draws: int
) -> list[float]:
    names = sorted(values_by_scenario)
    rng = np.random.default_rng(seed)
    samples = np.empty(draws, dtype=float)
    for index in range(draws):
        sampled = rng.choice(names, len(names), replace=True)
        scenario_means = [mean(values_by_scenario[str(name)]) for name in sampled]
        samples[index] = float(mean(scenario_means))
    low, high = np.quantile(samples, [0.025, 0.975])
    return [float(low), float(high)]


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def run_fault_ablation(
    output_dir: str | Path,
    *,
    scenarios: Iterable[Scenario] = REFERENCE_SCENARIOS,
    seeds: Iterable[int] = range(40),
    bootstrap_seed: int = 20260711,
    bootstrap_draws: int = 5000,
) -> dict[str, object]:
    """Run controlled faults and write a case CSV plus summary JSON.

    The study is deterministic. It does not assert that every external simulator
    contains these bugs; it measures their consequences when intentionally
    introduced into the same workload.
    """
    scenario_list = list(scenarios)
    seed_list = [int(seed) for seed in seeds]
    if not scenario_list or not seed_list:
        raise ValueError("fault ablation requires scenarios and seeds")
    if len({scenario.name for scenario in scenario_list}) != len(scenario_list):
        raise ValueError("scenario names must be unique")
    if len(set(seed_list)) != len(seed_list):
        raise ValueError("seeds must be unique")
    if bootstrap_draws <= 0:
        raise ValueError("bootstrap_draws must be positive")

    cases: list[FaultCase] = []
    bias_by_scenario: dict[str, list[float]] = defaultdict(list)

    for scenario in scenario_list:
        scenario.validate()
        for seed in seed_list:
            keyed_base = _run_no_response_with_noise(
                scenario, seed, shared_environment_rng=False, policy_draws_per_step=0
            )
            keyed_noop = _run_no_response_with_noise(
                scenario, seed, shared_environment_rng=False, policy_draws_per_step=1
            )
            shared_base = _run_no_response_with_noise(
                scenario, seed, shared_environment_rng=True, policy_draws_per_step=0
            )
            shared_noop = _run_no_response_with_noise(
                scenario, seed, shared_environment_rng=True, policy_draws_per_step=1
            )

            correct_reactive, correct_digest = _run_reactive_observation_variant(
                scenario, seed, sequential_observation=False
            )
            flawed_reactive, flawed_digest = _run_reactive_observation_variant(
                scenario, seed, sequential_observation=True
            )

            no_response = run_episode("no_response", scenario, seed)
            reactive = run_episode("reactive", scenario, seed)
            coordinated = run_episode("coordinated", scenario, seed)

            reactive_correct_benefit = no_response.burned_area - reactive.burned_area
            reactive_faulty_benefit = no_response.burned_area - (
                reactive.burned_area + reactive.suppressed_area
            )
            coordinated_correct_benefit = no_response.burned_area - coordinated.burned_area
            coordinated_faulty_benefit = no_response.burned_area - (
                coordinated.burned_area + coordinated.suppressed_area
            )
            correct_ranking = _sign(coordinated.burned_area - reactive.burned_area)
            conflated_ranking = _sign(
                (coordinated.burned_area + coordinated.suppressed_area)
                - (reactive.burned_area + reactive.suppressed_area)
            )
            bias_by_scenario[scenario.name].append(
                float((reactive.suppressed_area + coordinated.suppressed_area) / 2.0)
            )

            cases.append(
                FaultCase(
                    scenario=scenario.name,
                    seed=seed,
                    keyed_rng_diverged=keyed_base != keyed_noop,
                    shared_rng_diverged=shared_base != shared_noop,
                    sequential_observation_diverged=(
                        correct_digest != flawed_digest
                        or correct_reactive.to_dict() != flawed_reactive.to_dict()
                    ),
                    correct_reset_diverged=_reset_divergence(scenario, seed, incomplete=False),
                    incomplete_reset_diverged=_reset_divergence(scenario, seed, incomplete=True),
                    reactive_burned_correct=reactive.burned_area,
                    reactive_burned_conflated=reactive.burned_area + reactive.suppressed_area,
                    coordinated_burned_correct=coordinated.burned_area,
                    coordinated_burned_conflated=(
                        coordinated.burned_area + coordinated.suppressed_area
                    ),
                    reactive_benefit_sign_changed=(
                        _sign(reactive_correct_benefit) != _sign(reactive_faulty_benefit)
                    ),
                    coordinated_benefit_sign_changed=(
                        _sign(coordinated_correct_benefit) != _sign(coordinated_faulty_benefit)
                    ),
                    response_ranking_changed=correct_ranking != conflated_ranking,
                )
            )

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    csv_path = destination / "fault_ablation_cases.csv"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="", dir=destination, delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cases[0].to_dict()))
        writer.writeheader()
        writer.writerows(case.to_dict() for case in cases)
        temporary = Path(handle.name)
    os.replace(temporary, csv_path)

    total = len(cases)

    def proportion(field: str) -> dict[str, object]:
        count = sum(bool(getattr(case, field)) for case in cases)
        return {
            "count": count,
            "n": total,
            "rate": count / total,
            "wilson_95_ci": _wilson(count, total),
        }

    all_biases = [value for values in bias_by_scenario.values() for value in values]
    summary: dict[str, object] = {
        "study_version": "1.0",
        "purpose": (
            "Controlled fault injection within the same workloads; not a prevalence claim "
            "about external software."
        ),
        "num_scenarios": len(scenario_list),
        "num_seeds": len(seed_list),
        "num_matched_cases": total,
        "scenario_names": [scenario.name for scenario in scenario_list],
        "microcase": sequential_observation_microcase(),
        "random_stream_drift": {
            "keyed_environment_rng_with_policy_noop": proportion("keyed_rng_diverged"),
            "shared_global_rng_with_policy_noop": proportion("shared_rng_diverged"),
        },
        "within_step_information_leakage": {
            "reference_benchmark_cases": proportion("sequential_observation_diverged"),
            "adversarial_microstates": run_information_leakage_stress_cases(),
        },
        "reset_contamination": {
            "complete_reset": proportion("correct_reset_diverged"),
            "incomplete_reset": proportion("incomplete_reset_diverged"),
        },
        "state_conflation": {
            "mean_overstatement_of_natural_burned_cells": float(mean(all_biases)),
            "cluster_bootstrap_95_ci_of_mean_overstatement": _cluster_bootstrap_mean_ci(
                bias_by_scenario, seed=bootstrap_seed, draws=bootstrap_draws
            ),
            "reactive_benefit_sign_changed": proportion("reactive_benefit_sign_changed"),
            "coordinated_benefit_sign_changed": proportion("coordinated_benefit_sign_changed"),
            "response_ranking_changed": proportion("response_ranking_changed"),
        },
        "bootstrap_seed": bootstrap_seed,
        "bootstrap_draws": bootstrap_draws,
    }
    _atomic_text(
        destination / "fault_ablation_summary.json",
        json.dumps(summary, indent=2, allow_nan=False) + "\n",
    )
    return summary
