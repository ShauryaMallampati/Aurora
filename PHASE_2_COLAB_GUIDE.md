# 🚀 PHASE 2: PPO + HYBRID LLM TRAINING WITH GOOGLE COLAB

> **TL;DR:** Train both PPO baseline and Hybrid PPO+LLM models on Google Colab (free GPU), then download trained models to your Mac for demo/presentation.

---

## 📋 PHASE 2 Overview

| Task | Description | Effort | GPU Time |
|------|-------------|--------|----------|
| **2.1** | PPO Baseline (multi-seed) | 4-6h | 8-12h |
| **2.2** | Hybrid PPO+LLM (3 cadences) | 8-12h | 20-30h |
| **2.3** | Generate plots & analysis | 3-4h | 0h |
| **2.4** | Ablation studies | 6-8h | 15-20h |
| **TOTAL** | Full Phase 2 | ~24h | ~50h GPU |

---

## 🎯 Key Architecture Decisions

### Why Split Between Colab & Mac?

```
┌─────────────────────────────────────────────────────────────┐
│                      Training Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GOOGLE COLAB (Free GPU)              YOUR MAC              │
│  ├─ train_hybrid.py                   ├─ load & demo         │
│  ├─ train_ppo_baseline.py             ├─ generate plots      │
│  ├─ checkpoint save                   ├─ presentation        │
│  └─ upload to Drive                   └─ custom scenarios    │
│         ↓                                                    │
│  (Download as .zip)  ────────────────────→                  │
│         ↓                                                    │
│  results/aurora_hybrid_ppo_llm_model/                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why This Works:
- ✅ **Colab:** Unlimited free TPU/GPU (no cost, no setup)
- ✅ **More compute:** Use larger LLM models if needed (7B instead of 1.5B)
- ✅ **More steps:** Train on full 116K fires without time limit
- ✅ **Mac:** Run trained models instantly, no VRAM needed
- ✅ **Demo-ready:** Show judges live results from your laptop

---

## 🔧 Setup: Create Colab Notebook

### Step 1: Create New Colab Notebook

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. Click "New notebook"
3. Rename: `AURORA_Phase2_Hybrid_Training`

### Step 2: Mount Google Drive & Clone Repo

```python
# Cell 1: Mount Drive
from google.colab import drive
drive.mount('/content/drive')

# Cell 2: Clone repo (or upload as .zip)
import os
os.chdir('/content/drive/MyDrive')

# If you have Colab zip backup:
!unzip -q ISEF_AURORA_code.zip

# OR clone from GitHub:
!git clone https://github.com/ShauryaMallampati/aurora.git
os.chdir('/content/drive/MyDrive/aurora')  # or your cloned dir
```

### Step 3: Install Dependencies

```python
# Cell 3: Install AURORA dependencies
!pip install -q \
  stable-baselines3 \
  gymnasium \
  torch \
  transformers \
  accelerate \
  geopandas \
  shapely \
  rasterio \
  pandas \
  numpy \
  scipy \
  requests \
  sentencepiece

# Verify GPU
!nvidia-smi
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
print(f"GPU Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
```

---

## 🏃 Task 2.1: PPO Baseline Training (Multi-Seed)

### Objective
Train PPO **without** LLM to establish baseline. This is critical for comparison.

### Configuration
```python
config_ppo_baseline = {
    "model": "ppo",
    "timesteps": 401_408,  # Full 400K steps
    "n_envs": 4,           # More env workers on Colab GPU
    "num_drones": 3,
    "grid_size": 50,
    "llm_freq": 999_999,   # Effectively disable LLM
    "seeds": [42, 123, 456, 789, 1024]
}
```

### Colab Script: `train_ppo_baseline_colab.py`

Create this file in your Colab workspace:

```python
# train_ppo_baseline_colab.py
"""
PPO Baseline Training for AURORA (Colab-optimized)

Train PPO without LLM on all 116K real fires.
Outputs checkpoints every 40K steps for resuming.
"""

import sys
import os
from pathlib import Path
import json
import subprocess
from datetime import datetime

# Mount Google Drive for saving
DRIVE_PATH = Path('/content/drive/MyDrive/AURORA_Results')
DRIVE_PATH.mkdir(exist_ok=True)

def train_ppo_seed(seed: int, output_dir: Path):
    """Train PPO for single seed."""
    print(f"\n{'='*80}")
    print(f"🚀 TRAINING PPO SEED {seed}")
    print(f"{'='*80}\n")
    
    cmd = [
        "python", "train_hybrid.py",
        "--phase", "full",              # 400K steps
        "--timesteps", "401408",
        "--n_envs", "4",                # Colab can handle 4
        "--llm_freq", "999999",         # Disable LLM
        "--seed", str(seed),
        "--output_dir", str(output_dir / f"ppo_seed_{seed}"),
        "--save_freq", "40960",         # Save every 40K steps
        "--verbose", "1"
    ]
    
    # Run training
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0

def main():
    seeds = [42, 123, 456, 789, 1024]
    results = {}
    
    output_base = DRIVE_PATH / "ppo_baseline"
    output_base.mkdir(exist_ok=True)
    
    for seed in seeds:
        success = train_ppo_seed(seed, output_base)
        results[seed] = "✅ Success" if success else "❌ Failed"
        
        # Save progress after each seed
        with open(DRIVE_PATH / "ppo_training_progress.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": results,
                "seeds_completed": len([r for r in results.values() if "Success" in r])
            }, f, indent=2)
    
    print("\n" + "="*80)
    print("PPO BASELINE TRAINING COMPLETE")
    print("="*80)
    for seed, status in results.items():
        print(f"  Seed {seed}: {status}")
    
    return results

if __name__ == "__main__":
    main()
```

### Run in Colab Cell:

```python
# Cell 4: Run PPO training
os.chdir('/content/drive/MyDrive/aurora')  # Your repo dir
!python train_ppo_baseline_colab.py
```

### Expected Output:
```
================================================================================
🚀 TRAINING PPO SEED 42
================================================================================

🔥 AURORA ISEF 2025 - PPO BASELINE TRAINING
Phase: full (401,408 steps)
[Timestep 0/401408]
[Timestep 40960/401408] Episode Return: 45.23 | Area Saved: 1250 hectares
[Timestep 81920/401408] Episode Return: 47.85 | Area Saved: 1380 hectares
...
[Timestep 401408/401408] ✅ Training complete!
✅ Model saved to: results/ppo_baseline/ppo_seed_42/

✅ Progress saved: /content/drive/MyDrive/AURORA_Results/ppo_training_progress.json
```

---

## 🧠 Task 2.2: Hybrid PPO+LLM Training (3 Cadences)

### Objective
Train Hybrid model with **3 different LLM guidance frequencies**:
- **Cadence 25:** LLM every 25 steps (aggressive guidance)
- **Cadence 50:** LLM every 50 steps (balanced)
- **Cadence 100:** LLM every 100 steps (light guidance)

### Why 3 Cadences?
Studies show LLM frequency = speed vs quality tradeoff:
- **High freq (25):** More strategic guidance but slower training
- **Medium freq (50):** Sweet spot for ISEF
- **Low freq (100):** Fast but less strategic

### Configuration

```python
config_hybrid = {
    "model": "hybrid",
    "timesteps": 401_408,
    "n_envs": 4,
    "llm_model": "Qwen/Qwen2.5-7B-Instruct",  # Larger model on Colab
    "cadences": [25, 50, 100],
    "seeds": [42, 123, 456, 789, 1024]
}
```

### Colab Script: `train_hybrid_colab.py`

```python
# train_hybrid_colab.py
"""
Hybrid PPO+LLM Training for AURORA (Colab-optimized)

Train at 3 LLM cadences × 5 seeds = 15 training runs
Total: ~30 hours GPU time on Colab A100
"""

import sys
import os
from pathlib import Path
import json
import subprocess
from datetime import datetime
import itertools

# Mount Google Drive
DRIVE_PATH = Path('/content/drive/MyDrive/AURORA_Results')
DRIVE_PATH.mkdir(exist_ok=True)

def train_hybrid_config(cadence: int, seed: int, output_dir: Path):
    """Train Hybrid PPO+LLM for single config."""
    print(f"\n{'='*80}")
    print(f"🧠 TRAINING HYBRID PPO+LLM (Cadence={cadence}, Seed={seed})")
    print(f"{'='*80}\n")
    
    cmd = [
        "python", "train_hybrid.py",
        "--phase", "full",              # 400K steps
        "--timesteps", "401408",
        "--n_envs", "4",
        "--llm_model", "Qwen/Qwen2.5-7B-Instruct",  # Use 7B on Colab (not 1.5B)
        "--llm_freq", str(cadence),     # Guidance every N steps
        "--seed", str(seed),
        "--output_dir", str(output_dir / f"hybrid_cadence_{cadence}_seed_{seed}"),
        "--save_freq", "40960",
        "--verbose", "1"
    ]
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0

def main():
    cadences = [25, 50, 100]
    seeds = [42, 123, 456, 789, 1024]
    
    output_base = DRIVE_PATH / "hybrid_training"
    output_base.mkdir(exist_ok=True)
    
    results = {}
    total_configs = len(cadences) * len(seeds)
    completed = 0
    
    for cadence, seed in itertools.product(cadences, seeds):
        key = f"cadence_{cadence}_seed_{seed}"
        success = train_hybrid_config(cadence, seed, output_base)
        results[key] = "✅ Success" if success else "❌ Failed"
        completed += 1
        
        # Save progress
        progress = {
            "timestamp": datetime.now().isoformat(),
            "progress": f"{completed}/{total_configs}",
            "results": results
        }
        with open(DRIVE_PATH / "hybrid_training_progress.json", "w") as f:
            json.dump(progress, f, indent=2)
        
        print(f"\n📊 Progress: {completed}/{total_configs} ({100*completed/total_configs:.1f}%)")
    
    print("\n" + "="*80)
    print("HYBRID TRAINING COMPLETE")
    print("="*80)
    
    # Summary by cadence
    for cadence in cadences:
        cadence_results = [
            r for k, r in results.items() 
            if f"cadence_{cadence}" in k
        ]
        success_rate = sum(1 for r in cadence_results if "Success" in r) / len(cadence_results)
        print(f"  Cadence {cadence}: {success_rate*100:.0f}% success ({sum(1 for r in cadence_results if 'Success' in r)}/5 seeds)")

if __name__ == "__main__":
    main()
```

### Run in Colab:

```python
# Cell 5: Run Hybrid training (this will take ~24-30 hours)
os.chdir('/content/drive/MyDrive/aurora')
!python train_hybrid_colab.py

# Optional: Run in background with nohup
# !nohup python train_hybrid_colab.py > hybrid_training.log 2>&1 &
```

### Expected Progress:
```
================================================================================
🧠 TRAINING HYBRID PPO+LLM (Cadence=25, Seed=42)
================================================================================

Phase: full (401,408 steps)
[Timestep 0/401408]
[Timestep 25] 🧠 LLM Strategy: Priority zones [12,15], [40,45] | Cadence 25
[Timestep 50] 🧠 LLM Strategy: Retreat to recharge | Latency: 145ms
[Timestep 81920/401408] Episode Return: 52.34 | Area Saved: 1580 hectares
...
✅ Model saved: results/hybrid_training/hybrid_cadence_25_seed_42/

📊 Progress: 1/15 (6.7%)
```

---

## 📥 Task 2.3: Download Models to Mac

### On Colab (after training):

```python
# Cell 6: Prepare for download
import shutil
from google.colab import files

# Zip all results
!cd /content/drive/MyDrive/AURORA_Results && \
  zip -r aurora_results.zip ppo_baseline hybrid_training && \
  ls -lh aurora_results.zip

# Or selective download of best models:
!zip -r \
  best_models.zip \
  /content/drive/MyDrive/AURORA_Results/ppo_baseline/ppo_seed_42 \
  /content/drive/MyDrive/AURORA_Results/hybrid_training/hybrid_cadence_50_seed_42
```

### On Your Mac:

```bash
# Option 1: Download from Colab directly
# In Colab: from google.colab import files
# files.download('/content/drive/MyDrive/aurora_results.zip')

# Option 2: Download via rclone (faster for large files)
# Install rclone: brew install rclone
# rclone config create gdrive drive
# rclone copy gdrive:/path/to/AURORA_Results ~/Downloads/aurora_models

# Option 3: Manual via Google Drive
# 1. Open Google Drive
# 2. Find "AURORA_Results" folder
# 3. Right-click → Download as ZIP
# 4. Extract to: ~/Desktop/ISEF/results/

# Verify models on Mac
ls -lh ~/Desktop/ISEF/results/ppo_baseline/ppo_seed_42/
ls -lh ~/Desktop/ISEF/results/hybrid_training/hybrid_cadence_50_seed_42/
```

---

## 📊 Task 2.4: Analysis & Metrics on Mac

### After downloading, run on Mac:

```bash
# Set up environment
cd ~/Desktop/ISEF
python -m venv venv_analysis
source venv_analysis/bin/activate
pip install -r requirements.txt

# Generate evaluation metrics
python generate_evaluation_metrics_simple.py \
  --ppo_dir results/ppo_baseline \
  --hybrid_dir results/hybrid_training \
  --output results/eval_metrics_full.csv

# Generate plots
python generate_plots.py \
  --metrics_csv results/eval_metrics_full.csv \
  --output_dir aurora-web/public/charts/
```

---

## 📈 Expected Results

After Phase 2, you should have:

### PPO Baseline Results
```
Seed | Mean Return | Area Saved (ha) | Containment Time | Success Rate
-----|-------------|-----------------|------------------|-------------
42   | 45.2 ± 3.1  | 1250 ± 85       | 78 ± 5 steps     | 85%
123  | 44.8 ± 2.9  | 1240 ± 78       | 79 ± 6 steps     | 83%
456  | 46.1 ± 3.4  | 1280 ± 92       | 76 ± 4 steps     | 87%
789  | 45.5 ± 3.0  | 1265 ± 88       | 77 ± 5 steps     | 86%
1024 | 44.9 ± 2.8  | 1235 ± 75       | 80 ± 7 steps     | 82%
-----|-------------|-----------------|------------------|-------------
Mean | 45.3 ± 1.4  | 1254 ± 18       | 78 ± 1.5 steps   | 84.6%
```

### Hybrid Results (Best Cadence)
```
Cadence | Mean Return | Area Saved (ha) | Improvement | LLM Latency
--------|-------------|-----------------|-------------|-------------
25      | 51.8 ± 3.2  | 1420 ± 95      | +14.3%      | 245ms
50      | 51.2 ± 3.1  | 1410 ± 92      | +12.8%      | 125ms
100     | 50.1 ± 3.0  | 1380 ± 88      | +10.0%      | 65ms
∞ (PPO) | 45.3 ± 1.4  | 1254 ± 18      | -            | 0ms
```

---

## 🔄 Handling Training Interruptions

### If Colab times out (>12 hours):

```python
# Cell: Resume from checkpoint
cmd = [
    "python", "train_hybrid.py",
    "--phase", "full",
    "--resume",  # Auto-finds latest checkpoint
    "--output_dir", "results/hybrid_training/hybrid_cadence_50_seed_42"
]
subprocess.run(cmd)
```

### If internet drops:

```python
# Save checkpoint to Google Drive regularly
import shutil
checkpoint_dir = Path('/content/drive/MyDrive/AURORA_Checkpoints')
checkpoint_dir.mkdir(exist_ok=True)

# After each 40K steps, copy checkpoint
!cp -r results/checkpoints/latest/* /content/drive/MyDrive/AURORA_Checkpoints/
```

---

## 🎯 Success Criteria

✅ **Phase 2 Complete when:**

1. **PPO Baseline:** 5 seeds × 400K steps completed
2. **Hybrid Training:** 3 cadences × 5 seeds = 15 configs completed
3. **Models Downloaded:** All trained models on Mac
4. **Metrics Generated:** `eval_metrics_full.csv` with all results
5. **Plots Created:** 4 publication-quality plots saved
6. **Ablations Done:** 3 ablation studies results documented

---

## 📝 Troubleshooting

| Problem | Solution |
|---------|----------|
| Out of memory on Colab | Reduce `n_envs` to 2, use smaller LLM (1.5B) |
| Colab session timeout | Use nohup or background training |
| Models won't load on Mac | Check PyTorch version matches |
| LLM crashes | Fallback to heuristic strategy (automatic) |
| Training too slow | Increase `n_envs` to 8 (if GPU permits) |

---

## 🚀 Next Steps (After Phase 2)

- [ ] Phase 3: Neural World Model (optional but powerful)
- [ ] Phase 4: Web demo integration
- [ ] Prepare judges guide with metrics
- [ ] Record video demo
- [ ] Create presentation slides

---

**Version:** 1.0  
**Last Updated:** November 2, 2025  
**Status:** Ready to Execute
