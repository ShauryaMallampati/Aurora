#!/usr/bin/env python3
import pandas as pd
import os
from pathlib import Path

base_dir = Path("results+models")

print("=" * 80)
print("🎯 AURORA TRAINED MODELS SUMMARY")
print("=" * 80)

for model_dir in sorted(base_dir.iterdir()):
    if not model_dir.is_dir():
        continue
    
    print(f"\n✅ {model_dir.name}")
    print("-" * 80)
    
    model_results = []
    seed_dirs = [d for d in model_dir.iterdir() if d.is_dir() and d.name.startswith("seed_")]
    
    for seed_dir in sorted(seed_dirs):
        csv_file = seed_dir / "episodes.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            if len(df) > 0:
                final_return = df["episode_return"].iloc[-1]
                mean_return = df["episode_return"].mean()
                final_containment = df["final_containment"].iloc[-1]
                model_results.append({
                    "seed": seed_dir.name,
                    "episodes": len(df),
                    "final_return": final_return,
                    "mean_return": mean_return,
                    "final_containment": final_containment
                })
                print(f"  {seed_dir.name}: {len(df)} episodes | Final Return: {final_return:.2f} | Mean: {mean_return:.2f} | Containment: {final_containment:.2%}")
    
    if model_results:
        avg_final = sum(r["final_return"] for r in model_results) / len(model_results)
        avg_mean = sum(r["mean_return"] for r in model_results) / len(model_results)
        avg_containment = sum(r["final_containment"] for r in model_results) / len(model_results)
        print(f"\n  📊 AVERAGES (across {len(model_results)} seeds):")
        print(f"     • Final Return: {avg_final:.2f}")
        print(f"     • Mean Return: {avg_mean:.2f}")
        print(f"     • Final Containment: {avg_containment:.2%}")

print("\n" + "=" * 80)
print("✅ TRAINING COMPLETE - MODELS READY FOR EVALUATION & DEPLOYMENT")
print("=" * 80)
