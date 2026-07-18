# Changelog

## 0.4.0 — 2026-07-11

### Scientific and systems evidence

- Added a controlled fault-injection study over 160 matched scenario-seed cases.
- Added event-keyed versus shared-stream random-drift ablation.
- Added complete-reset versus retained-fuel contamination ablation.
- Added synchronous versus sequential observation timing tests, including 1,000 adversarial microstates.
- Added causal state-conflation analysis with Wilson intervals and a scenario-cluster bootstrap.
- Added deterministic figures and machine-readable diagnostic outputs.

### Interoperability and reuse

- Added a tested PettingZoo `ParallelEnv` adapter behind the `interfaces` extra.
- Added a 160-case direct-engine versus adapter equivalence study.
- Added the public `run_strategy_episode` custom-strategy path.
- Added executable custom-strategy and PettingZoo examples.

### Quality and artifact evaluation

- Expanded the suite to 115 tests with 93.70% branch-aware coverage.
- Added full Artifact Evaluation checks for tests, coverage, examples, benchmark hashes, fault-study hashes, interface-study hashes, and 21 numerical claims.
- Added resumable `--reuse-existing` artifact verification.
- Updated CI, Docker, Makefile, documentation, metadata, and release packaging for version 0.4.0.
- Rewrote the anonymous JSys manuscript around controlled systems evidence rather than policy-performance claims.

## 0.3.2 — 2026-07-10

- Added the initial JSys Tools/Benchmark paper and Artifact Evaluation workflow.
- Added trace import/replay and scenario discovery commands.
- Added four regression and CLI tests.

## 0.3.1 — 2026-07-10

- Retargeted the package from JOSS to software-publication venues.
- Added software metadata and release assets.

## 0.3.0 — 2026-07-10

- Corrected fire-state semantics, reset behavior, random-stream handling, spawning, movement, water accounting, and benchmark statistics.
- Added no-response baseline, scenario serialization, traces, replay, and deterministic benchmark generation.
