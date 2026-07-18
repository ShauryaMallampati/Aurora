# Troubleshooting

## `ModuleNotFoundError: aurora`

Install the package first with `python -m pip install .` or use `PYTHONPATH=src` only for source-tree development.

## Figure generation cannot import Matplotlib

Install the figure extra: `python -m pip install -e '.[figures]'`.

## Results differ

Confirm the package version, scenario manifest, seed list, Python/NumPy versions, and benchmark configuration. Delete only the output directory, not source files, then regenerate. Compare the raw CSV and summary SHA-256 hashes.

## Windows activation fails

In PowerShell use `.venv\Scripts\Activate.ps1`; in `cmd.exe` use `.venv\Scripts\activate.bat`.

## A trace fails replay

Replay is guaranteed only for the same AURORA version and compatible dependency versions. Preserve the scenario, method, seed, and full trace JSON. A failure within the same version is a bug and should be reported with the trace.

## Do not interpret fire inactivity as containment

All built-in fires eventually become inactive in the current finite-fuel model, including no-response runs. Use paired affected-area differences for the bundled validation benchmark.
