# JSys Artifact Evaluation Guide

This single-blind artifact accompanies an anonymous JSys Tools/Benchmark submission. It evaluates the paper's software, fault-isolation, interoperability, and reproducibility claims on Linux with Python 3.10 or later. It requires no GPU, external service, private dataset, or network access after dependencies are installed.

## Claims evaluated

The full workflow checks:

1. package validation passes;
2. a seeded episode records and replays with the same canonical digest;
3. 115 tests pass and branch-aware coverage remains at least 93.5%;
4. the custom-strategy and PettingZoo examples execute;
5. the reference benchmark contains 8 scenarios × 20 seeds × 3 methods = 480 episodes;
6. benchmark CSV/JSON hashes and nine manuscript values match;
7. the 160-case controlled fault study regenerates exactly;
8. twelve fault/interoperability claims match the manuscript contract;
9. the 160-case direct-engine/PettingZoo study matches after every no-op transition.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install '.[dev,figures,interfaces]'
```

The package may also be installed from the included wheel. Linux is the primary Artifact Evaluation platform; the core package is designed for Linux, macOS, and Windows.

## Fast smoke test

```bash
python artifact/scripts/run_artifact.py \
  --mode smoke --output-dir artifact_output_smoke
```

The smoke workflow runs validation, trace record/replay, a 48-episode benchmark, an 8-case fault study, and an 8-case interface study. Expected final status: `PASS`.

## Full reproduction

```bash
python artifact/scripts/run_artifact.py \
  --mode full --output-dir artifact_output_full
```

The full workflow generates all evidence and exits nonzero on any failure. In the audited environment, the long stages took approximately:

- reference benchmark: 12.4 seconds;
- fault study: 29.3 seconds;
- interface study: 4.5 seconds;
- tests/examples/final verification: 6.4 seconds.

Expect roughly one minute on a contemporary CPU, with hardware-dependent variation. Peak resident memory remained below 200 MB in the audited environment.

## Resumable verification

Long stages write atomically. If they were generated separately or a previous run was interrupted after generation, verify them without recomputation:

```bash
python artifact/scripts/run_artifact.py \
  --mode full --reuse-existing --output-dir artifact_output_full
```

`--reuse-existing` does not weaken verification: benchmark, fault, and interface hashes and parsed claims are still checked. A missing stage is regenerated.

## Manual stage commands

```bash
aurora benchmark \
  --output-dir artifact_output_full/benchmark --num-seeds 20

aurora ablation \
  --output-dir artifact_output_full/fault_ablation \
  --num-seeds 20 --bootstrap-draws 2000

python experiments/scripts/run_interface_case_study.py \
  --output-dir artifact_output_full/interface_case_study \
  --num-seeds 20

python artifact/scripts/run_artifact.py \
  --mode full --reuse-existing --output-dir artifact_output_full
```

## Outputs

- `artifact_report.json` — overall status, runtime, platform, checks, and hashes;
- `validation.json` — installation and deterministic-lifecycle checks;
- `trace.json` — recorded replay fixture;
- `coverage.json` — branch-aware coverage data;
- `benchmark/` — raw benchmark CSV and summary JSON;
- `fault_ablation/` — controlled-fault case CSV and summary JSON;
- `interface_case_study/` — direct-versus-adapter case CSV and summary JSON.

Expected contracts are under `artifact/expected/`:

- `benchmark_hashes.json`
- `paper_claims.json`
- `fault_hashes.json`
- `interface_hashes.json`
- `diagnostic_claims.json`
- `quality_claims.json`

## Interpretation boundary

The artifact validates deterministic software behavior, experimental isolation, and the consequences of deliberately injected faults. It does not validate physical wildfire fidelity, operational response effectiveness, or defect prevalence in third-party software.
