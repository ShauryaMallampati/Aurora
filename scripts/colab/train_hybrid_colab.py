#!/usr/bin/env python3
"""
Hybrid PPO+LLM Training for AURORA (Colab-optimized)

Train at 3 LLM guidance cadences × 5 seeds = 15 training runs
- Cadence 25: LLM every 25 steps (aggressive)
- Cadence 50: LLM every 50 steps (balanced)
- Cadence 100: LLM every 100 steps (conservative)

Total estimated time: ~30 hours on Colab A100 GPU

Usage:
    python train_hybrid_colab.py [--cadences 25,50,100] [--seeds 42,123]

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
import itertools

# Try to detect if running in Colab
try:
    from google.colab import drive
    IS_COLAB = True
    DRIVE_PATH = Path('/content/drive/MyDrive/AURORA_Results')
except ImportError:
    IS_COLAB = False
    DRIVE_PATH = Path('results')

DRIVE_PATH.mkdir(exist_ok=True, parents=True)


def train_hybrid_config(cadence: int, seed: int, output_dir: Path, 
                       timesteps: int = 401_408, 
                       n_envs: int = 4,
                       llm_model: str = "Qwen/Qwen2.5-7B-Instruct"):
    """Train Hybrid PPO+LLM for single config.
    
    Args:
        cadence: Steps between LLM guidance requests
        seed: Random seed
        output_dir: Output directory for model
        timesteps: Total training steps
        n_envs: Number of parallel environments
        llm_model: LLM model ID from HuggingFace
    
    Returns:
        bool: True if training succeeded
    """
    print(f"\n{'='*80}")
    print(f"🧠 TRAINING HYBRID PPO+LLM")
    print(f"{'='*80}")
    print(f"  Cadence: Every {cadence} steps")
    print(f"  Seed: {seed}")
    print(f"  Timesteps: {timesteps:,}")
    print(f"  LLM Model: {llm_model}")
    print(f"  Parallel Envs: {n_envs}")
    print(f"  Output: {output_dir}")
    print(f"{'='*80}\n")
    
    output_dir.mkdir(exist_ok=True, parents=True)
    
    cmd = [
        sys.executable, "train_hybrid.py",
        "--phase", "full",
        "--timesteps", str(timesteps),
        "--n_envs", str(n_envs),
        "--llm_model", llm_model,
        "--llm_freq", str(cadence),
        "--seed", str(seed),
        "--output_dir", str(output_dir),
        "--save_freq", "40960",       # Save every 40K steps
        "--verbose", "1"
    ]
    
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        success = result.returncode == 0
        
        if success:
            print(f"\n✅ Cadence {cadence} Seed {seed} training completed!")
        else:
            print(f"\n❌ Cadence {cadence} Seed {seed} failed with code {result.returncode}")
        
        return success
    except Exception as e:
        print(f"\n❌ Error training cadence {cadence} seed {seed}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Train Hybrid PPO+LLM on AURORA (Colab-optimized)'
    )
    parser.add_argument('--cadences', type=str, default='25,50,100',
                       help='Comma-separated LLM guidance cadences')
    parser.add_argument('--seeds', type=str, default='42,123,456,789,1024',
                       help='Comma-separated list of random seeds')
    parser.add_argument('--timesteps', type=int, default=401_408,
                       help='Total training timesteps (default: 400K)')
    parser.add_argument('--n_envs', type=int, default=4,
                       help='Number of parallel environments (default: 4 for Colab)')
    parser.add_argument('--llm_model', type=str, default='Qwen/Qwen2.5-7B-Instruct',
                       help='LLM model ID (use 7B on Colab, 1.5B on Mac)')
    parser.add_argument('--output_dir', type=str, default=None,
                       help='Output directory (default: DRIVE_PATH/hybrid_training)')
    
    args = parser.parse_args()
    
    # Parse cadences and seeds
    cadences = [int(c.strip()) for c in args.cadences.split(',')]
    seeds = [int(s.strip()) for s in args.seeds.split(',')]
    
    # Set output directory
    if args.output_dir:
        output_base = Path(args.output_dir)
    else:
        output_base = DRIVE_PATH / "hybrid_training"
    
    output_base.mkdir(exist_ok=True, parents=True)
    
    # Training metadata
    metadata = {
        "timestamp_start": datetime.now().isoformat(),
        "model": "hybrid_ppo_llm",
        "timesteps": args.timesteps,
        "n_envs": args.n_envs,
        "cadences": cadences,
        "seeds": seeds,
        "llm_model": args.llm_model,
        "status": "in_progress"
    }
    
    # Save initial metadata
    metadata_path = output_base / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "="*80)
    print("🧠 HYBRID PPO+LLM TRAINING - MULTI-CADENCE & MULTI-SEED")
    print("="*80)
    print(f"Total Timesteps: {args.timesteps:,}")
    print(f"LLM Model: {args.llm_model}")
    print(f"LLM Cadences: {cadences}")
    print(f"Random Seeds: {seeds}")
    print(f"Total Configs: {len(cadences)} cadences × {len(seeds)} seeds = {len(cadences)*len(seeds)} runs")
    print(f"Estimated GPU Time: ~{len(cadences)*len(seeds)*2} hours on A100")
    print(f"Output Directory: {output_base}")
    print(f"Mode: {'Google Colab' if IS_COLAB else 'Local'}")
    print("="*80 + "\n")
    
    results = {}
    total_configs = len(cadences) * len(seeds)
    completed = 0
    failed = 0
    
    # Train all configs (cadence × seed combinations)
    for cadence, seed in itertools.product(cadences, seeds):
        config_key = f"cadence_{cadence}_seed_{seed}"
        config_number = len(results) + 1
        
        print(f"\n[{config_number}/{total_configs}] Training {config_key}...")
        
        seed_output_dir = output_base / config_key
        success = train_hybrid_config(
            cadence=cadence,
            seed=seed,
            output_dir=seed_output_dir,
            timesteps=args.timesteps,
            n_envs=args.n_envs,
            llm_model=args.llm_model
        )
        
        results[config_key] = {
            "cadence": cadence,
            "seed": seed,
            "status": "✅ Success" if success else "❌ Failed",
            "output_dir": str(seed_output_dir),
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            completed += 1
        else:
            failed += 1
        
        # Save progress after each config
        progress = {
            "timestamp": datetime.now().isoformat(),
            "progress": f"{completed}/{total_configs}",
            "completion_percent": 100 * completed / total_configs,
            "configs_completed": completed,
            "configs_failed": failed,
            "results": results
        }
        
        progress_path = output_base / "training_progress.json"
        with open(progress_path, "w") as f:
            json.dump(progress, f, indent=2)
        
        percent_complete = 100 * completed / total_configs
        print(f"\n📊 Progress: {completed}/{total_configs} ({percent_complete:.1f}% complete, {failed} failed)")
    
    # Summary by cadence
    print("\n" + "="*80)
    print("✅ HYBRID TRAINING COMPLETE")
    print("="*80)
    print(f"\nResults by Cadence:\n")
    
    for cadence in cadences:
        cadence_results = {
            k: v for k, v in results.items() 
            if v["cadence"] == cadence
        }
        success_count = sum(1 for r in cadence_results.values() if "Success" in r["status"])
        total = len(cadence_results)
        
        print(f"  Cadence {cadence:3d}: {success_count}/{total} seeds successful")
        for config_key in sorted(cadence_results.keys()):
            status = cadence_results[config_key]["status"]
            print(f"    {config_key}: {status}")
    
    print(f"\nOverall: {completed}/{total_configs} configs successful ({100*completed/total_configs:.1f}%)")
    
    # Update final metadata
    metadata["timestamp_end"] = datetime.now().isoformat()
    metadata["status"] = "completed" if failed == 0 else "partial"
    metadata["configs_successful"] = completed
    metadata["configs_failed"] = failed
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n📍 Results saved to: {output_base}")
    print(f"📍 Metadata saved to: {metadata_path}")
    print(f"📍 Progress saved to: {output_base / 'training_progress.json'}")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
