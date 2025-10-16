# 🚀 AURORA Quick Start Guide

**Last Updated:** October 16, 2025  
**Status:** ✅ All systems ready for training

---

## ✅ Pre-Flight Complete

All checks passed! You're ready to train AURORA models on real wildfire data.

```bash
python preflight.py  # ✅ ALL CHECKS PASSED
```

---

## 🎯 Quick Test (5 minutes)

Before full training, run a quick sanity check:

```bash
# Test PPO baseline (500K steps ≈ 5-10 minutes)
python train_manager.py --mode ppo --phase quick --dry_run

# If dry run looks good, remove --dry_run to actually train
python train_manager.py --mode ppo --phase quick
```

**Expected output:**
- Model starts training on real fire scenarios
- Progress logs with ETA
- Checkpoint saved at end
- No synthetic fallbacks triggered

---

## 🔥 Full Training Workflow

### Phase 1: PPO Baseline (4-6 hours)

```bash
python train_manager.py \
  --mode ppo \
  --phase phase_a \
  --output_dir results/ppo_baseline
```

**What happens:**
- Trains on 57,344 steps (Phase A from training_phases.yaml)
- Evaluates every 81,920 steps on held-out fires
- Saves checkpoints every 40,960 steps
- Logs to `results/ppo_baseline/` and `logs/`

**Monitor training:**
```bash
tail -f logs/ppo_training.log
```

### Phase 2: Hybrid PPO+LLM (4-6 hours)

```bash
python train_manager.py \
  --mode hybrid \
  --phase phase_a \
  --output_dir results/hybrid_model
```

**What happens:**
- Trains with LLM strategic guidance every 50 steps
- Same evaluation schedule as PPO
- Logs LLM latency to `results/llm_latency.csv`
- Uses Gemini backend (fast, no HF downloads)

---

## 📊 After Training: Comparison

```bash
# Compare models
python -c "
from evaluation_battery import compare_models
comp = compare_models('results/metrics.csv')
if comp:
    print(f'Return: +{comp[\"return_improvement\"]:.1f}%')
    print(f'Area saved: +{comp[\"burned_area_reduction\"]:.1f}%')
    print(f'Time: -{comp[\"containment_time_improvement\"]:.1f}%')
"
```

---

## 🎨 Frontend Demo

```bash
cd aurora-web
npm install  # First time only
npm run dev
```

Open http://localhost:3000

**Key pages:**
- `/` - Hero landing page
- `/sim` - Live Mission Control
- `/scenarios` - Scenario Gallery (NEW!)
- `/runs` - Run History

---

## 🐛 Troubleshooting

### "No scenarios built"
```bash
# Test scenario builder
python real_scenario_builder.py
# Should build 10 sample scenarios
```

### "Validation failed"
```bash
python validate_strict_mode.py
# Check which component failed
```

### "Import errors"
```bash
pip install -r requirements.txt
# Reinstall dependencies
```

### "Out of memory"
```bash
# Reduce parallel environments
python train_manager.py --mode ppo --phase phase_a --n_envs 2
```

---

## 📁 Key Files Created/Modified

### New Files ✨
- ✅ `fire_perimeter_loader_real.py` - Real fire data loader
- ✅ `evaluation_battery.py` - Held-out test set (5 fires × 5 seeds)
- ✅ `callbacks.py` - Training callbacks with eval integration
- ✅ `train_manager.py` - Simplified training interface
- ✅ `preflight.py` - Pre-flight validation
- ✅ `QUICKSTART.md` - This guide!

### Frontend Additions 🎨
- ✅ `aurora-web/src/app/scenarios/page.tsx` - Scenario Gallery
- ✅ `aurora-web/src/app/sim/SplitViewComparison.tsx` - Model comparison

### Modified Files 🔧
- ✅ `requirements.txt` - Complete dependencies
- ✅ `train_real_fire.py` - No synthetic fallback, shape assertions
- ✅ `train_hybrid.py` - No synthetic fallback, shape assertions
- ✅ `env/fire_sim.py` - Accepts initial_fire_grid parameter
- ✅ `real_scenario_builder.py` - Fallback import for loader

---

## 🎯 Next Steps for ISEF

### Immediate (Before Competition)
1. ✅ Train both models (PPO + Hybrid) - **8-12 hours**
2. ⏳ Generate comparison videos - **1 hour**
3. ⏳ Polish frontend (implement remaining components) - **12-16 hours**
4. ⏳ Create poster figures - **2 hours**
5. ⏳ Practice demo script - **1 hour**

### Frontend Priorities
1. 🔴 Split View working (currently has type errors)
2. 🟢 Scenario Gallery (done!)
3. 🔴 Experiment Lab page
4. 🔴 Drone "why" popover
5. 🔴 Run History enhancements

---

## 💡 Pro Tips

### Speed Up Training
- Use `--phase quick` for fast iteration (500K steps)
- Use `--n_envs 2` if low on RAM
- Gemini backend is faster than local transformers

### Ensure Reproducibility
- Evaluation battery is frozen (5 fires, 5 seeds)
- Metrics automatically append to `results/metrics.csv`
- Every checkpoint includes metadata JSON

### Debug Mode
- Add `--verbose 2` to training scripts for detailed logs
- Check `logs/*.log` files for errors
- Use `--dry_run` to test configs without training

---

## 🏆 Judge Demo Ready Checklist

- [x] All dependencies installed
- [x] Data files verified
- [x] Modules importable
- [x] Output directories created
- [ ] PPO baseline trained
- [ ] Hybrid model trained
- [ ] Evaluation metrics computed
- [ ] Videos generated
- [ ] Frontend polished
- [ ] Demo script practiced

---

## 📞 Need Help?

**Check these in order:**
1. Run `python preflight.py` - Identifies most issues
2. Read error logs in `logs/`
3. Check `results/*/run_metadata.json` for run details
4. Verify data files exist in `data/`

---

**You're ready to train world-class wildfire AI! 🔥🚁**

Start with: `python train_manager.py --mode ppo --phase quick`
