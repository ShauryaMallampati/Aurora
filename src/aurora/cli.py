"""Command-line entry points for AURORA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import run_reference_benchmark
from .coordination import EpisodeTrace, run_episode, run_episode_with_trace, verify_trace
from .diagnostics import run_fault_ablation
from .scenarios import REFERENCE_SCENARIOS, load_scenarios
from .validation import validate_core


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aurora", description="AURORA wildfire-response research software"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="run one deterministic reference episode")
    demo.add_argument(
        "--method", choices=["no_response", "reactive", "coordinated"], default="coordinated"
    )
    demo.add_argument(
        "--scenario",
        choices=[item.name for item in REFERENCE_SCENARIOS],
        default="warm_crosswind",
    )
    demo.add_argument("--seed", type=int, default=7)
    demo.add_argument(
        "--trace",
        "--trace-output",
        dest="trace",
        type=Path,
        default=None,
        help="write a replayable JSON trace",
    )

    benchmark = subparsers.add_parser("benchmark", help="run the matched reference benchmark")
    benchmark.add_argument("--output-dir", type=Path, default=Path("experiments/processed_results"))
    benchmark.add_argument("--num-seeds", type=int, default=20)
    benchmark.add_argument(
        "--scenario-manifest",
        type=Path,
        default=None,
        help="optional JSON scenario manifest; defaults to bundled reference scenarios",
    )
    benchmark.add_argument("--bootstrap-draws", type=int, default=5000)

    replay = subparsers.add_parser("replay", help="verify a recorded episode trace")
    replay.add_argument("trace", type=Path, help="path to a JSON EpisodeTrace")

    scenarios = subparsers.add_parser("scenarios", help="list bundled reference scenarios")
    scenarios.add_argument("--output", type=Path, default=None, help="optional JSON output path")

    ablation = subparsers.add_parser(
        "ablation", help="run controlled reproducibility fault-injection experiments"
    )
    ablation.add_argument(
        "--output-dir", type=Path, default=Path("experiments/processed_results/fault_ablation")
    )
    ablation.add_argument("--num-seeds", type=int, default=40)
    ablation.add_argument("--bootstrap-draws", type=int, default=5000)

    validate = subparsers.add_parser("validate", help="validate deterministic core functionality")
    validate.add_argument("--output", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        scenario = next(item for item in REFERENCE_SCENARIOS if item.name == args.scenario)
        if args.trace is None:
            payload = run_episode(args.method, scenario, args.seed).to_dict()
        else:
            trace = run_episode_with_trace(args.method, scenario, args.seed)
            args.trace.parent.mkdir(parents=True, exist_ok=True)
            args.trace.write_text(json.dumps(trace.to_dict(), indent=2) + "\n", encoding="utf-8")
            payload = {
                **trace.result.to_dict(),
                "trace": str(args.trace),
                "trace_sha256": trace.sha256(),
            }
        print(json.dumps(payload, indent=2))
        return 0
    if args.command == "benchmark":
        if args.num_seeds <= 0:
            raise SystemExit("--num-seeds must be positive")
        if args.bootstrap_draws <= 0:
            raise SystemExit("--bootstrap-draws must be positive")
        scenarios = (
            load_scenarios(args.scenario_manifest)
            if args.scenario_manifest is not None
            else REFERENCE_SCENARIOS
        )
        summary = run_reference_benchmark(
            args.output_dir,
            seeds=range(args.num_seeds),
            scenarios=scenarios,
            bootstrap_draws=args.bootstrap_draws,
        )
        print(json.dumps(summary, indent=2))
        return 0
    if args.command == "replay":
        payload = json.loads(args.trace.read_text(encoding="utf-8"))
        trace = EpisodeTrace.from_dict(payload)
        valid = verify_trace(trace)
        result = {"status": "PASS" if valid else "FAIL", "trace_sha256": trace.sha256()}
        print(json.dumps(result, indent=2))
        return 0 if valid else 1
    if args.command == "scenarios":
        payload = {
            "schema_version": "1.0",
            "scenarios": [scenario.to_dict() for scenario in REFERENCE_SCENARIOS],
        }
        text = json.dumps(payload, indent=2) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0
    if args.command == "ablation":
        if args.num_seeds <= 0:
            raise SystemExit("--num-seeds must be positive")
        if args.bootstrap_draws <= 0:
            raise SystemExit("--bootstrap-draws must be positive")
        summary = run_fault_ablation(
            args.output_dir,
            seeds=range(args.num_seeds),
            bootstrap_draws=args.bootstrap_draws,
        )
        print(json.dumps(summary, indent=2))
        return 0
    report = validate_core(args.output)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
