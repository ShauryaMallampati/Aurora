from __future__ import annotations

import json

import pytest

from aurora.diagnostics import (
    run_fault_ablation,
    run_information_leakage_stress_cases,
    sequential_observation_microcase,
)
from aurora.scenarios import REFERENCE_SCENARIOS


def test_sequential_microcase_exposes_information_leakage():
    result = sequential_observation_microcase()
    assert result == {
        "synchronous_unique_suppressions": 1,
        "sequential_suppressions": 2,
    }


def test_adversarial_information_leakage_study_is_deterministic():
    first = run_information_leakage_stress_cases(num_cases=50, seed=9)
    second = run_information_leakage_stress_cases(num_cases=50, seed=9)
    assert first == second
    assert first["count"] == 50
    assert first["mean_extra_suppressions_in_flawed_variant"] == 1.0


def test_fault_ablation_detects_injected_faults(tmp_path):
    summary = run_fault_ablation(
        tmp_path,
        scenarios=REFERENCE_SCENARIOS[:2],
        seeds=range(2),
        bootstrap_draws=50,
    )
    assert summary["num_matched_cases"] == 4
    assert summary["random_stream_drift"]["keyed_environment_rng_with_policy_noop"]["count"] == 0
    assert summary["random_stream_drift"]["shared_global_rng_with_policy_noop"]["count"] == 4
    assert summary["reset_contamination"]["complete_reset"]["count"] == 0
    assert summary["reset_contamination"]["incomplete_reset"]["count"] == 4
    assert summary["within_step_information_leakage"]["adversarial_microstates"]["count"] == 1000
    assert (tmp_path / "fault_ablation_cases.csv").is_file()
    loaded = json.loads((tmp_path / "fault_ablation_summary.json").read_text())
    assert loaded == summary


@pytest.mark.parametrize("seeds", [[], [1, 1]])
def test_fault_ablation_rejects_invalid_seeds(tmp_path, seeds):
    with pytest.raises(ValueError):
        run_fault_ablation(
            tmp_path,
            scenarios=REFERENCE_SCENARIOS[:1],
            seeds=seeds,
            bootstrap_draws=10,
        )


def test_fault_ablation_rejects_invalid_draw_count(tmp_path):
    with pytest.raises(ValueError):
        run_fault_ablation(
            tmp_path,
            scenarios=REFERENCE_SCENARIOS[:1],
            seeds=[0],
            bootstrap_draws=0,
        )
