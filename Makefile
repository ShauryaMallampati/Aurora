.PHONY: install test coverage validate artifact-smoke artifact-full benchmark ablation interface build clean

install:
	python -m pip install -e '.[dev,figures,interfaces]'

test:
	python -m pytest

coverage:
	python -m pytest --cov=aurora --cov-branch --cov-report=term-missing

validate:
	python -m aurora validate --output artifact_output/validation.json

artifact-smoke:
	python artifact/scripts/run_artifact.py --mode smoke --output-dir artifact_output_smoke

artifact-full:
	python artifact/scripts/run_artifact.py --mode full --output-dir artifact_output_full

benchmark:
	python -m aurora benchmark --output-dir experiments/processed_results --num-seeds 20

ablation:
	python -m aurora ablation --output-dir experiments/processed_results/fault_ablation --num-seeds 20 --bootstrap-draws 2000

interface:
	python experiments/scripts/run_interface_case_study.py --output-dir experiments/processed_results/interface_case_study --num-seeds 20

build:
	python -m build

clean:
	rm -rf build dist .pytest_cache .coverage htmlcov artifact_output artifact_output_*
