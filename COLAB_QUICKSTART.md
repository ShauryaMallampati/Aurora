# 📱 QUICK START: COLAB TO MAC WORKFLOW

**Goal:** Run Phase 2 training on Google Colab's free GPU, then download trained models to Mac.

---

## 🚀 5-Step Quick Start

### Step 1: Prepare Your Code for Colab (5 min)

```bash
# On your Mac, create a ZIP backup of your repo
cd ~/Desktop/ISEF
zip -r ISEF_AURORA_code.zip \
  --exclude='logs/*' '*.pyc' '__pycache__' '.git' \
  .

# Move to Google Drive folder (if you have one synced locally)
# OR just remember the path to upload manually
```

### Step 2: Open Colab & Mount Drive (10 min)

1. Go to **[colab.research.google.com](https://colab.research.google.com)**
2. Click **"New notebook"**
3. Rename: `AURORA_Phase2_Training`
4. Run this cell:

```python
# Cell 1: Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Verify
import os
os.listdir('/content/drive/MyDrive')
```

### Step 3: Upload Code or Clone (10 min)

**Option A: Upload ZIP** (simplest)
```python
# Cell 2: Upload your code
from google.colab import files
uploaded = files.upload()  # Select ISEF_AURORA_code.zip

import zipfile
with zipfile.ZipFile('/content/ISEF_AURORA_code.zip', 'r') as zip_ref:
    zip_ref.extractall('/content/ISEF')

os.chdir('/content/ISEF')
```

**Option B: Clone from GitHub**
```python
# Cell 2: Clone repo
!git clone https://github.com/ShauryaMallampati/aurora.git /content/ISEF
os.chdir('/content/ISEF')
```

### Step 4: Install Dependencies (15 min)

```python
# Cell 3: Install packages
!pip install -q \
  stable-baselines3 gymnasium torch transformers accelerate \
  geopandas shapely rasterio pandas numpy scipy requests sentencepiece

# Verify GPU
!nvidia-smi
import torch
print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
```

### Step 5: Start Training! (varies)

```python
# Cell 4: Train PPO baseline
os.chdir('/content/ISEF')
!python train_ppo_baseline_colab.py \
  --seeds 42,123,456,789,1024 \
  --timesteps 401408 \
  --n_envs 4 \
  --output_dir /content/drive/MyDrive/AURORA_Results/ppo_baseline
```

Or for hybrid training:

```python
# Cell 5: Train Hybrid (this takes 24-30 hours)
!python train_hybrid_colab.py \
  --cadences 25,50,100 \
  --seeds 42,123,456,789,1024 \
  --timesteps 401408 \
  --n_envs 4 \
  --llm_model "Qwen/Qwen2.5-7B-Instruct" \
  --output_dir /content/drive/MyDrive/AURORA_Results/hybrid_training
```

---

## 📊 Monitor Training Progress

**In Colab (while running):**
```python
# Check latest results
import json
progress_file = '/content/drive/MyDrive/AURORA_Results/ppo_baseline/training_progress.json'
with open(progress_file) as f:
    progress = json.load(f)
print(f"Progress: {progress['progress']}")
print(f"Completion: {progress['completion_percent']:.1f}%")
```

**From your Mac (via Google Drive):**
1. Open Google Drive → AURORA_Results folder
2. Look for `training_progress.json`
3. Open it to see real-time progress

---

## 📥 Download Models to Mac

**After training completes:**

```python
# Cell: Prepare download (in Colab)
import os
import shutil

# Zip results for download
os.chdir('/content/drive/MyDrive')
!zip -r aurora_results_complete.zip AURORA_Results/

# Show file size
!ls -lh aurora_results_complete.zip
```

**On your Mac:**
```bash
# Download from Google Drive (via web interface or rclone)
# Option 1: Manual download from Drive UI
# Option 2: Use rclone (if installed)
#   brew install rclone
#   rclone config create gdrive drive
#   rclone copy gdrive:AURORA_Results ~/Desktop/ISEF/results/

# Verify models are there
ls -lh ~/Desktop/ISEF/results/ppo_baseline/ppo_seed_42/

# Expected structure:
# results/
# ├── ppo_baseline/
# │   ├── ppo_seed_42/
# │   │   ├── best_model.zip
# │   │   └── ...
# │   ├── ppo_seed_123/
# │   └── ...
# └── hybrid_training/
#     ├── hybrid_cadence_25_seed_42/
#     └── ...
```

---

## 🔄 Resume Training if Interrupted

```python
# In Colab, if training gets interrupted:

# Cell: Resume PPO
!python train_ppo_baseline_colab.py \
  --resume  # Auto-finds latest checkpoint
```

Or manually find last checkpoint:
```python
# Check what's been trained
import json
progress_file = '/content/drive/MyDrive/AURORA_Results/ppo_baseline/training_progress.json'
with open(progress_file) as f:
    results = json.load(f)
print(results)
```

---

## 💾 Disk Space Management

**Colab storage limits:**
- Session disk: 108 GB (deleted when session ends)
- Drive storage: Depends on your Google Drive account

**To manage space:**
```python
# Check current usage
!du -sh /content/drive/MyDrive/AURORA_Results/

# Delete old checkpoints to free space
!rm -rf /content/drive/MyDrive/AURORA_Results/ppo_baseline/ppo_seed_42/checkpoints/

# Keep only best model
!rm -rf /content/drive/MyDrive/AURORA_Results/ppo_baseline/ppo_seed_42/logs/
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named 'gym'" | Run: `!pip install gymnasium` |
| "Out of memory" | Reduce n_envs to 2, or split training |
| "CUDA out of memory" | Same as above, or use smaller LLM (1.5B) |
| "File not found" | Check path is correct with `!ls -la /path/` |
| "Training too slow" | Increase n_envs if GPU has space |
| "Colab session timeout" | Use nohup: `!nohup python ... > train.log 2>&1 &` |

---

## ✅ Expected Timing

| Task | Time |
|------|------|
| Upload code | 5-10 min |
| Install dependencies | 10-15 min |
| PPO training (5 seeds) | 8-12 hours |
| Hybrid training (15 configs) | 24-30 hours |
| Download results | 5-30 min |

**Total: ~36-48 hours across ~3-4 Colab sessions**

---

## 📋 Colab Tips & Tricks

### Keep Colab session alive (optional)
```python
# Run this in a cell to prevent timeout
from IPython.display import clear_output
import time

for i in range(1000):  # Run for ~10 hours
    print(f"Keep-alive ping {i}")
    time.sleep(30)  # Ping every 30 seconds
    clear_output(wait=True)
```

### Background training (advanced)
```python
# Train in background while working on other things
import subprocess

# Start training in background
proc = subprocess.Popen([
    'python', 'train_ppo_baseline_colab.py',
    '--n_envs', '4'
], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print(f"Training process started with PID {proc.pid}")

# Check status later
import psutil
if psutil.pid_exists(proc.pid):
    print("Training is still running...")
else:
    print("Training has completed!")
```

### Monitor GPU utilization
```python
# Check GPU usage in real-time
!watch -n 1 nvidia-smi
```

---

## 🎯 Next: On Your Mac

After downloading, run on Mac:

```bash
cd ~/Desktop/ISEF

# Generate evaluation metrics
python generate_evaluation_metrics_simple.py \
  --ppo_dir results/ppo_baseline \
  --hybrid_dir results/hybrid_training \
  --output results/eval_metrics_full.csv

# Generate plots
python generate_plots.py \
  --metrics_csv results/eval_metrics_full.csv \
  --output_dir aurora-web/public/charts/

# Start web demo
cd aurora-web
npm run dev
```

---

**Last Updated:** November 2, 2025  
**Version:** 1.0
