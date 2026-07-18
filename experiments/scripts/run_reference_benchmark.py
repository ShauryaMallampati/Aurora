"""Regenerate the complete reference benchmark from package source."""

from pathlib import Path

from aurora.benchmark import run_reference_benchmark

if __name__ == "__main__":
    run_reference_benchmark(
        Path("experiments/processed_results"),
        seeds=range(20),
        bootstrap_seed=20260710,
        bootstrap_draws=5000,
    )
