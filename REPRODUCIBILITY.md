# Reproducibility Contract

## Clean build and install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install build
python -m build
python -m pip install 'dist/aurora_wildfire-0.4.0-py3-none-any.whl[interfaces]'
```

For tests and figures from the source tree:

```bash
python -m pip install '.[dev,figures,interfaces]'
```

## Core checks

```bash
aurora --help
aurora scenarios
aurora demo --method coordinated --scenario warm_crosswind --seed 7 --trace trace.json
aurora replay trace.json
aurora validate --output validation.json
python examples/custom_strategy.py
python examples/pettingzoo_parallel.py
python -m pytest
python -m pytest --cov=aurora --cov-branch --cov-report=term-missing
```

Release expectation: 115 tests and at least 93.5% branch-aware coverage.

## JSys Artifact Evaluation

```bash
python artifact/scripts/run_artifact.py --mode smoke --output-dir artifact_output_smoke
python artifact/scripts/run_artifact.py --mode full --output-dir artifact_output_full
```

The full workflow covers record/replay, tests, coverage, examples, the 480-episode benchmark, the 160-case fault study, the 160-case interface study, exact release hashes, and 21 numerical paper claims. Any mismatch returns a nonzero status.

See `artifact/README.md` for manual stage execution and resumable verification.

## Paper build

The anonymous submission uses the official JSys style included in `paper/jsys.sty` and the `plainurl` BibTeX style.

```bash
cd paper
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Some Debian images expose the binary as `bibtex.original` because of an alternatives configuration; standard TeX installations use `bibtex`.

## Audited environment

Final local validation used CPython 3.13.5 on Linux. The package declares Python 3.10–3.13 and public CI is configured for all four versions. Cross-platform CI must be confirmed after the exact release is pushed.
