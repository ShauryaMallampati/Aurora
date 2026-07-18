import csv
import json

import pytest

from aurora.benchmark import _stabilize, run_reference_benchmark
from aurora.types import Scenario


def test_stabilize_rounds_floats_for_cross_version_reproducibility():
    # statistics.stdev differs in the last ULP across CPython 3.10-3.13; the
    # serialized summary must not depend on those bits or the artifact hash
    # contract breaks on independent evaluator machines.
    noisy = {
        "std": 5.261578710455237,
        "nested": [1.4095538674570611, {"ci": (4.76078125, 9.931250001)}],
        "count": 160,
        "label": "keep",
    }
    stable = _stabilize(noisy)
    assert stable["std"] == round(5.261578710455237, 9)
    assert stable["nested"][0] == round(1.4095538674570611, 9)
    assert stable["nested"][1]["ci"] == [4.76078125, round(9.931250001, 9)]
    assert stable["count"] == 160
    assert stable["label"] == "keep"


def test_summary_floats_are_stable_to_nine_decimals(tmp_path):
    scenario = Scenario(name="tiny", grid_size=12, max_steps=8)
    run_reference_benchmark(tmp_path, seeds=[1, 2, 3], scenarios=[scenario], bootstrap_draws=100)
    summary = json.loads((tmp_path / "reference_benchmark_summary.json").read_text())
    std = summary["methods"]["no_response"]["affected_area"]["std"]
    assert std == round(std, 9)


def test_benchmark_writes_raw_and_summary(tmp_path):
    scenario = Scenario(name="tiny", grid_size=12, max_steps=8)
    summary = run_reference_benchmark(
        tmp_path, seeds=[1, 2], scenarios=[scenario], bootstrap_draws=100
    )
    assert summary["num_episodes_per_method"] == 2
    assert summary["total_episodes"] == 6
    rows = list(csv.DictReader((tmp_path / "reference_benchmark.csv").open()))
    assert len(rows) == 6
    loaded = json.loads((tmp_path / "reference_benchmark_summary.json").read_text())
    assert loaded["benchmark_version"] == "3.0"
    assert (
        "hierarchical_paired_bootstrap_95_ci_of_mean"
        in loaded["paired_response_comparison"]["affected_area"]
    )


def test_benchmark_is_reproducible_in_memory_and_on_disk(tmp_path):
    scenario = Scenario(name="tiny", grid_size=12, max_steps=8)
    first = run_reference_benchmark(
        tmp_path / "a", seeds=[1, 2], scenarios=[scenario], bootstrap_draws=100
    )
    second = run_reference_benchmark(
        tmp_path / "b", seeds=[1, 2], scenarios=[scenario], bootstrap_draws=100
    )
    assert first == second
    assert (tmp_path / "a/reference_benchmark.csv").read_bytes() == (
        tmp_path / "b/reference_benchmark.csv"
    ).read_bytes()
    assert (tmp_path / "a/reference_benchmark_summary.json").read_bytes() == (
        tmp_path / "b/reference_benchmark_summary.json"
    ).read_bytes()


def test_repeated_run_replaces_outputs_cleanly(tmp_path):
    scenario = Scenario(name="tiny", grid_size=12, max_steps=8)
    run_reference_benchmark(tmp_path, seeds=[1], scenarios=[scenario], bootstrap_draws=50)
    first = (tmp_path / "reference_benchmark.csv").read_bytes()
    run_reference_benchmark(tmp_path, seeds=[1], scenarios=[scenario], bootstrap_draws=50)
    assert (tmp_path / "reference_benchmark.csv").read_bytes() == first


@pytest.mark.parametrize(
    "seeds, scenarios, message",
    [
        ([], [Scenario(name="x")], "seed"),
        ([1], [], "scenario"),
        ([1, 1], [Scenario(name="x")], "unique"),
    ],
)
def test_invalid_benchmark_inputs_rejected(tmp_path, seeds, scenarios, message):
    with pytest.raises(ValueError, match=message):
        run_reference_benchmark(tmp_path, seeds=seeds, scenarios=scenarios, bootstrap_draws=10)


def test_duplicate_scenario_names_rejected(tmp_path):
    with pytest.raises(ValueError, match="unique"):
        run_reference_benchmark(
            tmp_path,
            seeds=[1],
            scenarios=[Scenario(name="x"), Scenario(name="x")],
            bootstrap_draws=10,
        )


def test_nonpositive_bootstrap_draws_rejected(tmp_path):
    with pytest.raises(ValueError, match="positive"):
        run_reference_benchmark(
            tmp_path, seeds=[1], scenarios=[Scenario(name="x")], bootstrap_draws=0
        )


def test_summary_json_contains_no_nonstandard_nan(tmp_path):
    run_reference_benchmark(
        tmp_path,
        seeds=[1],
        scenarios=[Scenario(name="x", grid_size=12, max_steps=4)],
        bootstrap_draws=10,
    )
    text = (tmp_path / "reference_benchmark_summary.json").read_text()
    assert "NaN" not in text
