#!/usr/bin/env python3
"""
PPO Baseline Training for AURORA (Colab-optimized)

Train PPO without LLM on all 116K real fires.
Outputs checkpoints every 40K steps for resuming.
Saves progress to Google Drive for monitoring.

Usage:
    python train_ppo_baseline_colab.py [--seeds 42,123,456] [--timesteps 401408]

Author: Shaurya Mallampati
Date: November 2, 2025
"""

import sys
import os
from pathlib import Path
import json
import subprocess
from datetime import datetime
import argparse

# Try to detect if running in Colab
try:
    from google.colab import drive
    IS_COLAB = True
    DRIVE_PATH = Path('/content/drive/MyDrive/AURORA_Results')
except ImportError:
    IS_COLAB = False
    DRIVE_PATH = Path('results')

DRIVE_PATH.mkdir(exist_ok=True, parents=True)

def train_ppo_seed(seed: int, timesteps: int, output_dir: Path, n_envs: int = 4):
    """Train PPO for single seed.
    
    Args:
        seed: Random seed
        timesteps: Total training steps
        output_dir: Output directory for model
        n_envs: Number of parallel environments (4 for Colab, 2 for Mac)
    
    Returns:
        bool: True if training succeeded
    """
    print(f"\n{'='*80}")
    print(f"🚀 TRAINING PPO BASELINE SEED {seed}")
    print(f"{'='*80}")
    print(f"  Timesteps: {timesteps:,}")
    print(f"  Parallel Envs: {n_envs}")
    print(f"  LLM Disabled: True (cadence=999999)")
    print(f"  Output: {output_dir}")
    print(f"{'='*80}\n")
    
    output_dir.mkdir(exist_ok=True, parents=True)
    
    cmd = [
        sys.executable, "train_hybrid.py",
        "--phase", "full",
        "--timesteps", str(timesteps),
        "--n_envs", str(n_envs),
        "--llm_freq", "999999",           # Disable LLM
        "--seed", str(seed),
        "--output_dir", str(output_dir),
        "--save_freq", "40960",           # Save every 40K steps
        "--verbose", "1"
    ]
    
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        success = result.returncode == 0
        
        if success:
            print(f"\n✅ Seed {seed} training completed successfully!")
        else:
            print(f"\n❌ Seed {seed} training failed with code {result.returncode}")
        
        return success
    except Exception as e:
        print(f"\n❌ Error training seed {seed}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Train PPO baseline on AURORA (Colab-optimized)'
    )
    parser.add_argument('--seeds', type=str, default='42,123,456,789,1024',
                       help='Comma-separated list of seeds to train')
    parser.add_argument('--timesteps', type=int, default=401_408,
                       help='Total training timesteps (default: 400K)')
    parser.add_argument('--n_envs', type=int, default=4,
                       help='Number of parallel environments (default: 4 for Colab)')
    parser.add_argument('--output_dir', type=str, default=None,
                       help='Output directory (default: DRIVE_PATH/ppo_baseline)')
    
    args = parser.parse_args()
    
    # Parse seeds
    seeds = [int(s.strip()) for s in args.seeds.split(',')]
    
    # Set output directory
    if args.output_dir:
        output_base = Path(args.output_dir)
    else:
        output_base = DRIVE_PATH / "ppo_baseline"
    
    output_base.mkdir(exist_ok=True, parents=True)
    
    # Training metadata
    metadata = {
        "timestamp_start": datetime.now().isoformat(),
        "model": "ppo_baseline",
        "timesteps": args.timesteps,
        "n_envs": args.n_envs,
        "seeds": seeds,
        "llm_enabled": False,
        "status": "in_progress"
    }
    
    # Save initial metadata
    metadata_path = output_base / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "="*80)
    print("🏃 PPO BASELINE TRAINING - MULTI-SEED")
    print("="*80)
    print(f"Total Timesteps: {args.timesteps:,}")
    print(f"Parallel Envs: {args.n_envs}")
    print(f"Seeds: {seeds}")
    print(f"Output Directory: {output_base}")
    print(f"Mode: {'Google Colab' if IS_COLAB else 'Local'}")
    print("="*80 + "\n")
    
    results = {}
    total_seeds = len(seeds)
    completed = 0
    
    for i, seed in enumerate(seeds, 1):
        print(f"\n[{i}/{total_seeds}] Training Seed {seed}...")
        
        seed_output_dir = output_base / f"ppo_seed_{seed}"
        success = train_ppo_seed(
            seed=seed,
            timesteps=args.timesteps,
            output_dir=seed_output_dir,
            n_envs=args.n_envs
        )
        
        results[seed] = {
            "status": "✅ Success" if success else "❌ Failed",
            "output_dir": str(seed_output_dir),
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            completed += 1
        
        # Save progress after each seed
        progress = {
            "timestamp": datetime.now().isoformat(),
            "progress": f"{completed}/{total_seeds}",
            "completion_percent": 100 * completed / total_seeds,
            "results": results,
            "seeds_completed": completed,
            "seeds_failed": i - completed
        }
        
        progress_path = output_base / "training_progress.json"
        with open(progress_path, "w") as f:
            json.dump(progress, f, indent=2)
        
        print(f"\n📊 Progress: {completed}/{total_seeds} ({100*completed/total_seeds:.1f}% complete)")
    
    # Final summary
    print("\n" + "="*80)
    print("✅ PPO BASELINE TRAINING COMPLETE")
    print("="*80)
    
    success_count = sum(1 for r in results.values() if "Success" in r["status"])
    print(f"\nResults: {success_count}/{total_seeds} seeds successful\n")
    
    for seed in seeds:
        print(f"  Seed {seed}: {results[seed]['status']}")
    
    # Update final metadata
    metadata["timestamp_end"] = datetime.now().isoformat()
    metadata["status"] = "completed" if success_count == total_seeds else "partial"
    metadata["seeds_successful"] = success_count
    metadata["seeds_failed"] = total_seeds - success_count
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n📍 Results saved to: {output_base}")
    print(f"📍 Metadata saved to: {metadata_path}")
    print(f"📍 Progress saved to: {output_base / 'training_progress.json'}")
    
    return success_count == total_seeds


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
