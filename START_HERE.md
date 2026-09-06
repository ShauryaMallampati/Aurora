# Start Here - JSys Artifact Evaluation

This package accompanies the anonymous Tools/Benchmark submission. It contains the exact AURORA 0.4.0 source, tests, expected hashes, and generated reference evidence. Build release distributions locally with `python -m build`.

## Recommended evaluation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install '.[dev,figures,interfaces]'
python artifact/scripts/run_artifact.py --mode smoke --output-dir artifact_output_smoke
python artifact/scripts/run_artifact.py --mode full --output-dir artifact_output_full
```

Expected status is `PASS`. See `artifact/README.md` for stage-by-stage and resumable commands. The artifact validates software behavior and experimental isolation; it does not claim physical wildfire fidelity or operational suitability.
