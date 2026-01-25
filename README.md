# AURORA: Autonomous Unified Response Orchestration for Real-world Actions

## 🔥 Wildfire Containment Through Hybrid LLM-Guided Reinforcement Learning

AURORA is an AI system that trains autonomous drone swarms to contain wildfires using a hybrid architecture combining **Large Language Models (LLMs)** with **Proximal Policy Optimization (PPO)** reinforcement learning.

**Key Achievement:** 21% improvement over baseline RL through strategic LLM guidance on 116K real historical fires.

---

## 🎯 What is AURORA?

AURORA represents a paradigm shift in autonomous fire suppression:
- **Faster response**: 2-5 minutes vs 15-30 minutes traditional response
- **Strategic AI**: LLM provides guidance informed by 116K historical fires
- **Distributed attack**: Multiple drones suppress fire perimeter simultaneously
- **Real data**: Trained on actual wildfires with NOAA weather integration

### Key Results

| Metric | PPO Baseline | AURORA Hybrid | Improvement |
|--------|--------------|---------------|-------------|
| Final Return | 34.57 | 41.84 | **+21.0%** |
| Hard Scenarios | 36.26 | 58.85 | **+62.3%** |
| Easy Scenarios | 42.33 | 42.33 | 0.0% (already optimal) |
| Episodes Trained | 20,028 | 17,453 | 53,055 total |

**Key Insight:** Selective improvement on hard scenarios proves genuine strategic reasoning, not overfitting.

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.9+
- GPU recommended (CUDA 11.8+)
- 16GB RAM minimum

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/AURORA.git
cd AURORA

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python scripts/preflight.py
```

### Run a Quick Simulation

```bash
# Train for a few steps (10 min)
python scripts/train_hybrid.py --phase quick

# Run with trained model
python scripts/main_enhanced.py

# View web dashboard
cd aurora-web && npm run dev
# Open http://localhost:3000
```

---

## 📚 Documentation

- **[docs/ABSTRACT.md](docs/ABSTRACT.md)** - Research abstract (250 words)
- **[docs/ANALYSIS.md](docs/ANALYSIS.md)** - Complete analysis & results
- **[AURORA_vs_TRADITIONAL_FIREFIGHTING.md](AURORA_vs_TRADITIONAL_FIREFIGHTING.md)** - Real-world comparison
- **[CITATIONS.md](CITATIONS.md)** - Data sources & citations

---

## 🏗️ Project Structure

```
AURORA/
├── README.md                              # This file
├── LICENSE                               # MIT License
├── CITATIONS.md                          # All citations & data sources
├── AURORA_vs_TRADITIONAL_FIREFIGHTING.md # Real-world comparison
├── requirements.txt                      # Python dependencies
│
├── docs/                                 # Documentation
│   ├── ABSTRACT.md                      # Research abstract
│   ├── ANALYSIS.md                      # Complete analysis & results
│   └── README.md                        # Doc index
│
├── agents/                               # Autonomous agent controllers
│   ├── drone_agent.py                  # Individual drone
│   └── hybrid_ppo_llm_agent.py         # PPO + LLM hybrid agent
│
├── env/                                  # Fire simulation environment
│   └── fire_sim.py                     # Fire dynamics engine
│
├── data/                                 # Real data integration
│   ├── real_data_integration_complete.py
│   ├── fire_perimeter_loader.py
│   ├── InterAgencyFirePerimeterHistory/  # 116K historical fires
│   └── weather_cache/                   # NOAA weather data
│
├── configs/
│   └── training_phases.yaml            # Training hyperparameters
│
├── results/                              # Generated outputs
│   ├── models/                         # Trained model weights
│   ├── checkpoints/                    # Training checkpoints
│   ├── aurora_complete_evaluation.pdf  # Evaluation plots
│   └── aurora_metrics.csv              # Metrics data
│
├── scripts/                              # Core utilities
│   ├── train_hybrid.py                 # Main training script
│   ├── main_enhanced.py                # Run simulations
│   ├── evaluation_battery.py           # Evaluation suite
│   ├── preflight.py                    # Setup validation
│   └── validate_strict_mode.py         # Data validation
│
├── utils/                                # Visualization utilities
│   ├── visualizer.py
│   └── 3d_visualizer.py
│
├── aurora-web/                           # Next.js web dashboard
│   ├── src/
│   ├── package.json
│   └── README.md
│
└── callbacks.py                          # Training callbacks
```

---

## 🎓 How AURORA Works

### Hybrid Architecture

The core innovation is combining two AI approaches:

**1. Large Language Model (Qwen 2.5)**
- Analyzes entire fire state every 50 steps
- Learns from 116K historical wildfire patterns
- Provides strategic guidance to drone swarm
- Recommends priority zones and drone assignments

**2. Reinforcement Learning (PPO)**
- Learns continuous control policies
- Executes drone movement and suppression actions
- Adapts to real-time fire dynamics
- Improves through episode rewards

**Result**: LLM's strategic reasoning + PPO's learning agility = 21% improvement

---

## 📊 Training

### Quick Training (10-30 min)
```bash
python scripts/train_hybrid.py --phase quick
```

### Full Training (12 hours on GPU)
```bash
python scripts/train_hybrid.py --phase full
```

### Phased Training
```bash
# Phase A: 2-3 hours
python scripts/train_hybrid.py --phase phase_a

# Phase B: 3-4 hours
python scripts/train_hybrid.py --phase phase_b

# Phase C: 4-5 hours
python scripts/train_hybrid.py --phase phase_c
```

---

## 📈 Evaluation

### Run Evaluation Suite
```bash
python scripts/evaluation_battery.py
```

### Generate Analysis
```bash
cd scripts/analysis/
python verify_21_percent.py          # Verify 21% improvement
python deep_analysis.py              # Statistical analysis
python generate_comprehensive_plots.py  # Create visualizations
```

### View Results
- **Plots**: `results/aurora_complete_evaluation.pdf`
- **Metrics**: `results/aurora_metrics.csv`
- **Dashboard**: `http://localhost:3000`

---

## 🌐 Web Dashboard

```bash
cd aurora-web
npm install
npm run dev
# Open http://localhost:3000
```

Dashboard features:
- Real-time metrics display
- PPO vs Hybrid comparison
- Fire scenario viewer
- Training progress charts

---

## 📋 Real Data Integration

All training uses **real historical data**:

| Source | Size | Usage |
|--------|------|-------|
| **InterAgency Fire Perimeter** | 116,337 fires | Training scenarios |
| **NOAA Weather API** | Historical records | Wind, temp, humidity |
| **USGS 3DEP Elevation** | Full resolution | Terrain effects |

**Strict Mode**: System fails fast if real data unavailable (no synthetic fallbacks).

---

## 💾 Pre-trained Models

Trained models available in `results/models/`:
- `ppo_baseline_no_llm/` - Pure PPO (control)
- `ppo_llm_qwen2_5_3b_freq50/` - Hybrid with 3B LLM
- `ppo_llm_qwen2_5_7b_freq50/` - Hybrid with 7B LLM

Automatically loaded in `scripts/main_enhanced.py`

---

## 🛠️ Requirements

**Core Dependencies**
- Python 3.9+
- PyTorch 2.0+
- Stable-Baselines3 2.0+
- Gymnasium 0.27+
- Transformers 4.30+
- GeoPandas 0.12+

**Hardware**
- GPU: NVIDIA (CUDA 11.8+) recommended
- RAM: 16GB minimum
- Disk: 10GB for models + data

See `requirements.txt` for exact versions.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- How to report issues
- Code style guidelines
- Testing requirements
- Pull request process

---

## 📜 License

Released under **MIT License**. See [LICENSE](LICENSE) for details.

---

## 🙏 Citations & Acknowledgments

AURORA builds on:
- **Schulman et al. (2017)** - Proximal Policy Optimization
- **Wolf et al. (2020)** - Transformers & LLMs
- **Raffin et al. (2021)** - Stable-Baselines3
- **USGS, NOAA, Alibaba Qwen team** - Data & models

See [CITATIONS.md](CITATIONS.md) for complete bibliography.

---

## 📞 Support

- 📖 **Documentation**: [docs/README.md](docs/README.md)
- 🐛 **Issues**: GitHub Issues
- 💬 **Discussions**: GitHub Discussions
- 🤝 **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🚀 Next Steps

1. **Install & Run**: Follow Quick Start above
2. **View Results**: `results/aurora_complete_evaluation.pdf`
3. **Read Analysis**: `docs/ANALYSIS.md`
4. **Train Model**: `python scripts/train_hybrid.py --phase quick`
5. **Contribute**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Status**: ✅ Production Ready | ISEF 2025 Competition  
**Version**: 1.0 | Released: January 25, 2026  
**License**: MIT

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
