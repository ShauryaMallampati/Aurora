from __future__ import annotations

import csv
import json

import pytest

from aurora.interoperability import run_interface_case_study
from aurora.scenarios import REFERENCE_SCENARIOS


def test_interface_case_study_matches_direct_engine(tmp_path):
    summary = run_interface_case_study(
        tmp_path,
        scenarios=REFERENCE_SCENARIOS[:2],
        seeds=[0, 1],
    )
    assert summary == {
        "study_version": "1.0",
        "num_scenarios": 2,
        "num_seeds": 2,
        "num_cases": 4,
        "per_step_exact_matches": 4,
        "final_digest_matches": 4,
        "affected_area_matches": 4,
        "interpretation": (
            "Stay actions through the PettingZoo ParallelEnv leave fire dynamics unchanged; "
            "the adapter and direct engine are compared after every transition."
        ),
    }
    with (tmp_path / "interface_cases.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert all(row["per_step_exact_match"] == "True" for row in rows)
    assert json.loads((tmp_path / "interface_summary.json").read_text()) == summary


@pytest.mark.parametrize(
    ("scenarios", "seeds"),
    [([], [0]), (REFERENCE_SCENARIOS[:1], [])],
)
def test_interface_case_study_requires_scenarios_and_seeds(tmp_path, scenarios, seeds):
    with pytest.raises(ValueError, match="requires scenarios and seeds"):
        run_interface_case_study(tmp_path, scenarios=scenarios, seeds=seeds)
