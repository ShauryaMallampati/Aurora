#!/usr/bin/env python3
"""
Download & Setup Phase 2 Models from Google Colab to Mac

This script helps you:
1. Download trained models from Google Drive
2. Verify model integrity
3. Generate evaluation metrics CSV
4. Create publication-quality plots

Usage:
    python setup_phase2_models.py [--drive_path "path/to/AURORA_Results"]

Author: Shaurya Mallampati
Date: November 2, 2025
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

def check_rclone_installed():
    """Check if rclone is installed for Google Drive access."""
    try:
        subprocess.run(['rclone', '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def setup_rclone():
    """Setup rclone for Google Drive access."""
    print("\n" + "="*80)
    print("🔗 SETTING UP RCLONE FOR GOOGLE DRIVE ACCESS")
    print("="*80 + "\n")
    
    print("Rclone is not installed. Install with:")
    print("  brew install rclone\n")
    
    print("Then configure Google Drive:")
    print("  rclone config create gdrive drive\n")
    
    print("Follow prompts (use web authentication when asked)\n")
    
    return False

def download_models_rclone(drive_remote: str = "gdrive", 
                          remote_path: str = "AURORA_Results",
                          local_path: str = "results"):
    """Download models from Google Drive using rclone."""
    
    print(f"\n📥 Downloading from Google Drive...")
    print(f"  Remote: {drive_remote}:{remote_path}")
    print(f"  Local: {local_path}\n")
    
    try:
        cmd = [
            'rclone', 'copy',
            f'{drive_remote}:{remote_path}',
            local_path,
            '--progress',
            '--exclude', '*.pyc',
            '--exclude', '__pycache__'
        ]
        
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def download_models_manual(manual_path: str):
    """Use manually downloaded ZIP file."""
    
    manual_path = Path(manual_path)
    
    if not manual_path.exists():
        print(f"❌ File not found: {manual_path}")
        return False
    
    print(f"\n📦 Extracting ZIP: {manual_path}")
    
    try:
        import zipfile
        with zipfile.ZipFile(manual_path, 'r') as zip_ref:
            zip_ref.extractall('results')
        
        print("✅ Extraction complete!")
        return True
    except Exception as e:
        print(f"❌ Error extracting: {e}")
        return False

def verify_models(results_dir: str = "results"):
    """Verify downloaded models are complete."""
    
    results_path = Path(results_dir)
    
    print("\n" + "="*80)
    print("🔍 VERIFYING MODEL STRUCTURE")
    print("="*80 + "\n")
    
    # Check for required directories
    ppo_dir = results_path / "ppo_baseline"
    hybrid_dir = results_path / "hybrid_training"
    
    errors = []
    
    if ppo_dir.exists():
        ppo_seeds = list(ppo_dir.glob("ppo_seed_*"))
        print(f"✅ PPO baseline: {len(ppo_seeds)} seeds found")
        
        for seed_dir in ppo_seeds:
            if not (seed_dir / "best_model.zip").exists():
                errors.append(f"Missing best_model.zip in {seed_dir}")
    else:
        print("❌ PPO baseline directory not found")
        errors.append("Missing ppo_baseline directory")
    
    if hybrid_dir.exists():
        hybrid_configs = list(hybrid_dir.glob("hybrid_cadence_*_seed_*"))
        print(f"✅ Hybrid training: {len(hybrid_configs)} configs found")
        
        # Count by cadence
        for cadence in [25, 50, 100]:
            cadence_dirs = [d for d in hybrid_configs if f"cadence_{cadence}" in d.name]
            print(f"   Cadence {cadence}: {len(cadence_dirs)} seeds")
            
            for cfg_dir in cadence_dirs:
                if not (cfg_dir / "best_model.zip").exists():
                    errors.append(f"Missing best_model.zip in {cfg_dir}")
    else:
        print("❌ Hybrid training directory not found")
        errors.append("Missing hybrid_training directory")
    
    print()
    
    if errors:
        print("⚠️  Issues found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ All models verified successfully!")
        return True

def load_model_metadata(model_path: Path) -> dict:
    """Load metadata from model directory."""
    
    metadata_path = model_path / "metadata.json"
    
    if metadata_path.exists():
        try:
            with open(metadata_path) as f:
                return json.load(f)
        except:
            pass
    
    # Fallback: estimate from path
    name = model_path.name
    if "cadence" in name and "seed" in name:
        parts = name.split("_")
        return {
            "model": "hybrid",
            "cadence": int(parts[1]),
            "seed": int(parts[3])
        }
    elif "ppo" in name and "seed" in name:
        seed = int(name.split("_")[-1])
        return {
            "model": "ppo",
            "seed": seed
        }
    
    return {}

def generate_models_manifest(results_dir: str = "results") -> dict:
    """Generate manifest of all trained models."""
    
    results_path = Path(results_dir)
    manifest = {
        "generated": datetime.now().isoformat(),
        "ppo_baseline": [],
        "hybrid_training": {}
    }
    
    # Collect PPO models
    ppo_dir = results_path / "ppo_baseline"
    if ppo_dir.exists():
        for seed_dir in sorted(ppo_dir.glob("ppo_seed_*")):
            metadata = load_model_metadata(seed_dir)
            metadata["path"] = str(seed_dir.relative_to(results_path))
            metadata["model_file"] = str((seed_dir / "best_model.zip").relative_to(results_path))
            manifest["ppo_baseline"].append(metadata)
    
    # Collect Hybrid models
    hybrid_dir = results_path / "hybrid_training"
    if hybrid_dir.exists():
        for cfg_dir in sorted(hybrid_dir.glob("hybrid_cadence_*_seed_*")):
            metadata = load_model_metadata(cfg_dir)
            metadata["path"] = str(cfg_dir.relative_to(results_path))
            metadata["model_file"] = str((cfg_dir / "best_model.zip").relative_to(results_path))
            
            cadence = metadata.get("cadence")
            if cadence not in manifest["hybrid_training"]:
                manifest["hybrid_training"][cadence] = []
            
            manifest["hybrid_training"][cadence].append(metadata)
    
    return manifest

def print_models_summary(manifest: dict):
    """Print summary of downloaded models."""
    
    print("\n" + "="*80)
    print("📊 DOWNLOADED MODELS SUMMARY")
    print("="*80 + "\n")
    
    # PPO summary
    ppo_models = manifest["ppo_baseline"]
    if ppo_models:
        print(f"✅ PPO Baseline: {len(ppo_models)} models")
        for model in ppo_models:
            seed = model.get("seed", "unknown")
            print(f"   - Seed {seed}: {model.get('path')}")
    
    # Hybrid summary
    hybrid_models = manifest["hybrid_training"]
    if hybrid_models:
        total_hybrid = sum(len(m) for m in hybrid_models.values())
        print(f"\n✅ Hybrid PPO+LLM: {total_hybrid} models")
        for cadence in sorted(hybrid_models.keys()):
            models = hybrid_models[cadence]
            print(f"   Cadence {cadence}: {len(models)} seeds")
            for model in models:
                seed = model.get("seed", "unknown")
                print(f"     - Seed {seed}")
    
    print("\n" + "="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description='Setup Phase 2 models from Google Colab to Mac'
    )
    parser.add_argument('--download-method', 
                       choices=['rclone', 'manual', 'skip'],
                       default='skip',
                       help='Download method (default: skip if files exist)')
    parser.add_argument('--manual-zip', type=str, default=None,
                       help='Path to manually downloaded ZIP file')
    parser.add_argument('--drive-remote', type=str, default='gdrive',
                       help='Rclone remote name for Google Drive')
    parser.add_argument('--drive-path', type=str, default='AURORA_Results',
                       help='Path in Google Drive')
    parser.add_argument('--output-dir', type=str, default='results',
                       help='Local output directory')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "="*80)
    print("📱 PHASE 2 MODEL SETUP: COLAB → MAC")
    print("="*80)
    
    # Check if download needed
    ppo_exists = (output_dir / "ppo_baseline").exists()
    hybrid_exists = (output_dir / "hybrid_training").exists()
    
    if ppo_exists and hybrid_exists and args.download_method == 'skip':
        print("\n✅ Models already exist locally, skipping download")
    else:
        # Download if needed
        if args.download_method == 'manual' and args.manual_zip:
            success = download_models_manual(args.manual_zip)
        elif args.download_method == 'rclone':
            if not check_rclone_installed():
                setup_rclone()
                return False
            success = download_models_rclone(
                args.drive_remote, args.drive_path, str(output_dir)
            )
        else:
            print("\n⚠️  No download method specified")
            print("  Use --download-method rclone|manual")
            print("  Or download manually from Google Drive")
            success = True
        
        if not success and args.download_method != 'skip':
            return False
    
    # Verify models
    if not verify_models(str(output_dir)):
        print("\n⚠️  Some models are missing. Please download manually.")
        return False
    
    # Generate manifest
    manifest = generate_models_manifest(str(output_dir))
    
    # Save manifest
    manifest_path = output_dir / "models_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Manifest saved to: {manifest_path}")
    
    # Print summary
    print_models_summary(manifest)
    
    # Next steps
    print("\n" + "="*80)
    print("📋 NEXT STEPS")
    print("="*80)
    print("""
1. Generate evaluation metrics:
   python generate_evaluation_metrics_simple.py \\
     --ppo_dir results/ppo_baseline \\
     --hybrid_dir results/hybrid_training \\
     --output results/eval_metrics_full.csv

2. Create plots:
   python generate_plots.py \\
     --metrics_csv results/eval_metrics_full.csv \\
     --output_dir aurora-web/public/charts/

3. Run web demo:
   cd aurora-web && npm run dev

4. Create presentation materials:
   python demo_hybrid_model.py \\
     --model_path results/hybrid_training/hybrid_cadence_50_seed_42/best_model.zip
    """)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
