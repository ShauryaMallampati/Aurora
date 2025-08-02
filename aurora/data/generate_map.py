"""
Terrain generation script for AURORA.

This script produces a 20×20 numpy array representing a random
environment.  Each cell takes one of four integer codes indicating the
terrain type:

  * 0 – empty (no vegetation)
  * 1 – forest (flammable)
  * 2 – road (non‑flammable)
  * 3 – water (non‑flammable)

By default the distribution of terrain types is 70 % forest, 10 %
road, 10 % water and 10 % empty.  The generated array is saved to
``terrain_map.npy`` in the same folder.  You can run this script
directly to regenerate the terrain map.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np


def generate_map(size: int = 20, seed: int | None = None) -> np.ndarray:
    """Generate a random terrain map.

    Args:
        size: width and height of the square grid
        seed: optional random seed for reproducibility

    Returns:
        A ``size × size`` numpy array with integer terrain codes.
    """
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()
    # Probability distribution for terrain codes: [empty, forest, road, water]
    probs = [0.1, 0.7, 0.1, 0.1]
    # Corresponding terrain codes
    values = [0, 1, 2, 3]
    flat = rng.choice(values, size=size * size, p=probs)
    return flat.reshape((size, size)).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a terrain map for AURORA")
    parser.add_argument("--size", type=int, default=20, help="Grid side length (default: 20)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()
    terrain = generate_map(args.size, args.seed)
    output_path = Path(__file__).resolve().parent / "terrain_map.npy"
    np.save(output_path, terrain)
    print(f"Generated terrain map of shape {terrain.shape} and saved to {output_path}")


if __name__ == "__main__":
    main()