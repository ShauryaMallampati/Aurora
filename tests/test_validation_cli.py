import json
import subprocess
import sys

import pytest

from aurora.cli import main
from aurora.scenarios import save_scenarios
from aurora.types import Scenario
from aurora.validation import validate_core


def test_validation_report_passes(tmp_path):
    output = tmp_path / "validation.json"
    report = validate_core(output)
    assert report["status"] == "PASS"
    assert json.loads(output.read_text())["status"] == "PASS"
    assert len(report["checks"]) >= 5


def test_cli_demo(capsys):
    assert main(["demo", "--method", "reactive", "--scenario", "calm_humid", "--seed", "1"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "reactive"


def test_cli_demo_writes_trace(tmp_path, capsys):
    path = tmp_path / "trace.json"
    assert main(["demo", "--scenario", "calm_humid", "--seed", "1", "--trace", str(path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert path.exists()
    assert len(payload["trace_sha256"]) == 64
    assert json.loads(path.read_text())["schema_version"] == "1.0"


def test_cli_benchmark_custom_manifest(tmp_path, capsys):
    manifest = save_scenarios(
        tmp_path / "manifest.json", [Scenario(name="tiny", grid_size=12, max_steps=3)]
    )
    output = tmp_path / "results"
    assert (
        main(
            [
                "benchmark",
                "--num-seeds",
                "1",
                "--bootstrap-draws",
                "10",
                "--scenario-manifest",
                str(manifest),
                "--output-dir",
                str(output),
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_episodes"] == 3


def test_cli_rejects_nonpositive_seed_count():
    with pytest.raises(SystemExit, match="positive"):
        main(["benchmark", "--num-seeds", "0"])


def test_module_help_runs():
    completed = subprocess.run(
        [sys.executable, "-m", "aurora", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "wildfire-response" in completed.stdout


def test_cli_replay_verifies_trace(tmp_path, capsys):
    path = tmp_path / "trace.json"
    assert main(["demo", "--scenario", "calm_humid", "--seed", "2", "--trace", str(path)]) == 0
    capsys.readouterr()
    assert main(["replay", str(path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS"
    assert len(payload["trace_sha256"]) == 64


def test_cli_replay_rejects_bad_schema(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema_version": "9.9"}))
    with pytest.raises(ValueError, match="schema_version"):
        main(["replay", str(path)])


def test_cli_lists_scenarios(tmp_path, capsys):
    output = tmp_path / "scenarios.json"
    assert main(["scenarios", "--output", str(output)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["scenarios"]) == 8
    assert json.loads(output.read_text()) == payload
