# AURORA ISEF 2025 - Training Guide
# Expert-recommended phased training for world-class competition results

## 🎯 Quick Start for ISEF

### Recommended: Run Phases A → B → C (11M steps, ~18-20 hours)
```bash
# Phase A: Sanity & Overfit (2M steps, ~2-3 hours)
python train_hybrid.py --phase phase_a

# Phase B: Curriculum (4M steps, ~6-8 hours)  
python train_hybrid.py --phase phase_b

# Phase C: Full Dataset (5M steps, ~8-10 hours)
python train_hybrid.py --phase phase_c

# Optional Phase D: Qwen Fine-tune (2M steps, ~3-4 hours)
python train_hybrid.py --phase phase_d
```

### Or run all phases at once (13M steps, ~22-26 hours)
```bash
python train_hybrid.py --phase full
```

### Quick test (500K steps, ~45-60 minutes)
```bash
python train_hybrid.py --phase quick
```

## 📊 Training Schedule

| Phase | Updates | Steps | Time | Purpose |
|-------|---------|-------|------|---------|
| **A** | 250 | 2.05M | 2-3h | Sanity check, overfit small dataset |
| **B** | 500 | 4.10M | 6-8h | Curriculum scaling, increase difficulty |
| **C** | 600 | 4.92M | 8-10h | Full dataset diversity, all 116K fires |
| **D** | 250 | 2.05M | 3-4h | Fine-tune strategy alignment (optional) |
| **Total** | 1600 | 13.12M | 22-26h | Complete training |

## 🔧 Configuration Details

### Default Settings (Optimized for ISEF)
- **n_steps**: 2048 (PPO rollout buffer)
- **num_envs**: 4 (parallel environments)
- **Steps per update**: 8,192 (2048 × 4)
- **LLM**: Qwen/Qwen2.5-7B-Instruct
- **LLM cadence**: Every 50 steps (reduce to 40 in Phase D)
- **Save frequency**: Every 5 updates (40,960 steps)
- **Eval frequency**: Every 10 updates (81,920 steps)

### Custom Training
```bash
# Custom timesteps
python train_hybrid.py --timesteps 10000000

# More parallel environments (faster but needs more RAM/GPU)
python train_hybrid.py --phase phase_c --n_envs 8

# Different LLM
python train_hybrid.py --phase phase_b --llm_model "meta-llama/Llama-2-7b-chat-hf"

# Adjust LLM frequency (higher = less frequent, lower GPU load)
python train_hybrid.py --phase phase_c --llm_freq 75
```

## 📈 Checkpointing & Evaluation

### Automatic Checkpoints
- Saved every **5 updates** (40,960 steps)
- Keeps top **5 models** by eval return
- Location: `results/aurora_hybrid_ppo_llm_model/`

### Evaluation Splits
1. **Temporal**: Years 2020-2024 (held-out recent fires)
2. **Geographic**: CA, WA, OR (held-out western states)

### Tracked Metrics
- Mean return ± 95% CI
- Median area burned
- Containment steps
- Idle steps per agent
- Completion rate
- Action distribution
- LLM latency & cache hit rate

## 🛑 Early Stopping Criteria

Training automatically stops when:

### Phase A
- Return plateaus for 30 updates AND
- Idle steps per agent < 3.0

### Phase B
- Completion rate ≥ 0.85 AND
- Area burned improves < 1% over 40 updates

### Phase C
- Return 95% CI overlaps for 3 consecutive evals AND
- Entropy < 0.01

### Phase D
- Completion rate ≥ 0.90 on both eval splits AND
- 3 consecutive successful evals

## 💡 Training Tips

### For Best ISEF Results
1. **Run all phases** (A → B → C → D) for maximum performance
2. **Use Qwen model** (better than Llama-2 for strategy)
3. **4-8 parallel environments** (balance speed vs memory)
4. **Monitor eval metrics** every 10 updates
5. **Keep top 5 checkpoints** and test on held-out data

### If Time/Resources Limited
- **Minimum**: Phase A + B (6M steps, ~10 hours) ✅
- **Good**: Phase A + B + C (11M steps, ~18 hours) ✅✅
- **Best**: All phases (13M steps, ~24 hours) ✅✅✅

### GPU Memory Issues?
```bash
# Reduce parallel environments
python train_hybrid.py --phase phase_c --n_envs 2

# Increase LLM cadence (less frequent calls)
python train_hybrid.py --phase phase_c --llm_freq 100

# Use smaller model
python train_hybrid.py --phase phase_c --llm_model "meta-llama/Llama-2-7b-chat-hf"
```

## 📂 Output Structure

```
results/
├── aurora_hybrid_ppo_llm_model/          # Final model
├── aurora_hybrid_ppo_llm_model_phase_a/  # Phase A checkpoint
├── aurora_hybrid_ppo_llm_model_phase_b/  # Phase B checkpoint
├── aurora_hybrid_ppo_llm_model_phase_c/  # Phase C checkpoint
└── hybrid_training_summary.json          # Training metrics

logs/
└── hybrid_training.log                    # Full training log
```

## 🔢 Quick Calculations

### Convert steps ↔ updates
- **Steps to updates**: `steps / 8192`
- **Updates to steps**: `updates × 8192`

### Examples
- 1M steps = 122 updates
- 5M steps = 611 updates
- 10M steps = 1,221 updates
- 13M steps = 1,587 updates

### Time estimates
- ~200K-250K steps/hour
- 1M steps ≈ 1.5-2 hours
- 5M steps ≈ 8-10 hours
- 13M steps ≈ 22-26 hours

## 🏆 ISEF Competition Strategy

### Week 1: Setup & Phase A
- Day 1-2: Environment setup, data preparation
- Day 3-4: Run Phase A (2M steps)
- Day 5: Analyze results, tune hyperparams

### Week 2: Core Training
- Day 1-3: Run Phase B (4M steps)
- Day 4-7: Run Phase C (5M steps)

### Week 3: Fine-tuning & Analysis
- Day 1-2: Run Phase D (2M steps) [optional]
- Day 3-5: Evaluate on held-out data
- Day 6-7: Generate visualizations, prepare results

### Presentation Materials
1. Training curves (return, area burned, completion rate)
2. Comparison: PPO-only vs Hybrid (use ablation)
3. Real fire case studies (temporal & geographic splits)
4. LLM guidance examples (show strategic decisions)
5. Performance metrics table

## 🚀 Run Commands (Copy-Paste Ready)

```bash
# === RECOMMENDED: Full phased training ===
./master.sh train --phase full

# === OR: Step-by-step phases ===
./master.sh train --phase phase_a  # 2M steps
./master.sh train --phase phase_b  # 4M steps  
./master.sh train --phase phase_c  # 5M steps
./master.sh train --phase phase_d  # 2M steps (optional)

# === Quick test ===
./master.sh train --phase quick  # 500K steps

# === Monitor training ===
tail -f logs/hybrid_training.log

# === Validate after training ===
./master.sh validate
```

## 📧 Support

Questions? Check:
1. `configs/training_phases.yaml` - Full phase configurations
2. `train_hybrid.py --help` - All command-line options
3. Training logs in `logs/hybrid_training.log`

Good luck with ISEF 2025! 🔥🚁
