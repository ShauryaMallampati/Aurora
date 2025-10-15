# 🌍 AURORA: Autonomous Wildfire Response Simulation

**AURORA** (Autonomous Unified Response Orchestration for Real-world Actions) is an AI-powered simulation system where autonomous drone agents learn to coordinate in containing wildfires. This project uses reinforcement learning in a custom-built fire environment based on real-world terrain types.

---

## 🔥 Project Overview

AURORA simulates the spread of wildfire over a 2D forested terrain and trains AI agents (drones) to suppress it using reinforcement learning.

* 🌲 Simulated terrain with forests, roads, and water
* 🔥 Fire spreads dynamically based on terrain, wind, elevation, and fuel density
* 🤖 Multi-agent drones move, suppress fires, and learn optimal behavior via PPO
* 📈 Real-time visualization with matplotlib and interactive web interfaces
* 🧠 LLaMA integration for strategic decision-making
* 🌍 Real-world data integration (NASA FIRMS, NOAA Weather, USGS Elevation)

---

## 🗘️ Simulation Environment

The terrain is randomly generated from 4 cell types:

* `1 = Forest` (flammable)
* `2 = Road` (non-flammable)
* `3 = Water` (non-flammable)
* `0 = Empty` (no vegetation)

Fire starts in the center and spreads based on realistic physics-inspired rules including wind effects, elevation changes, and fuel density. Drones can move across the map and extinguish adjacent fires.

---

## 🧠 Drone Agents

Each drone observes a local 3x3 area and takes one of 8 actions:

```
[Stay, Move Up, Move Down, Move Left, Move Right, Suppress Fire, Scan, Communicate]
# AURORA — Consolidated README

This README consolidates project documentation and the generated notes into a single source of truth.

Contents in this file:
- Quick start and run commands
- Strict real-data mode notes
- Qwen fine-tuning and hybrid training pointers
- Where logs are written and how to change that

For full development notes and guides that were merged, see `README.backup.md` (original) and the individual docs in the repo if you need deeper detail.

---

## Quick start

1. Create and activate a Python virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run a basic simulation:

```bash
python main.py
```

3. Run the enhanced, real-data-capable simulation:

```bash
python main_enhanced.py
```

4. Train agents (PPO):

```bash
python train.py
```

5. Qwen fine-tuning (sketch): see `QWEN_QUICKSTART.md` and `train_qwen_wildfire.py` for the LoRA training scaffolds.

---

## Strict real-data mode (REAL_DATA_STRICT)

This codebase includes a strict mode flag `REAL_DATA_STRICT = True` used across data ingestion and scenario builders.
When enabled, the system will:

- Fail fast on missing real-world inputs (NOAA weather cache, InterAgency perimeter shapefile, USGS elevation samples)
- Not use synthetic or fallback weather/terrain
- Require the `data/real_data_cache` and `data/real_training_data` datasets to be present

If you need to run in synthetic/demo mode, set `REAL_DATA_STRICT = False` in the relevant data ingestion modules (not recommended for final experiments).

---

## Logs

All simulation logs are now saved to the top-level `logs/` directory by default. `SimulationLogger` in `main_enhanced.py` defaults to `log_dir='logs'` and creates the directory automatically.

Files you may see in `logs/`:
- aurora_simulation_YYYYMMDD_HHMMSS.json  — per-run JSON logs
- training and validation artifacts (if produced by scripts)

Note: older scripts referenced `results/logs/`; we migrated the default to `logs/` to centralize outputs. If a script still writes to `results/`, either update it or create a `results/logs` symlink.

---

## Qwen & Hybrid Training

- Qwen LoRA fine-tuning scaffolds: `prepare_qwen_dataset.py`, `train_qwen_wildfire.py`.
- Hybrid training (PPO + LLM) scaffolds: `train_hybrid.py`, `train_hybrid.sh`.
- Merged `requirements.txt` includes both RL and LLM dependencies — install into a GPU-enabled environment for full training.

---

## Where to find more details

- `validate_strict_mode.py` — a helper script to check presence of required real data files
- `REAL_DATA_STRICT_MODE.md`, `STRICT_MODE_COMPLETE.md` — more elaborate notes (kept in repo)
- `QWEN_QUICKSTART.md`, `QWEN_INTEGRATION_PLAN.md` — LLM integration notes

---

If you'd like, I can now safely remove the merged documentation files (they were backed up) and update the remaining scripts that still write to `results/` to use `logs/` instead. I will not delete any files until you confirm.
