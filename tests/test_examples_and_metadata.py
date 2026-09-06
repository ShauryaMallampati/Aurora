from __future__ import annotations

import json
import runpy
from pathlib import Path

import aurora
from aurora.coordination import EpisodeResult, EpisodeTrace, run_episode, verify_trace
from aurora.scenarios import REFERENCE_SCENARIOS, load_scenarios

ROOT = Path(__file__).resolve().parents[1]


def test_checked_sample_result_matches_release() -> None:
    expected = json.loads(
        (ROOT / "examples/sample_output/coordinated_result.json").read_text(encoding="utf-8")
    )
    scenario = next(item for item in REFERENCE_SCENARIOS if item.name == "warm_crosswind")
    assert run_episode("coordinated", scenario, seed=7).to_dict() == expected


def test_checked_trace_replays() -> None:
    payload = json.loads(
        (ROOT / "examples/sample_output/coordinated_trace.json").read_text(encoding="utf-8")
    )
    trace = EpisodeTrace(
        schema_version=payload["schema_version"],
        method=payload["method"],
        scenario=payload["scenario"],
        seed=payload["seed"],
        frames=tuple(payload["frames"]),
        result=EpisodeResult(**payload["result"]),
    )
    assert verify_trace(trace)


def test_sample_scenario_manifest_loads() -> None:
    scenarios = load_scenarios(ROOT / "examples/sample_scenario.json")
    assert len(scenarios) == 1
    assert scenarios[0].name == "warm_crosswind"


def test_minimal_example_runs(capsys) -> None:
    runpy.run_path(str(ROOT / "examples/minimal.py"), run_name="__main__")
    output = capsys.readouterr().out
    assert "affected_area" in output


def test_codemeta_matches_package_version() -> None:
    payload = json.loads((ROOT / "docs/codemeta.json").read_text(encoding="utf-8"))
    assert payload["version"] == aurora.__version__
    assert payload["license"].endswith("MIT.html")
