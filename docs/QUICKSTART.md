# Quick Start

## Requirements

- Python 3.10–3.13
- Linux, macOS, or Windows for the core package
- Linux recommended for reproducing the JSys Artifact Evaluation environment

## Install

```bash
git clone https://github.com/ShauryaMallampati/Aurora.git
cd Aurora
python -m venv .venv
source .venv/bin/activate  # PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install '.[dev,figures,interfaces]'
```

## Verify installation

```bash
aurora --help
aurora validate --output validation.json
```

Expected: JSON with `"status": "PASS"` and a `validation.json` file.

## Run and replay an episode

```bash
aurora demo \
  --method coordinated \
  --scenario warm_crosswind \
  --seed 7 \
  --trace trace.json

aurora replay trace.json
```

Expected replay status: `PASS`.

## Run examples

```bash
python examples/minimal.py
python examples/custom_strategy.py
python examples/pettingzoo_parallel.py
```

## Run tests

```bash
python -m pytest
python -m pytest --cov=aurora --cov-branch --cov-report=term-missing
```

Release expectation: 115 passed and at least 93.5% branch-aware coverage.

## Run evidence workflows

```bash
aurora benchmark --output-dir benchmark_output --num-seeds 20
aurora ablation --output-dir fault_output --num-seeds 20 --bootstrap-draws 2000
python experiments/scripts/run_interface_case_study.py \
  --output-dir interface_output --num-seeds 20
```

Or run the integrated Artifact Evaluation command:

```bash
python artifact/scripts/run_artifact.py --mode full --output-dir artifact_output_full
```
