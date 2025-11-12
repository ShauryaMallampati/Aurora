# Phase 2 – Training, Evaluation, and Demo Execution Plan (AURORA)

This document lists exactly what remains to complete Phase 2 (2A–2F), the models to train, run commands, outputs, and verification steps. It aligns with the current repo scripts and Real Data Strict Mode.

## Overview
- Target: Complete PPO baseline and Hybrid PPO+LLM experiments, gather metrics, and prepare demo + plots for ISEF.
- Dataset: InterAgency Fire Perimeter History (116,337 fires), NOAA weather, USGS elevation.
- Strict Mode: `REAL_DATA_STRICT=True` enforced. Use `preflight.py` and `validate_strict_mode.py` before long runs.
- Compute: Google Colab A100 (recommended) for training; Mac for analysis, plots, and web demo.

## Models To Train
- PPO Baseline (no LLM): Stable-Baselines3 PPO in `train_hybrid.py` with LLM disabled.
- Hybrid PPO+LLM: PPO + strategic guidance via Qwen Instruct model.
  - Primary: `Qwen/Qwen2.5-7B-Instruct` (A100 40GB recommended).
  - Fallback (faster/lighter): `Qwen/Qwen2.5-1.5B-Instruct`.

## Training Matrix (Phase 2)
- 2A – PPO Baseline: 5 seeds × 400k steps = 5 runs.
- 2B – Hybrid PPO+LLM: 3 cadences × 5 seeds × 400k steps = 15 runs.
  - Cadences: {100, 250, 500} steps between guidance calls.

## Prerequisites (Run Once)
```bash
# Verify environment + data integrity
python preflight.py
python validate_strict_mode.py
```
If any check fails: fix shapefile path/CRS, NOAA cache, or USGS/elevation before training.

## Commands – PPO Baseline (2A)
Disable LLM by passing `--llm_model none` (or `--llm_freq 999999`). Use 400k steps and 5 seeds.

```bash
# Example (seed 0)
python train_hybrid.py \
  --phase full \
  --timesteps 400000 \
  --llm_model none \
  --llm_freq 999999 \
  --llm_backend transformers \
  --n_envs 2 \
  --save_freq 40960 \
  --eval_freq 81920 \
  --seed 0 \
  --resume

# Repeat seeds: 0 1 2 3 4
```

Outputs:
- Checkpoints: `results/checkpoints/checkpoint_step_*.zip`
- Final model: `results/aurora_hybrid_ppo_llm_model/` (used for PPO too)
- Summary: `results/hybrid_training_summary.json`

## Commands – Hybrid PPO+Qwen (2B)
Train with 3 cadences and 5 seeds each (400k steps).

```bash
# Example (cadence 250, seed 0)
python train_hybrid.py \
  --phase full \
  --timesteps 400000 \
  --llm_backend transformers \
  --llm_model Qwen/Qwen2.5-7B-Instruct \
  --llm_freq 250 \
  --n_envs 2 \
  --save_freq 40960 \
  --eval_freq 81920 \
  --seed 0 \
  --resume

# Cadences to run: 100, 250, 500
# Seeds: 0 1 2 3 4
```

Notes:
- If VRAM is tight, switch to `--llm_model Qwen/Qwen2.5-1.5B-Instruct`.
- Provide `HF_TOKEN` only for gated models (Qwen is typically ungated).

## Colab Run Steps (Recommended)
```bash
# 1) Environment setup
!nvidia-smi
!pip install -r requirements.txt

# 2) (Optional) Mount Google Drive to save outputs
from google.colab import drive
drive.mount('/content/drive')
%cd /content
!mkdir -p /content/aurora && cp -r /content/drive/MyDrive/Aurora/* /content/aurora/ || true
%cd /content/aurora

# 3) Preflight checks
!python preflight.py
!python validate_strict_mode.py

# 4) Train PPO Baseline (repeat for seeds)
!python train_hybrid.py --timesteps 400000 --llm_model none --llm_freq 999999 --seed 0 --resume

# 5) Train Hybrid (repeat cadence×seed)
!python train_hybrid.py --timesteps 400000 --llm_model Qwen/Qwen2.5-7B-Instruct --llm_freq 250 --seed 0 --resume

# 6) Save to Drive
!cp -r results /content/drive/MyDrive/Aurora/results
```

## Download Models to Mac (2C)
Option A – rclone (fast, resumable):
```bash
# Install rclone once, then configure Google Drive remote named `gdrive`
rclone copy gdrive:/Aurora/results ~/Desktop/ISEF/results --progress
```
Option B – Manual download via Drive UI, then place under `results/`.

Verify models:
```bash
python generate_evaluation_metrics_simple.py --verify-only
```

## Metrics and Analysis (2D)
```bash
# Generates eval_metrics_full.csv
python generate_evaluation_metrics_simple.py
# Optionally: comprehensive metrics
python generate_evaluation_metrics.py
```
Artifacts:
- `eval_metrics_full.csv`
- Any per-run summaries in `results/`

## Publication Plots (2E)
```bash
python generate_plots.py
```
Outputs:
- Charts saved to `aurora-web/public/charts/` (Returns vs Latency, Containment vs Cadence, Completion Rate, Robustness)

## Live Demo & Presentation (2F)
```bash
# Start local web demo
cd aurora-web
npm install
npm run dev
# http://localhost:3000
```
Checklist:
- Test split view, metrics dashboard, custom fire creator
- Record short demo video (optional)
- Practice judge presentation, include plots and case studies

## Resume, Checkpointing, and Seeds
- Use `--resume` to auto-continue from the latest `results/checkpoints/checkpoint_step_*.zip`.
- Default PPO hyperparameters set in `train_hybrid.py`: `n_steps=2048`, `n_envs=2` → 4096 steps/update.
- Default save/eval: `--save_freq 40960`, `--eval_freq 81920`.

## When to Extend Training
- **Eval cadence:** Evaluate every `eval_freq` steps (~81,920). Judge with moving trends over the last 2–3 evals.
- **Extend (+200k steps) when:**
  - **Success rate:** < 70% and improves ≥ 3% absolute over the last two evals.
  - **Burned area:** Hybrid beats PPO by < 10% but improved ≥ 2% absolute over the last two evals.
  - **Containment time:** Median containment time is still decreasing by ≥ 2% across the last two evals.
- **Do NOT extend when (plateau):**
  - Success rate and burned area both change < 1% relative across two consecutive evals, and curves are flat.
  - PPO typically plateaus by 300k–400k; only extend PPO if it’s still improving at 400k.
- **Priority order (Hybrid):** Extend cadence `100` first, then `250`. Extend `500` only if it’s still trending up notably.
- **Max per run:** Cap at ~800k total steps before reconsidering model size/cadence rather than more steps.
- **Command to extend (example):**
  ```bash
  # Extend an existing run from 400k to 600k using checkpoints
  python train_hybrid.py \
    --timesteps 600000 \
    --llm_model Qwen/Qwen2.5-7B-Instruct \
    --llm_freq 250 \
    --seed 0 \
    --resume
  ```
Notes:
- Keep `--save_freq` and `--eval_freq` fixed to maintain comparability across runs.
- If GPU VRAM is tight for 7B, switch only the LLM model to `Qwen/Qwen2.5-1.5B-Instruct`; keep all other settings identical.

## Git LFS and Sync
```bash
git lfs track "data/InterAgencyFirePerimeterHistory_All_Years_View_5507083134356011387/*"
git lfs track "results/**"
git add .gitattributes

git add .
git commit -m "Phase 2 plan + training runs"
git pull --rebase
git push origin Main
```

## Remaining Work (at a Glance)
- 2A: Run PPO baseline – 5 seeds × 400k, upload results
- 2B: Run Hybrid – cadences {100,250,500} × 5 seeds, upload
- 2C: Download all models to Mac and verify
- 2D: Generate metrics CSV and sanity-check results
- 2E: Create publication plots into the web folder
- 2F: Test live demo end-to-end, record optional video

## Risks/Blockers
- NOAA/USGS API rate limits → rely on cached weather/elevation where possible
- VRAM constraints for Qwen-7B → use Qwen-1.5B fallback
- Data integrity issues → re-run `preflight.py` and `validate_strict_mode.py`

---
Maintainer: Phase 2 owner – Shaurya Mallampati
Updated: 2025-11-12
