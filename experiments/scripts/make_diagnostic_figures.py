#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    labels = [
        "Keyed RNG\n+ no-op draw",
        "Shared RNG\n+ no-op draw",
        "Complete\nreset",
        "Incomplete\nreset",
        "Synchronous\nbenchmark",
        "Sequential\nstress cases",
    ]
    values = [
        summary["random_stream_drift"]["keyed_environment_rng_with_policy_noop"]["rate"],
        summary["random_stream_drift"]["shared_global_rng_with_policy_noop"]["rate"],
        summary["reset_contamination"]["complete_reset"]["rate"],
        summary["reset_contamination"]["incomplete_reset"]["rate"],
        summary["within_step_information_leakage"]["reference_benchmark_cases"]["rate"],
        summary["within_step_information_leakage"]["adversarial_microstates"]["rate"],
    ]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    bars = ax.bar(np.arange(len(labels)), np.asarray(values) * 100.0)
    ax.set_ylabel("Cases with changed outcome (%)")
    ax.set_ylim(0, 108)
    ax.set_xticks(np.arange(len(labels)), labels)
    ax.grid(axis="y", alpha=0.3)
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2, value * 100 + 2, f"{value * 100:.0f}%", ha="center"
        )
    fig.tight_layout()
    fig.savefig(args.output_dir / "fault_isolation.pdf", bbox_inches="tight")
    fig.savefig(args.output_dir / "fault_isolation.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    labels = ["Reactive benefit sign", "Coordinated benefit sign", "Policy ranking"]
    values = [
        summary["state_conflation"]["reactive_benefit_sign_changed"]["rate"],
        summary["state_conflation"]["coordinated_benefit_sign_changed"]["rate"],
        summary["state_conflation"]["response_ranking_changed"]["rate"],
    ]
    intervals = [
        summary["state_conflation"]["reactive_benefit_sign_changed"]["wilson_95_ci"],
        summary["state_conflation"]["coordinated_benefit_sign_changed"]["wilson_95_ci"],
        summary["state_conflation"]["response_ranking_changed"]["wilson_95_ci"],
    ]
    values_pct = np.asarray(values) * 100.0
    lower = values_pct - np.asarray([x[0] for x in intervals]) * 100.0
    upper = np.asarray([x[1] for x in intervals]) * 100.0 - values_pct
    fig, ax = plt.subplots(figsize=(6.4, 3.1))
    bars = ax.bar(np.arange(len(labels)), values_pct, yerr=np.vstack([lower, upper]), capsize=4)
    ax.set_ylabel("Matched cases changed (%)")
    ax.set_ylim(0, 70)
    ax.set_xticks(np.arange(len(labels)), labels, rotation=10, ha="right")
    ax.grid(axis="y", alpha=0.3)
    for bar, value in zip(bars, values_pct, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 2, f"{value:.1f}%", ha="center")
    fig.tight_layout()
    fig.savefig(args.output_dir / "state_conflation.pdf", bbox_inches="tight")
    fig.savefig(args.output_dir / "state_conflation.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
