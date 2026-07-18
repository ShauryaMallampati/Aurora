#!/usr/bin/env python3
"""Run the JSys artifact smoke or full reproducibility workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

from aurora.benchmark import run_reference_benchmark
from aurora.diagnostics import run_fault_ablation
from aurora.interoperability import run_interface_case_study


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    print(f"[artifact] running: {' '.join(command)}", file=sys.stderr, flush=True)
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    print(f"[artifact] completed: {' '.join(command)}", file=sys.stderr, flush=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def check_claims(summary: dict[str, object], expected: dict[str, object]) -> list[str]:
    checks: list[str] = []
    for key in ("total_episodes", "num_scenarios", "num_seeds"):
        if summary[key] != expected[key]:
            raise AssertionError(f"{key}: expected {expected[key]!r}, got {summary[key]!r}")
        checks.append(key)
    methods = summary["methods"]
    for method, value in expected["affected_area_mean"].items():
        actual = methods[method]["affected_area"]["mean"]
        if abs(actual - value) > 1e-12:
            raise AssertionError(f"affected_area mean for {method}: {actual} != {value}")
        checks.append(f"affected_area_mean:{method}")
    response = summary["response_vs_no_response"]
    for method, value in expected["avoided_affected_cells_mean"].items():
        actual = response[method]["avoided_affected_cells"]["mean"]
        if abs(actual - value) > 1e-12:
            raise AssertionError(f"avoided affected cells for {method}: {actual} != {value}")
        checks.append(f"avoided_affected_cells_mean:{method}")
    actual = summary["paired_response_comparison"]["affected_area"]["coordinated_minus_reactive"][
        "mean"
    ]
    value = expected["coordinated_minus_reactive_mean"]
    if abs(actual - value) > 1e-12:
        raise AssertionError(f"coordinated-minus-reactive mean: {actual} != {value}")
    checks.append("coordinated_minus_reactive_mean")
    return checks


def check_diagnostic_claims(
    fault_summary: dict[str, object],
    interface_summary: dict[str, object],
    expected: dict[str, object],
) -> list[str]:
    checks: list[str] = []

    def exact(name: str, actual: object) -> None:
        if actual != expected[name]:
            raise AssertionError(f"{name}: expected {expected[name]!r}, got {actual!r}")
        checks.append(name)

    exact("num_matched_cases", fault_summary["num_matched_cases"])
    exact(
        "keyed_rng_divergence_count",
        fault_summary["random_stream_drift"]["keyed_environment_rng_with_policy_noop"]["count"],
    )
    exact(
        "shared_rng_divergence_count",
        fault_summary["random_stream_drift"]["shared_global_rng_with_policy_noop"]["count"],
    )
    exact(
        "complete_reset_divergence_count",
        fault_summary["reset_contamination"]["complete_reset"]["count"],
    )
    exact(
        "incomplete_reset_divergence_count",
        fault_summary["reset_contamination"]["incomplete_reset"]["count"],
    )
    exact(
        "adversarial_information_leakage_count",
        fault_summary["within_step_information_leakage"]["adversarial_microstates"]["count"],
    )
    for name, actual in (
        (
            "mean_overstatement_of_natural_burned_cells",
            fault_summary["state_conflation"]["mean_overstatement_of_natural_burned_cells"],
        ),
        (
            "reactive_benefit_sign_change_rate",
            fault_summary["state_conflation"]["reactive_benefit_sign_changed"]["rate"],
        ),
        (
            "coordinated_benefit_sign_change_rate",
            fault_summary["state_conflation"]["coordinated_benefit_sign_changed"]["rate"],
        ),
        (
            "response_ranking_change_rate",
            fault_summary["state_conflation"]["response_ranking_changed"]["rate"],
        ),
    ):
        if abs(float(actual) - float(expected[name])) > 1e-12:
            raise AssertionError(f"{name}: expected {expected[name]!r}, got {actual!r}")
        checks.append(name)
    exact("interface_cases", interface_summary["num_cases"])
    exact(
        "interface_per_step_exact_matches",
        interface_summary["per_step_exact_matches"],
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--output-dir", type=Path, default=Path("artifact_output"))
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="reuse existing generated benchmark/diagnostic files and verify them",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    commands: list[dict[str, object]] = []

    validation_path = output / "validation.json"
    completed = run(
        [sys.executable, "-m", "aurora", "validate", "--output", str(validation_path)], root
    )
    commands.append({"command": "validate", "stdout": json.loads(completed.stdout)})

    trace_path = output / "trace.json"
    completed = run(
        [
            sys.executable,
            "-m",
            "aurora",
            "demo",
            "--method",
            "coordinated",
            "--scenario",
            "warm_crosswind",
            "--seed",
            "7",
            "--trace",
            str(trace_path),
        ],
        root,
    )
    commands.append({"command": "demo", "stdout": json.loads(completed.stdout)})
    completed = run([sys.executable, "-m", "aurora", "replay", str(trace_path)], root)
    replay = json.loads(completed.stdout)
    if replay["status"] != "PASS":
        raise AssertionError("trace replay did not pass")
    commands.append({"command": "replay", "stdout": replay})

    quality_checks: dict[str, object] = {}
    if args.mode == "full":
        coverage_path = output / "coverage.json"
        completed = run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=aurora",
                "--cov-branch",
                f"--cov-report=json:{coverage_path}",
                "-q",
            ],
            root,
        )
        match = re.search(r"(\d+) passed", completed.stdout)
        if match is None:
            raise AssertionError("could not parse pytest pass count")
        test_count = int(match.group(1))
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        coverage_percent = float(coverage["totals"]["percent_covered"])
        expected_quality = json.loads(
            (root / "artifact/expected/quality_claims.json").read_text(encoding="utf-8")
        )
        if test_count != int(expected_quality["test_count"]):
            raise AssertionError(
                f"test count differs: {test_count} != {expected_quality['test_count']}"
            )
        minimum = float(expected_quality["minimum_branch_aware_coverage_percent"])
        if coverage_percent < minimum:
            raise AssertionError(f"coverage below contract: {coverage_percent:.3f} < {minimum:.3f}")
        quality_checks = {
            "test_count": test_count,
            "branch_aware_coverage_percent": coverage_percent,
            "minimum_coverage_percent": minimum,
        }
        commands.append({"command": "pytest_coverage", **quality_checks})
        for example in ("examples/custom_strategy.py", "examples/pettingzoo_parallel.py"):
            completed = run([sys.executable, example], root)
            commands.append({"command": example, "stdout": completed.stdout.strip()})

    seeds = 20 if args.mode == "full" else 2
    benchmark_dir = output / "benchmark"
    benchmark_summary_path = benchmark_dir / "reference_benchmark_summary.json"
    if args.reuse_existing and benchmark_summary_path.exists():
        print("[artifact] reusing existing benchmark outputs", file=sys.stderr, flush=True)
        summary = json.loads(benchmark_summary_path.read_text(encoding="utf-8"))
    else:
        print(f"[artifact] running benchmark: {seeds} seeds", file=sys.stderr, flush=True)
        summary = run_reference_benchmark(benchmark_dir, seeds=range(seeds))
        print("[artifact] completed benchmark", file=sys.stderr, flush=True)
    expected_episodes = 8 * seeds * 3
    if summary["total_episodes"] != expected_episodes:
        raise AssertionError(
            f"expected {expected_episodes} episodes, got {summary['total_episodes']}"
        )
    commands.append({"command": "benchmark", "total_episodes": expected_episodes})

    hashes = {
        name: sha256(benchmark_dir / name)
        for name in ("reference_benchmark.csv", "reference_benchmark_summary.json")
    }
    claim_checks: list[str] = []
    if args.mode == "full":
        expected_hashes = json.loads(
            (root / "artifact/expected/benchmark_hashes.json").read_text(encoding="utf-8")
        )
        if hashes != expected_hashes:
            raise AssertionError(f"benchmark hashes differ: {hashes} != {expected_hashes}")
        expected_claims = json.loads(
            (root / "artifact/expected/paper_claims.json").read_text(encoding="utf-8")
        )
        claim_checks = check_claims(summary, expected_claims)

    fault_dir = output / "fault_ablation"
    fault_seeds = 20 if args.mode == "full" else 1
    fault_draws = 2000 if args.mode == "full" else 50
    fault_summary_path = fault_dir / "fault_ablation_summary.json"
    if args.reuse_existing and fault_summary_path.exists():
        print("[artifact] reusing existing fault-ablation outputs", file=sys.stderr, flush=True)
        fault_summary = json.loads(fault_summary_path.read_text(encoding="utf-8"))
    else:
        message = (
            f"[artifact] running fault ablation: {fault_seeds} seeds, {fault_draws} bootstrap draws"
        )
        print(message, file=sys.stderr, flush=True)
        fault_summary = run_fault_ablation(
            fault_dir, seeds=range(fault_seeds), bootstrap_draws=fault_draws
        )
        print("[artifact] completed fault ablation", file=sys.stderr, flush=True)
    commands.append(
        {"command": "ablation", "num_matched_cases": fault_summary["num_matched_cases"]}
    )

    interface_dir = output / "interface_case_study"
    interface_seeds = 20 if args.mode == "full" else 1
    interface_summary_path = interface_dir / "interface_summary.json"
    if args.reuse_existing and interface_summary_path.exists():
        print("[artifact] reusing existing interface outputs", file=sys.stderr, flush=True)
        interface_summary = json.loads(interface_summary_path.read_text(encoding="utf-8"))
    else:
        print(
            f"[artifact] running interface case study: {interface_seeds} seeds",
            file=sys.stderr,
            flush=True,
        )
        interface_summary = run_interface_case_study(interface_dir, seeds=range(interface_seeds))
        print("[artifact] completed interface case study", file=sys.stderr, flush=True)
    commands.append(
        {"command": "interface_case_study", "num_cases": interface_summary["num_cases"]}
    )

    diagnostic_hashes: dict[str, dict[str, str]] = {}
    diagnostic_checks: list[str] = []
    if args.mode == "full":
        fault_hashes = {
            name: sha256(fault_dir / name)
            for name in ("fault_ablation_cases.csv", "fault_ablation_summary.json")
        }
        expected_fault_hashes = json.loads(
            (root / "artifact/expected/fault_hashes.json").read_text(encoding="utf-8")
        )
        if fault_hashes != expected_fault_hashes:
            raise AssertionError(
                f"fault-ablation hashes differ: {fault_hashes} != {expected_fault_hashes}"
            )
        interface_hashes = {
            name: sha256(interface_dir / name)
            for name in ("interface_cases.csv", "interface_summary.json")
        }
        expected_interface_hashes = json.loads(
            (root / "artifact/expected/interface_hashes.json").read_text(encoding="utf-8")
        )
        if interface_hashes != expected_interface_hashes:
            raise AssertionError(
                f"interface hashes differ: {interface_hashes} != {expected_interface_hashes}"
            )
        diagnostic_hashes = {"fault_ablation": fault_hashes, "interface": interface_hashes}
        expected_diagnostics = json.loads(
            (root / "artifact/expected/diagnostic_claims.json").read_text(encoding="utf-8")
        )
        diagnostic_checks = check_diagnostic_claims(
            fault_summary, interface_summary, expected_diagnostics
        )

    report = {
        "status": "PASS",
        "mode": args.mode,
        "elapsed_seconds": time.perf_counter() - started,
        "python": sys.version,
        "platform": platform.platform(),
        "commands": commands,
        "benchmark_hashes": hashes,
        "claim_checks": claim_checks,
        "diagnostic_hashes": diagnostic_hashes,
        "diagnostic_checks": diagnostic_checks,
        "quality_checks": quality_checks,
    }
    report_path = output / "artifact_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
