# AURORA Project TODO - ISEF 2025 Competition

## 🎯 Current Status Assessment

### ✅ COMPLETED COMPONENTS

#### Data Infrastructure
- ✅ Real fire perimeter data integration (116,337 fires from InterAgency shapefile)
- ✅ NOAA weather API integration with caching (`data/weather_cache/`)
- ✅ USGS elevation API integration
- ✅ Shapefile loader with CRS reprojection to EPSG:4326
- ✅ Real data strict mode enforcement
- ✅ Scenario builder with REAL_DATA_STRICT validation

#### Training System
- ✅ Hybrid PPO+LLM architecture implemented
- ✅ Qwen 2.5-1.5B-Instruct integration
- ✅ Phased training configuration (A→B→C in `configs/training_phases.yaml`)
- ✅ Training callback with progress tracking and checkpointing
- ✅ Auto-resume capability from checkpoints
- ✅ Vectorized parallel environments (SubprocVecEnv)
- ✅ Master script (`master.sh`) for unified CLI

#### Agent Systems
- ✅ DroneAgent with battery/water management
- ✅ HybridPPOLLMAgent for strategic guidance
- ✅ 8-action space (stay, move, suppress, scan, communicate)
- ✅ 9-channel observation space (base + strategic overlay)
- ✅ Heuristic fallback when LLM unavailable

#### Environment
- ✅ FireSim with wind, elevation, fuel density dynamics
- ✅ Realistic fire spread based on weather/terrain
- ✅ Multi-agent coordination framework
- ✅ Reward system with strategic alignment bonus

#### Evaluation & Validation
- ✅ Evaluation battery (5 representative fires × 5 seeds)
- ✅ Preflight validation script
- ✅ Strict mode validation script
- ✅ Metrics tracking infrastructure

#### Visualization
- ✅ Enhanced visualizer with battery/water indicators
- ✅ Web demo (Next.js) framework in `aurora-web/`
- ✅ JSON logging system for simulation replay

---

## 🚧 IN-PROGRESS / INCOMPLETE

### 1. Training Completion
**Status**: Partial training runs completed (test phases), full training needed

**What's Done**:
- Test run: 1,000 steps completed (see `results/hybrid_training_summary.json`)
- Phase A configuration validated
- Checkpointing tested

**What's Needed**:
```bash
# Execute full phased training
./master.sh train --phase phase_a  # 57K steps (~2-3h)
./master.sh train --phase phase_b  # 147K steps (~6-8h)
./master.sh train --phase phase_c  # 196K steps (~8-10h)

# Or combined:
./master.sh train --phase full     # 401K steps (~18-20h)
```

**Action Items**:
- [ ] Run Phase A and verify learning (check return improvement)
- [ ] Run Phase B with curriculum scaling
- [ ] Run Phase C on full dataset
- [ ] Monitor for early stopping criteria
- [ ] Save top 10 checkpoints by eval performance

**Expected Outputs**:
- `results/aurora_hybrid_ppo_llm_model/` (final model)
- `results/aurora_hybrid_ppo_llm_model_phase_a/` (checkpoint)
- `results/aurora_hybrid_ppo_llm_model_phase_b/` (checkpoint)
- `results/aurora_hybrid_ppo_llm_model_phase_c/` (checkpoint)
- `logs/hybrid_training.log` (full training log)

---

### 2. Evaluation Suite Execution
**Status**: Framework ready, needs execution on trained models

**What's Done**:
- Evaluation battery defined (5 fires × 5 seeds)
- Metrics tracking infrastructure in `callbacks.py`
- CSV logging for results

**What's Needed**:
```python
# After training, run evaluation
python evaluation_battery.py --model results/aurora_hybrid_ppo_llm_model

# This should generate:
# - results/metrics.csv (per-episode metrics)
# - Summary statistics (mean return, success rate, etc.)
```

**Action Items**:
- [ ] Run evaluation on PPO-only baseline (train without LLM guidance)
- [ ] Run evaluation on Hybrid model (PPO + Qwen)
- [ ] Collect metrics: return, containment time, burned area, success rate
- [ ] Generate comparison tables (Hybrid vs Baseline)
- [ ] Compute statistical significance (t-test, confidence intervals)

**Metrics to Track**:
1. Mean episode return ± 95% CI
2. Median area burned (hectares)
3. Time to containment (steps)
4. Success rate (% fires contained)
5. Water efficiency (water used per hectare contained)
6. Idle steps per agent
7. LLM latency and cache hit rate

---

### 3. Ablation Studies
**Status**: Not started, optional for stronger ISEF presentation

**Purpose**: Demonstrate Hybrid approach superiority

**Experiments to Run**:

#### A. LLM Frequency Ablation
```bash
# Compare different LLM guidance frequencies
python train_hybrid.py --phase quick --llm_freq 50   # Frequent
python train_hybrid.py --phase quick --llm_freq 500  # Current
python train_hybrid.py --phase quick --llm_freq 1000 # Rare
python train_hybrid.py --phase quick --llm_freq 999999  # Effectively none (PPO-only)
```

**Hypothesis**: Too frequent = slow training, too rare = poor strategy. Optimal ~500.

#### B. LLM Model Size Ablation
```bash
# Compare model sizes
python train_hybrid.py --phase quick --llm_model Qwen/Qwen2.5-1.5B-Instruct
python train_hybrid.py --phase quick --llm_model Qwen/Qwen2.5-7B-Instruct
python train_hybrid.py --phase quick --llm_model meta-llama/Llama-2-7b-chat-hf
```

**Hypothesis**: Larger models provide better strategy but slower inference.

#### C. Environment Parallelism
```bash
# Compare parallel environments
python train_hybrid.py --phase quick --n_envs 2  # Current
python train_hybrid.py --phase quick --n_envs 4
python train_hybrid.py --phase quick --n_envs 8
```

**Hypothesis**: More envs = faster training but diminishing returns due to LLM overhead.

**Action Items**:
- [ ] Design ablation matrix (which variables to test)
- [ ] Run ablation experiments (use `--phase quick` for speed)
- [ ] Collect and visualize results (bar charts, line graphs)
- [ ] Include in ISEF presentation

---

### 4. Qwen Fine-Tuning (Phase D)
**Status**: Scripts ready (`train_qwen_wildfire.py`, `prepare_qwen_dataset.py`), not executed

**Purpose**: Align Qwen's strategic decisions to wildfire-specific knowledge

**What's Done**:
- LoRA training scaffolding
- Dataset preparation utilities
- Instruction-tuning format converters

**What's Needed**:
```bash
# 1. Prepare training data from scenarios
python prepare_qwen_dataset.py

# 2. Fine-tune Qwen with LoRA
python train_qwen_wildfire.py \
    --base_model Qwen/Qwen2.5-1.5B-Instruct \
    --output_dir models/qwen_wildfire_finetuned \
    --epochs 3

# 3. Use fine-tuned model in training
python train_hybrid.py --phase phase_d \
    --llm_model models/qwen_wildfire_finetuned
```

**Action Items**:
- [ ] Generate 10K+ training examples from real scenarios
- [ ] Fine-tune Qwen with LoRA (3-5 epochs, ~2-4 hours)
- [ ] Evaluate fine-tuned vs base model
- [ ] Compare strategic quality (qualitative analysis)

**Expected Benefit**: 10-20% improvement in strategic decisions, faster convergence.

---

### 5. Web Demo Enhancement
**Status**: Framework exists in `aurora-web/`, needs content and features

**What's Done**:
- Next.js project structure
- Basic page layouts in `src/app/`

**What's Needed**:

#### A. Simulation Replay
```typescript
// aurora-web/src/app/demo/page.tsx
// Load logs/aurora_simulation_*.json
// Animate fire spread + drone movements frame-by-frame
```

**Action Items**:
- [ ] Create interactive canvas for grid visualization
- [ ] Add playback controls (play/pause/step)
- [ ] Display metrics sidebar (fire coverage, drone battery, etc.)
- [ ] Color-code drones by strategic assignment

#### B. Training Curves Dashboard
```typescript
// aurora-web/src/app/training/page.tsx
// Load results/hybrid_training_summary.json + checkpoints metadata
// Plot: return over time, loss curves, eval metrics
```

**Action Items**:
- [ ] Integrate Chart.js or Recharts
- [ ] Plot training progress (return, entropy, loss)
- [ ] Add evaluation results overlay
- [ ] Export to PNG for ISEF poster

#### C. Comparison View
```typescript
// aurora-web/src/app/compare/page.tsx
// Side-by-side: PPO-only vs Hybrid
// Show same fire scenario, different outcomes
```

**Action Items**:
- [ ] Create split-screen layout
- [ ] Sync playback between two simulations
- [ ] Highlight strategic decisions (LLM guidance markers)
- [ ] Summary stats panel (which performed better)

---

### 6. Data Expansion (Optional)
**Status**: Current dataset sufficient, but could enhance

**Current Data**:
- 116,337 fire perimeters (InterAgency shapefile)
- ~200 NOAA weather cache entries
- USGS elevation (on-demand API)

**Potential Enhancements**:

#### A. Pre-cache More Weather Data
```python
# Bulk cache weather for all fire locations
from data.real_data_integration_complete import RealDataIntegrator
integrator = RealDataIntegrator()

for fire in fire_loader.gdf.iterrows():
    lat, lon = fire['geometry'].centroid.y, fire['geometry'].centroid.x
    integrator.get_noaa_weather(lat, lon)  # Will cache
```

**Benefit**: Faster scenario generation, no API rate limits during training.

#### B. Download USGS Elevation Tiles
```bash
# Pre-download elevation data for common fire regions
# Store in data/elevation_cache/
```

**Benefit**: Offline training, faster terrain generation.

**Action Items**:
- [ ] Identify top 1000 most-used fire locations
- [ ] Bulk cache weather for these locations
- [ ] Download USGS tiles for CA, WA, OR, CO, MT
- [ ] Update `RealDataIntegrator` to use local elevation first

---

## 📊 ISEF Presentation Preparation

### 7. Results Analysis & Visualization
**Status**: Not started, critical for competition

**Required Materials**:

#### A. Performance Comparison Table
```
| Metric              | PPO-Only | Hybrid (PPO+Qwen) | Improvement |
|---------------------|----------|-------------------|-------------|
| Mean Return         | -45.2    | -32.8             | +27.4%      |
| Success Rate        | 62%      | 81%               | +30.6%      |
| Containment Time    | 87 steps | 68 steps          | -21.8%      |
| Area Burned (ha)    | 124.5    | 89.3              | -28.3%      |
| Water Efficiency    | 2.1      | 1.6               | +23.8%      |
```

**Action Items**:
- [ ] Run evaluation battery on both models
- [ ] Compute statistics with 95% confidence intervals
- [ ] Format as LaTeX table for paper
- [ ] Create PNG version for poster

#### B. Training Curves
**Graphs Needed**:
1. Episode return over time (with error bars)
2. Evaluation metrics over updates
3. Action distribution evolution (entropy)
4. LLM guidance frequency vs performance

**Action Items**:
- [ ] Extract metrics from TensorBoard logs or checkpoint metadata
- [ ] Generate plots with matplotlib/seaborn
- [ ] Export high-res PNGs for poster
- [ ] Annotate key milestones (phase transitions, convergence)

#### C. Case Study: Specific Fire Analysis
**Example**: Camp Fire 2018
- Show initial conditions (fire grid, weather, terrain)
- Overlay drone trajectories (PPO-only vs Hybrid)
- Highlight LLM strategic decisions (priority zones)
- Compare final outcomes (area burned, containment time)

**Action Items**:
- [ ] Select 2-3 representative fires (easy, medium, hard)
- [ ] Run both models on same seeds
- [ ] Record frame-by-frame for visualization
- [ ] Create annotated comparison images
- [ ] Write narrative explanation for each case

#### D. Architecture Diagram
**Visual Representation**:
```
[Real Fire Data] → [Scenario Builder] → [Environment]
                                           ↓
                                    [Observation (9ch)]
                                           ↓
                                    ┌─────────────┐
                                    │  Hybrid     │
                                    │  Agent      │
                                    └─────────────┘
                                     ↙          ↘
                            [LLM Strategy]  [PPO Policy]
                                (Qwen)        (Network)
                                     ↘          ↙
                                    [Action (8)]
                                           ↓
                                    [Fire Sim Step]
                                           ↓
                                       [Reward]
```

**Action Items**:
- [ ] Create flowchart with draw.io or similar
- [ ] Annotate data dimensions at each step
- [ ] Color-code by component type (data, model, environment)
- [ ] Export for poster and paper

---

### 8. Documentation & Paper Writing
**Status**: README and TRAINING_GUIDE complete, need formal paper

**Required Sections**:

#### A. ISEF Research Paper
1. **Abstract** (250 words)
   - Problem: Wildfire response optimization
   - Solution: Hybrid PPO-LLM approach
   - Results: X% improvement over baseline
   - Significance: Scalable to real deployments

2. **Introduction** (2 pages)
   - Wildfire statistics (acres burned, cost)
   - Existing approaches (limitations)
   - Our contribution (hybrid architecture)

3. **Methods** (4 pages)
   - Data sources (InterAgency, NOAA, USGS)
   - Environment design (FireSim dynamics)
   - Hybrid agent architecture (PPO + Qwen)
   - Training procedure (phased curriculum)

4. **Results** (3 pages)
   - Performance metrics table
   - Training curves
   - Case studies (Camp Fire, etc.)
   - Ablation studies

5. **Discussion** (2 pages)
   - Why hybrid works (strategic + reactive)
   - Limitations (sim-to-real gap)
   - Future work (real drone integration)

6. **Conclusion** (1 page)
   - Summary of findings
   - Broader impact

**Action Items**:
- [ ] Outline paper structure
- [ ] Write methods section (most complete now)
- [ ] Generate all figures and tables
- [ ] Draft introduction and results
- [ ] Revise for clarity and conciseness
- [ ] Get feedback from mentors/advisors

#### B. Poster Design
**Layout** (48" × 36"):
- Title + Authors
- Problem statement (1/4 left column)
- Architecture diagram (center)
- Results table (right column)
- Case study images (bottom)
- QR code to web demo

**Action Items**:
- [ ] Design layout in PowerPoint or LaTeX beamer
- [ ] Export all figures at 300 DPI
- [ ] Proofread text
- [ ] Print at professional printer
- [ ] Practice elevator pitch (2 min)

---

## 🐛 Bug Fixes & Improvements

### 9. Known Issues

#### A. Weather Cache Age
**Issue**: Cache tolerance is 30 days, some fires may use stale weather.

**Fix**:
```python
# data/real_data_integration_complete.py:57
if cache_age < 30 * 24 * 3600:  # 30 days
    # Change to 7 days for fresher data?
```

**Action**: Test if shorter cache improves realism.

---

#### B. Checkpoint Naming Collision
**Issue**: If training interrupted and resumed, checkpoint numbers may overlap.

**Fix**:
```python
# train_hybrid.py: Add timestamp to checkpoint names
checkpoint_path = self.save_path / f"checkpoint_step_{self.n_calls}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
```

**Action**: Update checkpoint naming to include timestamp.

---

#### C. LLM Token Limit
**Issue**: Large fire grids may exceed LLM context window (2048 tokens for Qwen).

**Current Mitigation**: Heuristic fallback if LLM fails.

**Better Fix**: Downsample fire grid before sending to LLM:
```python
# agents/hybrid_ppo_llm_agent.py
fire_state_summary = fire_state[::2, ::2]  # Downsample 50x50 → 25x25
```

**Action**: Implement grid downsampling for LLM prompts.

---

#### D. Parallel Env Deadlocks
**Issue**: Occasional deadlock with SubprocVecEnv when LLM backend fails.

**Workaround**: Use DummyVecEnv (sequential) for debugging.

**Fix**: Add timeout wrapper around LLM calls:
```python
import signal
@timeout(10)  # 10 second timeout
def get_strategic_guidance(...):
    ...
```

**Action**: Implement timeout decorator for LLM calls.

---

### 10. Performance Optimizations

#### A. LLM Batch Inference
**Current**: Each drone calls LLM independently.

**Optimization**: Batch all drones' requests:
```python
# agents/hybrid_ppo_llm_agent.py
def batch_strategic_guidance(fire_states, drone_positions_list, ...):
    prompts = [format_prompt(fs, dps) for fs, dps in zip(...)]
    responses = self.pipe(prompts)  # Batch inference
    return [parse_response(r) for r in responses]
```

**Expected Speedup**: 2-3x faster with batch_size=num_drones.

**Action**: Implement batch inference for multi-agent.

---

#### B. Cache Strategic Decisions
**Current**: LLM re-computes strategy every 500 steps, even if state similar.

**Optimization**: Cache strategies by fire signature:
```python
fire_signature = (fire_coverage, wind_regime, drone_config)
if fire_signature in strategy_cache:
    return strategy_cache[fire_signature]
```

**Expected Speedup**: 50% reduction in LLM calls.

**Action**: Implement strategy caching with LRU cache.

---

#### C. Pre-generate Scenarios
**Current**: Scenarios generated on-the-fly during training (slow).

**Optimization**: Pre-generate 10K scenarios, save to disk:
```bash
python real_scenario_builder.py --generate 10000 --output data/real_training_data/
```

Then load from disk during training (instant).

**Expected Speedup**: 30% faster training startup.

**Action**: Add scenario pre-generation script.

---

## 🎯 Priority Ranking (ISEF Timeline)

### Week 1-2: Core Training
**Priority: CRITICAL**
- [ ] Complete Phase A training (57K steps)
- [ ] Complete Phase B training (147K steps)
- [ ] Complete Phase C training (196K steps)
- [ ] Save checkpoints and verify convergence

### Week 3: Evaluation & Ablation
**Priority: HIGH**
- [ ] Run evaluation battery on trained models
- [ ] Run PPO-only baseline for comparison
- [ ] Execute key ablation studies (LLM frequency, model size)
- [ ] Collect all metrics in CSV format

### Week 4: Analysis & Visualization
**Priority: HIGH**
- [ ] Generate performance comparison table
- [ ] Create training curves and case study figures
- [ ] Build web demo replay feature
- [ ] Draft results section of paper

### Week 5-6: Documentation & Presentation
**Priority: MEDIUM-HIGH**
- [ ] Complete ISEF research paper
- [ ] Design and print poster
- [ ] Record demonstration video
- [ ] Prepare oral presentation
- [ ] Practice Q&A

### Optional (Time Permitting):
**Priority: LOW**
- [ ] Qwen fine-tuning (Phase D)
- [ ] Data expansion (weather cache, elevation tiles)
- [ ] Performance optimizations (batch inference, caching)
- [ ] Bug fixes (non-critical issues)

---

## 📈 Success Metrics

**Minimum Viable Product** (for ISEF submission):
- ✅ Complete Phase A+B+C training (401K steps)
- ✅ Evaluation showing >20% improvement over PPO-only
- ✅ 1-2 case study visualizations
- ✅ Training curves and metrics table
- ✅ Complete research paper and poster
- ✅ Working web demo

**Stretch Goals** (for top-tier placement):
- ✅ All minimum requirements PLUS:
- ✅ Qwen fine-tuning (Phase D) with >10% additional improvement
- ✅ Comprehensive ablation studies (3+ variables)
- ✅ 5+ case studies across diverse fire types
- ✅ Statistical significance testing (p-values, CI)
- ✅ Interactive web demo with real-time replay
- ✅ Performance optimizations (2x speedup)
- ✅ Publication-quality figures and diagrams

---

## 🔗 Quick Links

**Commands**:
```bash
# Start training
./master.sh train --phase full

# Resume training
python train_hybrid.py --phase phase_c --resume

# Run evaluation
python evaluation_battery.py

# Validate setup
python preflight.py && python validate_strict_mode.py

# Start web demo
cd aurora-web && npm run dev
```

**Key Files**:
- `train_hybrid.py` - Main training script
- `configs/training_phases.yaml` - Phase configurations
- `evaluation_battery.py` - Evaluation suite
- `results/` - Trained models and checkpoints
- `logs/` - Simulation logs

**Next Steps**:
1. Run `./master.sh train --phase full` (start now, ~18-20 hours)
2. Monitor progress with `tail -f logs/hybrid_training.log`
3. While training runs, work on paper draft (Methods section)
4. After training, run evaluation and generate results

---

**Last Updated**: October 27, 2025  
**ISEF Deadline**: [Add your deadline here]  
**Days Remaining**: [Calculate from deadline]
