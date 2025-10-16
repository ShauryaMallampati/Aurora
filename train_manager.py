#!/usr/bin/env python3
"""
AURORA Training Manager - Simplified Training Execution

This script provides a simple interface to run training phases with proper
configuration, checkpointing, and evaluation.

Usage:
    python train_manager.py --mode ppo --phase quick
    python train_manager.py --mode hybrid --phase phase_a
    python train_manager.py --mode ppo --resume results/ppo_baseline/checkpoint_100000

Author: Shaurya Mallampati
Date: October 16, 2025
"""

import argparse
import yaml
from pathlib import Path
import sys
import subprocess
import json
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def load_phase_config(phase_name='phase_a'):
    """Load phase configuration from YAML."""
    config_path = Path(__file__).parent / 'configs' / 'training_phases.yaml'
    
    if not config_path.exists():
        print(f"⚠️  Config file not found: {config_path}")
        return None
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    if phase_name not in config:
        print(f"⚠️  Phase '{phase_name}' not found in config")
        print(f"Available phases: {', '.join(config.keys())}")
        return None
    
    return config[phase_name]


def run_ppo_training(phase_config, output_dir, resume_from=None):
    """Run PPO baseline training."""
    
    # Build command
    cmd = [
        sys.executable,
        'train_real_fire.py',
        '--timesteps', str(phase_config.get('env_steps', 100000)),
        '--n_envs', str(phase_config.get('num_envs', 4)),
        '--save_freq', str(phase_config.get('checkpoint', {}).get('save_every_steps', 5000)),
        '--eval_freq', str(phase_config.get('checkpoint', {}).get('eval_every_updates', 10) * 8192),
        '--output_dir', output_dir
    ]
    
    if resume_from:
        cmd.extend(['--resume', resume_from])
    
    print("\n" + "="*80)
    print("🚀 STARTING PPO BASELINE TRAINING")
    print("="*80)
    print(f"Command: {' '.join(cmd)}")
    print("="*80 + "\n")
    
    # Run training
    result = subprocess.run(cmd)
    
    return result.returncode == 0


def run_hybrid_training(phase_config, output_dir, resume_from=None):
    """Run Hybrid PPO+LLM training."""
    
    # Build command
    cmd = [
        sys.executable,
        'train_hybrid.py',
        '--timesteps', str(phase_config.get('env_steps', 100000)),
        '--n_envs', str(phase_config.get('num_envs', 4)),
        '--llm_backend', 'gemini',  # Use Gemini for speed
        '--llm_freq', str(phase_config.get('llm', {}).get('guidance_cadence', 50)),
        '--save_freq', str(phase_config.get('checkpoint', {}).get('save_every_steps', 5000)),
        '--eval_freq', str(phase_config.get('checkpoint', {}).get('eval_every_updates', 10) * 8192),
        '--output_dir', output_dir
    ]
    
    if resume_from:
        cmd.extend(['--resume', resume_from])
    
    print("\n" + "="*80)
    print("🚀 STARTING HYBRID PPO+LLM TRAINING")
    print("="*80)
    print(f"Command: {' '.join(cmd)}")
    print("="*80 + "\n")
    
    # Run training
    result = subprocess.run(cmd)
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='AURORA Training Manager')
    parser.add_argument('--mode', choices=['ppo', 'hybrid'], required=True,
                       help='Training mode: ppo or hybrid')
    parser.add_argument('--phase', default='phase_a',
                       help='Training phase from configs/training_phases.yaml')
    parser.add_argument('--output_dir', default=None,
                       help='Output directory (default: results/{mode}_{phase})')
    parser.add_argument('--resume', default=None,
                       help='Resume from checkpoint path')
    parser.add_argument('--dry_run', action='store_true',
                       help='Print config and exit without training')
    
    args = parser.parse_args()
    
    # Load phase config
    phase_config = load_phase_config(args.phase)
    if phase_config is None:
        return 1
    
    # Set output directory
    if args.output_dir is None:
        args.output_dir = f"results/{args.mode}_{args.phase}"
    
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save run metadata
    metadata = {
        'mode': args.mode,
        'phase': args.phase,
        'start_time': datetime.now().isoformat(),
        'config': phase_config,
        'output_dir': args.output_dir
    }
    
    metadata_path = output_path / 'run_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "="*80)
    print("📋 TRAINING CONFIGURATION")
    print("="*80)
    print(f"Mode: {args.mode}")
    print(f"Phase: {args.phase}")
    print(f"Output: {args.output_dir}")
    print(f"Steps: {phase_config.get('env_steps', 'N/A'):,}")
    print(f"Envs: {phase_config.get('num_envs', 4)}")
    if args.mode == 'hybrid':
        print(f"LLM Frequency: Every {phase_config.get('llm', {}).get('guidance_cadence', 50)} steps")
    print("="*80)
    
    if args.dry_run:
        print("\n✅ Dry run complete. Configuration saved to:", metadata_path)
        return 0
    
    # Run training
    if args.mode == 'ppo':
        success = run_ppo_training(phase_config, args.output_dir, args.resume)
    else:
        success = run_hybrid_training(phase_config, args.output_dir, args.resume)
    
    if success:
        # Update metadata with completion time
        metadata['end_time'] = datetime.now().isoformat()
        metadata['status'] = 'completed'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print("\n" + "="*80)
        print("✅ TRAINING COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"Output directory: {args.output_dir}")
        print(f"Metadata: {metadata_path}")
        print("="*80 + "\n")
        return 0
    else:
        print("\n" + "="*80)
        print("❌ TRAINING FAILED")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
