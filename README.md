# AURORA: Autonomous Unified Response Orchestration for Real-world Actions

## Wildfire Containment Through Hybrid LLM-Guided Reinforcement Learning

AURORA is an AI system that trains autonomous drone swarms to contain wildfires using a hybrid architecture combining **Large Language Models (LLMs)** with **Proximal Policy Optimization (PPO)** reinforcement learning.

**Key Achievement:** 21% improvement over baseline RL through strategic LLM guidance on 116K real historical fires.

---

## What is AURORA?

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

## Quick Start (5 minutes)

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
python preflight.py
```

### Run a Quick Simulation

```bash
# Train for a few steps (10 min)
python train_hybrid.py --phase quick

# Run with trained model
python main_enhanced.py

# View web dashboard
cd aurora-web && npm run dev
# Open http://localhost:3000
```

---

## Documentation

- **[docs/ABSTRACT.md](docs/ABSTRACT.md)** - Research abstract (250 words)
- **[docs/ANALYSIS.md](docs/ANALYSIS.md)** - Complete analysis & results

---

## Project Structure

```
AURORA/
├── README.md                           # This file
├── LICENSE                             # MIT License
├── CITATIONS.md                        # Data sources & citations
├── requirements.txt                    # Dependencies
│
├── train_hybrid.py                     # Main training script
├── main_enhanced.py                    # Run simulations
├── evaluation_battery.py               # Evaluation suite
├── callbacks.py                        # Training callbacks
├── preflight.py                        # Setup validation
├── validate_strict_mode.py             # Data validation
│
├── agents/                             # Agent controllers
│   ├── drone_agent.py                  # Individual drone
│   └── hybrid_ppo_llm_agent.py         # Hybrid PPO+LLM agent
│
├── data/                               # Real data integration
│   └── real_data_integration_complete.py
│
├── configs/
│   └── training_phases.yaml            # Training config
│
├── results/                            # Outputs
│   ├── models/                         # Trained weights
│   ├── checkpoints/                    # Checkpoints
│   └── aurora_metrics.csv              # Metrics
│
├── docs/                               # Documentation
│   ├── ABSTRACT.md
│   └── ANALYSIS.md
│
├── utils/                              # Visualization
│   ├── visualizer.py
│   └── 3d_visualizer.py
│
└── aurora-web/                         # Web dashboard
    └── src/
```

---

## How AURORA Works

### Hybrid Architecture

**1. Large Language Model (Qwen 2.5)**
- Analyzes fire state every 50 steps
- Provides strategic guidance to drones
- Recommends priority zones

**2. Reinforcement Learning (PPO)**
- Executes movement and suppression actions
- Adapts to real-time fire dynamics
- Improves through episode rewards

**Result**: LLM strategy + PPO learning = 21% improvement

---

## 📊 Training

### Quick Training (10-30 min)
```bash
python train_hybrid.py --phase quick
```

### Full Training (12 hours on GPU)
```bash
python train_hybrid.py --phase full
```

### Phased Training
```bash
# Phase A: 2-3 hours
python train_hybrid.py --phase phase_a

# Phase B: 3-4 hours
python train_hybrid.py --phase phase_b

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

Automatically loaded in `main_enhanced.py`

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

See [CITATIONS.md](CITATIONS.md) for issues, contributions, and pull requests.

---

## 📜 License

MIT License. See [LICENSE](LICENSE).

---

## 🙏 Citations

See [CITATIONS.md](CITATIONS.md) for data sources, libraries, and how to cite.

---

**ISEF 2025 Competition**  
**Version**: 1.0 | January 2025
