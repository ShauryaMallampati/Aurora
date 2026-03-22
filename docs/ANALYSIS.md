# AURORA Analysis Status

**Last updated:** March 22, 2026

This document is intentionally conservative. It points to the current reviewer-facing artifacts and does not restate claims that are not yet fully supported by completed runs in the repository.

## Current status

- The repository contains the hybrid PPO + LLM training pipeline, evaluation helpers, and ablation-study orchestration.
- Reviewer-facing outputs are collected under `results/ablation_study/`.
- The current empirical state of the project is summarized in `results/ablation_study/FINAL_AUDIT.md`.

## Reviewer-facing files

- `results/ablation_study/README.md`: artifact index and usage notes
- `results/ablation_study/REPO_AUDIT.md`: repository audit and pipeline map
- `results/ablation_study/FINAL_AUDIT.md`: completed experiments, failed experiments, blockers, and consistency checks
- `results/ablation_study/PAPER_SNIPPETS.md`: draft paper text generated from available artifacts
- `results/ablation_study/estrat_spec.md`: strategic observation tensor specification
- `results/ablation_study/fallback_analysis/`: fallback-rate summaries and one real prompt/response example

## Interpretation guidance

Use the audit files in `results/ablation_study/` as the source of truth. If a table, plot, or summary is not backed by completed runs listed in `FINAL_AUDIT.md`, it should be treated as incomplete rather than publication-ready.

## Data and training pipeline

The codebase integrates:

- InterAgency fire perimeter data for scenario generation
- NOAA weather data when available
- terrain-derived features used by the simulator

Training entrypoints, evaluation flow, model locations, and logging outputs are summarized in `results/ablation_study/REPO_AUDIT.md`.
