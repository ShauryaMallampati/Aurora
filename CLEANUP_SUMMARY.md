# AURORA Project Cleanup - November 24, 2025

## Files Removed (Legacy/Unused)

### Documentation (Outdated Planning Docs)
- `PHASE_1_IMPLEMENTATION_PLAN.md` - superseded by completion
- `SERVER_RUNNING.md` - temporary server setup notes
- `SPLIT_VIEW_IMPLEMENTATION.md` - implementation notes (no longer needed)
- `TASK_1_1_COMPLETE.md` - task completion tracking
- `TASK_1_2_IMPLEMENTATION.md` - task notes
- `TASK_1_5_IMPLEMENTATION.md` - task notes
- `README_TASK_1_1.md` - task-specific README
- `PHASE_1_COMPLETION.md` - phase completion tracking
- `COMPLETION_SUMMARY.txt` - summary file

### Training Scripts (Obsolete/Superseded)
- `main.py` - original baseline (superseded by main_enhanced.py)
- `demo_hybrid_model.py` - demo script (not in active workflow)
- `train_qwen_wildfire.py` - separate Qwen training (redundant)
- `train_real_fire.py` - separate real fire training (redundant)
- `train_manager.py` - training manager (superseded by train_hybrid.py)

### Metrics & Visualization (Legacy)
- `generate_evaluation_metrics.py` - legacy evaluation (functionality in colab script)
- `generate_evaluation_metrics_simple.py` - legacy simple metrics
- `generate_plots.py` - legacy plotting (use web dashboard instead)
- `generate_web_demo.py` - legacy demo generation

### Data Processing (Unused)
- `data/fire_perimeter_loader.py` - superseded by real_data_integration_complete.py
- `data/fire_perimeter_loader_real.py` - duplicate real data loader
- `prepare_qwen_dataset.py` - Qwen dataset prep (not in current pipeline)

### Agent Files (Consolidated)
- `agents/llm_strategy_agent.py` - superseded by hybrid_ppo_llm_agent.py
- `agents/qwen_strategy_agent.py` - Qwen-specific agent (consolidated)

### Backend Infrastructure (Consolidated)
- `aurora-backend/` - entire folder removed (all functionality in aurora-web)

### Config Files (Auto-Generated)
- `package-lock.json` - auto-generated (regenerates with npm install)
- `start-dev.sh` - old dev starter (use aurora-web npm commands)

## Files Kept (Active/Essential)

### Core Training
- `train_hybrid.py` - **Main training script** with hybrid PPO+LLM
- `colab_train_aurora.py` - **Google Colab training** (new, all-in-one)
- `callbacks.py` - **Training callbacks** for metrics logging
- `evaluation_battery.py` - **Evaluation suite** on held-out fires

### Core Infrastructure
- `agents/drone_agent.py` - Individual drone control
- `agents/hybrid_ppo_llm_agent.py` - LLM strategic guidance layer
- `env/fire_sim.py` - Fire dynamics engine
- `data/real_data_integration_complete.py` - Real fire data + NOAA weather integration

### Configuration
- `configs/training_phases.yaml` - Phase A/B/C training hyperparameters
- `master.sh` - CLI entry point for all workflows
- `requirements.txt` - Python dependencies

### Validation & Tools
- `preflight.py` - Pre-training validation
- `validate_strict_mode.py` - Real data strict mode validation
- `real_scenario_builder.py` - Scenario generation with real data
- `main_enhanced.py` - Enhanced simulation runner

### Web Demo
- `aurora-web/` - Next.js web demo interface with all Phase 1 features

### Documentation (Kept)
- `README.md` - Main project README
- `TRAINING_GUIDE.md` - Complete training guide
- `ISEF_MASTER_PLAN.md` - ISEF competition master plan
- `ISEF_JUDGE_GUIDE.md` - Judge guide
- `GET_STARTED.md` - Quick start guide
- `COMMAND_REFERENCE.md` - CLI command reference
- `QUICK_REFERENCE.md` - Quick reference card
- `ARCHITECTURE_DIAGRAM.md` - System architecture
- `TODO.md` - Current TODOs and roadmap

## Storage Savings

- **Deleted files**: ~25 files
- **Deleted folders**: 1 (aurora-backend)
- **Estimated space freed**: ~2-3 MB
- **Git history**: Preserved (can still access deleted files via git)

## Project Structure Now

```
Aurora/
├── agents/                          # RL agent implementations
│   ├── drone_agent.py
│   └── hybrid_ppo_llm_agent.py
├── aurora-web/                      # Next.js web demo
│   └── src/...                      # All Phase 1 features
├── configs/
│   └── training_phases.yaml
├── data/
│   └── real_data_integration_complete.py
├── env/
│   ├── fire_sim.py
│   └── __init__.py
├── results/                         # Trained models & checkpoints
├── utils/                           # Visualization utilities
├── callbacks.py                     # Training callbacks
├── colab_train_aurora.py           # Google Colab script
├── evaluation_battery.py
├── main_enhanced.py
├── master.sh                        # CLI entry point
├── preflight.py
├── real_scenario_builder.py
├── train_hybrid.py                 # Main training script
├── validate_strict_mode.py
├── requirements.txt
└── docs/                           # Documentation

Total Python Files: 12 (down from 30+)
Total Documentation: 9 files (lean & essential)
```

## How to Use Now

### Training on Local Machine
```bash
./master.sh train --phase full
# or
python train_hybrid.py --phase phase_a --n_envs 4
```

### Training on Google Colab
```
1. Open /Users/ankit/Aurora/colab_train_aurora.py
2. Copy entire content
3. Paste into a Colab cell
4. Run (auto-handles setup, dependencies, data download)
```

### Run Web Demo
```bash
cd aurora-web
npm install
npm run dev
# Visit http://localhost:3000
```

### Validate Setup
```bash
python preflight.py                     # Quick validation
python validate_strict_mode.py          # Full validation
```

---

**Date**: November 24, 2025  
**Rationale**: Remove redundant training scripts, consolidate agents, eliminate outdated documentation, clean up obsolete utilities  
**Benefit**: Reduced cognitive load, easier to navigate, faster git operations
