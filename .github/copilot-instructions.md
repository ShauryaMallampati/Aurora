# AURORA: Wildfire AI Training System - Developer Guide

## Project Overview

**AURORA** (Autonomous Unified Response Orchestration for Real-world Actions) is an ISEF 2025 competition project that trains autonomous drone agents to contain wildfires using a hybrid PPO + LLM reinforcement learning approach with **REAL historical wildfire data**.

### Core Architecture: Hybrid PPO-LLM

```
┌─────────────────────────────────────────────────────────────┐
│                    AURORA Training Loop                      │
│                                                              │
│  Real Fire Data (116K fires) → Environment → Observations   │
│         ↓                           ↓              ↓         │
│  RealDataIntegrator      HybridRealFireEnv    DroneAgent    │
│         ↓                           ↓              ↓         │
│  NOAA Weather + Terrain    LLM Strategy    PPO Actions      │
│         ↓                           ↓              ↓         │
│  FireSim (dynamics)        Qwen 2.5-1.5B    Suppression     │
│                                    ↓              ↓         │
│                            Strategic Guidance  Rewards       │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Philosophy

1. **REAL DATA STRICT MODE**: Training uses ONLY real historical wildfire data—NO synthetic fallbacks
2. **Hybrid Intelligence**: LLM provides high-level strategy (every 500 steps), PPO handles low-level actions
3. **Phased Training**: Progressive curriculum (Phase A→B→C) for stable learning across 116K fire scenarios

---

## Critical File Structure

### Entry Points
- `train_hybrid.py` - **Main training script** (hybrid PPO+LLM with real data)
- `main_enhanced.py` - Run simulations with trained models
- `main.py` - Original baseline simulation (no RL)
- `master.sh` - Unified CLI for all workflows

### Core Systems
- `env/fire_sim.py` - Fire dynamics engine (wind, elevation, fuel density)
- `agents/hybrid_ppo_llm_agent.py` - LLM strategic guidance layer
- `agents/drone_agent.py` - Individual drone with battery/water management
- `data/real_data_integration_complete.py` - NOAA weather + fire perimeter loader
- `real_scenario_builder.py` - **STRICT MODE** real scenario generation

### Training Infrastructure
- `configs/training_phases.yaml` - Phase A/B/C hyperparameters
- `callbacks.py` - Progress tracking + evaluation battery integration
- `evaluation_battery.py` - 5 held-out fires × 5 seeds = 25 eval episodes
- `train_qwen_wildfire.py` - LoRA fine-tuning for Qwen (optional Phase D)

### Data Pipeline
- `data/InterAgencyFirePerimeterHistory_All_Years_View_5507083134356011387/` - 116,337 fire perimeters (1308-2024)
- `data/weather_cache/` - NOAA weather snapshots (lat/lon → temp, wind, humidity)
- `data/fire_perimeter_loader.py` - Shapefile → training scenario converter

### Outputs
- `results/aurora_hybrid_ppo_llm_model/` - Trained model checkpoints
- `results/checkpoints/` - Intermediate saves (every 40,960 steps)
- `logs/` - JSON simulation logs (default directory)

---

## Real Data Strict Mode

**CRITICAL**: This project enforces `REAL_DATA_STRICT = True` in `real_scenario_builder.py`.

### What This Means
- All training scenarios MUST come from the shapefile (`InteragencyFirePerimeterHistory.shp`)
- Weather MUST be from NOAA cache or live API—no fallback values
- Terrain derived from USGS elevation API or location-based generation
- If ANY real data source fails, training **must fail-fast** (no synthetic substitution)

### Data Validation
```bash
# Verify all data sources before training
python validate_strict_mode.py

# Quick preflight check
python preflight.py
```

### Required Files
1. `data/InterAgencyFirePerimeterHistory_All_Years_View_5507083134356011387/InteragencyFirePerimeterHistory.shp` (+ .dbf, .shx, .prj)
2. `data/weather_cache/*.json` (pre-cached NOAA snapshots)
3. Shapefile must be in EPSG:4326 (WGS84) CRS

---

## Training Workflow

### Quick Start (Recommended for ISEF)
```bash
# Full phased training (~18-20 hours on GPU)
./master.sh train --phase full

# Or step-by-step with checkpointing
./master.sh train --phase phase_a  # 2M steps, ~2-3h
./master.sh train --phase phase_b  # 4M steps, ~6-8h  
./master.sh train --phase phase_c  # 5M steps, ~8-10h
```

### Phase Configuration (from `configs/training_phases.yaml`)
- **Phase A**: Overfit on 1K fires, verify learning (57K steps)
- **Phase B**: Curriculum scaling to 5K fires (147K steps)
- **Phase C**: Full 116K dataset diversity (196K steps)
- **Full**: All phases combined (401K steps)

### Training Parameters
- **n_steps**: 2048 (PPO rollout buffer)
- **num_envs**: 2 (parallel environments, 4096 steps/update)
- **LLM cadence**: Every 500 steps (reduced from 50 for speed)
- **Checkpointing**: Every 5 updates (40,960 steps)
- **Evaluation**: Every 10 updates (81,920 steps)

### Resuming Training
```bash
# Auto-resume from latest checkpoint
python train_hybrid.py --phase phase_c --resume
```

Checkpoints stored in `results/checkpoints/checkpoint_step_<N>.zip`

---

## Key Code Patterns

### 1. Environment Reset (Real Data Only)
```python
# train_hybrid.py: HybridRealFireEnv.reset()
self.current_scenario = self.integrator.create_training_scenario(
    min_year=2010, min_acres=100, max_acres=50000
)
# NO FALLBACK to synthetic - if integrator fails, retry with another real scenario
```

### 2. LLM Strategic Guidance
```python
# agents/hybrid_ppo_llm_agent.py
if self.should_request_guidance(step):
    strategy = self.get_strategic_guidance(
        fire_state=fire_grid,
        drone_positions=positions,
        weather=noaa_data,
        step=current_step
    )
    # Returns: {'priority_zones': [...], 'drone_assignments': {...}}
```

### 3. Observation Space (9-channel)
```python
# Channels 0-5: Base observation (fire, terrain, elevation, fuel, battery, water)
# Channels 6-8: Strategic overlay from LLM (priority weight, direction_x, direction_y)
obs = np.zeros((3, 3, 9), dtype=np.float32)
```

### 4. Weather Integration (NOAA)
```python
# data/real_data_integration_complete.py
weather = integrator.get_noaa_weather(lat, lon)
# Returns: {temperature_c, wind_speed_mph, wind_direction, humidity}
# Uses cache if available (<30 days old), else live API
```

---

## Common Pitfalls

### 1. Shapefile Not Found
```
FileNotFoundError: Fire perimeter shapefile not found
```
**Fix**: Verify path in `data/fire_perimeter_loader.py` matches actual directory name. Check for Git LFS download.

### 2. CRS Reprojection Issues
Fire perimeters must be in EPSG:4326 (WGS84). The loader auto-reprojects but verify with:
```python
print(gdf.crs)  # Should be EPSG:4326
```

### 3. NOAA API Rate Limiting
The weather integrator caches responses. If you hit rate limits:
- Use cached weather (30-day tolerance)
- Set `REAL_DATA_STRICT=False` temporarily (NOT for final training)
- Wait 1 hour between bulk weather fetches

### 4. LLM Model Gating
For meta-llama models, you need HuggingFace token:
```bash
export HF_TOKEN=<your_huggingface_token>
python train_hybrid.py --llm_model meta-llama/Llama-2-7b-chat-hf
```
Qwen models are ungated (recommended for ISEF).

### 5. Checkpoint Step Mismatch
When resuming, ensure `--timesteps` accounts for already-trained steps:
```python
# train_hybrid.py handles this automatically:
remaining_timesteps = max(0, args.timesteps - resume_step)
```

---

## Testing & Validation

### Preflight Check (Before Training)
```bash
python preflight.py
# Validates: dependencies, data files, shapefile, weather cache
```

### Strict Mode Validation
```bash
python validate_strict_mode.py
# Tests: data integrity, CRS reprojection, USGS elevation, NOAA weather, scenario building
```

### Evaluation Battery
```python
# evaluation_battery.py
# 5 representative fires (Camp Fire, Riverside Fire, etc.)
# 5 seeds per fire = 25 eval episodes
# Metrics: return, containment_time, burned_area, success_rate
```

---

## LLM Backend Options

### Transformers (Recommended)
```bash
python train_hybrid.py --llm_backend transformers --llm_model Qwen/Qwen2.5-1.5B-Instruct
```
- Runs locally on GPU/CPU
- 1.5B model fast enough for training
- No API costs

### Heuristic Fallback
If LLM fails to load, `HybridPPOLLMAgent` falls back to rule-based strategy:
```python
# agents/hybrid_ppo_llm_agent.py: _heuristic_strategy()
# Identifies fire clusters, assigns drones to nearest hotspots
```

---

## Output Formats

### Training Summary (`results/hybrid_training_summary.json`)
```json
{
  "model_type": "hybrid_ppo_llm",
  "total_timesteps": 401408,
  "fire_records_available": 116337,
  "data_source": "InterAgency Fire Perimeter History (1308-2024)",
  "weather_source": "NOAA National Weather Service API"
}
```

### Simulation Logs (`logs/aurora_simulation_YYYYMMDD_HHMMSS.json`)
```json
{
  "simulation_config": {...},
  "step_data": [
    {
      "step": 0,
      "fire_coverage": 0.15,
      "weather": {...},
      "agent_positions": [[10, 20], [15, 25]],
      "actions": [5, 1]  // suppress, move_up
    }
  ]
}
```

---

## Performance Expectations

### Training Speed
- **~200K-250K steps/hour** on M1 Mac / NVIDIA RTX 3090
- Phase A (57K): ~1-2 hours
- Phase B (147K): ~3-4 hours
- Phase C (196K): ~4-5 hours
- **Full (401K): ~8-12 hours**

### Memory Requirements
- **Training**: 8-16GB RAM, 4-6GB GPU VRAM (for Qwen 1.5B)
- **2 parallel envs**: ~4GB RAM per env
- **4 parallel envs**: Faster but needs 16GB+ RAM

### Checkpoint Sizes
- PPO model: ~5MB
- Checkpoint with optimizer state: ~20MB
- Full training run: ~200MB total checkpoints

---

## Web Demo (Next.js)

Located in `aurora-web/`:
```bash
cd aurora-web
npm install
npm run dev
# Serves interactive simulation viewer on http://localhost:3000
```

Demo files stored in `public/demos/` (JSON logs from `logs/` directory)

---

## Environment Variables

```bash
# HuggingFace token (for gated models)
export HF_TOKEN=<your_huggingface_token>

# Disable tokenizer parallelism (avoids fork warnings)
export TOKENIZERS_PARALLELISM=false

# Set log directory (default: logs/)
export AURORA_LOG_DIR=custom_logs/
```

---

## Dependencies

Key packages (from `requirements.txt`):
- **RL**: `stable-baselines3`, `gymnasium`, `torch`
- **LLM**: `transformers`, `accelerate`, `sentencepiece`
- **Geospatial**: `geopandas`, `shapely`, `rasterio`, `pyproj`
- **Data**: `pandas`, `numpy`, `scipy`, `requests`
- **Viz**: `matplotlib`, `plotly`, `seaborn`

Install:
```bash
pip install -r requirements.txt
```

---

## Debugging Tips

### Enable Verbose Logging
```bash
python train_hybrid.py --phase quick --verbose 1
```

### Test Single Environment
```python
# train_hybrid.py
env = DummyVecEnv([make_env(0, llm_model, llm_freq, hf_token, llm_backend)])
```

### Inspect Fire Scenarios
```python
from data.real_data_integration_complete import RealDataIntegrator
integrator = RealDataIntegrator()
scenario = integrator.create_training_scenario()
print(scenario.keys())  # ['initial_fire_grid', 'weather', 'terrain', ...]
```

### Check LLM Guidance
```python
from agents.hybrid_ppo_llm_agent import HybridPPOLLMAgent
agent = HybridPPOLLMAgent(llm_model="Qwen/Qwen2.5-1.5B-Instruct")
strategy = agent.get_strategic_guidance(fire_state, positions, weather, step=0)
print(strategy)  # {'priority_zones': [...], 'drone_assignments': {...}}
```

---

## Project Status & TODOs

### ✅ Completed
- Real data integration (116K fires, NOAA weather)
- Hybrid PPO+LLM training infrastructure
- Phased curriculum training (A→B→C)
- Checkpointing and resume capability
- Evaluation battery (5 fires × 5 seeds)
- Strict mode validation
- Web demo interface

### 🚧 In Progress
- Phase C full dataset training (ongoing)
- Qwen fine-tuning (Phase D - optional)
- Evaluation metrics collection

### 📋 Remaining Work
1. **Complete Phase C Training**: Run full 196K steps on entire dataset
2. **Evaluation Analysis**: Generate comparison metrics (PPO-only vs Hybrid)
3. **Ablation Studies**: Test different LLM frequencies, model sizes
4. **Visualization Dashboard**: Enhance web demo with training curves
5. **ISEF Presentation Materials**: Generate charts, case studies, performance tables
6. **Documentation**: Add architecture diagrams, API docs for key classes

---

## Contact & Resources

- **ISEF Competition**: 2025
- **Author**: Shaurya Mallampati
- **Data Sources**:
  - InterAgency Fire Perimeter History: 116,337 fires (1308-2024)
  - NOAA National Weather Service API
  - USGS 3DEP Elevation API

---

## Quick Reference Commands

```bash
# Training
./master.sh train --phase full              # Full training (~12h)
python train_hybrid.py --phase phase_a      # Phase A only
python train_hybrid.py --resume             # Resume from checkpoint

# Validation
python preflight.py                         # Quick check
python validate_strict_mode.py              # Full validation

# Simulation
python main_enhanced.py                     # Run with trained model
python main.py                              # Run baseline (no RL)

# Evaluation
python evaluation_battery.py                # Run evaluation suite

# Web Demo
cd aurora-web && npm run dev                # Start Next.js server
```

---

**Remember**: This is a REAL DATA project. When debugging, always verify:
1. Shapefile is accessible and in EPSG:4326
2. Weather cache has data for fire locations
3. `REAL_DATA_STRICT = True` in production
4. No synthetic fallbacks in training pipeline
