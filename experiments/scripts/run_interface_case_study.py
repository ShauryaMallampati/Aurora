#!/usr/bin/env python3
"""Validate that the PettingZoo adapter preserves direct engine trajectories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aurora.interoperability import run_interface_case_study


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--num-seeds", type=int, default=20)
    args = parser.parse_args()
    if args.num_seeds <= 0:
        raise SystemExit("--num-seeds must be positive")
    summary = run_interface_case_study(args.output_dir, seeds=range(args.num_seeds))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
