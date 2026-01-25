# AURORA Documentation Index

Welcome to AURORA's documentation. Start here to navigate all project resources.

## 📚 Getting Started

1. **[README.md](../README.md)** - Project overview, quick start, installation
2. **[ABSTRACT.md](./ABSTRACT.md)** - Research abstract for ISEF competition
3. **[CONTRIBUTING.md](../CONTRIBUTING.md)** - How to contribute to the project
4. **[CITATIONS.md](../CITATIONS.md)** - All data sources, libraries, and citations

## 🔬 Technical Documentation

- **[ANALYSIS.md](./ANALYSIS.md)** - Complete analysis of 21% improvement with verification
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture and design details
- **[AURORA_vs_TRADITIONAL_FIREFIGHTING.md](../AURORA_vs_TRADITIONAL_FIREFIGHTING.md)** - Comparison to real-world firefighting methods

## 📊 Results & Evaluation

- **[Evaluation Plots](../results/aurora_complete_evaluation.pdf)** - 4-page PDF with all visualization plots
- **[Metrics Data](../results/aurora_metrics.csv)** - Raw metrics in CSV format
- **analysis/** - Detailed analysis documents
  - `SEED_DIFFICULTY_ANALYSIS.md` - Proof that seed difficulty is natural, not engineered
  - `21_PERCENT_EXPLAINED.md` - Executive summary of the improvement

## 🎯 Competition Materials

Located in `competition/` folder (for ISEF judges):
- `ISEF_JUDGE_GUIDE.md` - Guide for judges
- `ISEF_MASTER_PLAN.md` - Competition planning
- `PRESENTATION_NOTES.md` - Presentation guidance

## 🔧 How-To Guides

### Training a Model
See: [../scripts/train_hybrid.py](../scripts/train_hybrid.py) and [../README.md](../README.md#training)

### Running Evaluation
```bash
python scripts/evaluation_battery.py
```
See: [../scripts/evaluation_battery.py](../scripts/evaluation_battery.py)

### Reproducing Analysis
```bash
cd scripts/analysis/
python verify_21_percent.py
python deep_analysis.py
```

### Running Web Dashboard
```bash
cd aurora-web
npm install
npm run dev
# Open http://localhost:3000
```

## 📋 File Structure

```
AURORA/
├── README.md                              # Start here
├── LICENSE                               # MIT License
├── CONTRIBUTING.md                       # How to contribute
├── CITATIONS.md                          # All citations & acknowledgments
├── requirements.txt                      # Dependencies
│
├── docs/                                 # Documentation (this folder)
│   ├── README.md                        # This file
│   ├── ABSTRACT.md                      # Research abstract
│   ├── ANALYSIS.md                      # Complete analysis
│   ├── ARCHITECTURE.md                  # System design
│   ├── competition/                     # ISEF-specific
│   ├── internal/                        # Internal planning notes
│   └── analysis/                        # Detailed analysis
│
├── src/                                  # Source code
│   ├── agents/                          # RL agents (PPO, Hybrid)
│   ├── env/                             # Fire simulation environment
│   ├── data/                            # Data loaders
│   └── utils/                           # Utilities
│
├── scripts/                              # Training & utilities
│   ├── train_hybrid.py                 # Main training script
│   ├── main_enhanced.py                # Inference
│   ├── evaluation_battery.py           # Evaluation
│   ├── analysis/                       # Analysis scripts
│   └── colab/                          # Colab-specific
│
├── configs/                              # Configuration files
├── results/                              # Generated outputs
│   ├── models/                         # Trained models
│   ├── checkpoints/                    # Training checkpoints
│   ├── aurora_complete_evaluation.pdf  # 4-page evaluation plots
│   └── aurora_metrics.csv              # Metrics data
│
├── aurora-web/                           # Next.js web dashboard
└── .github/                              # GitHub config
```

## 🚀 Quick Links

| Need | Link |
|------|------|
| **Install & run** | [README.md](../README.md) |
| **Understand results** | [ANALYSIS.md](./ANALYSIS.md) |
| **Learn architecture** | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| **Compare to real world** | [../AURORA_vs_TRADITIONAL_FIREFIGHTING.md](../AURORA_vs_TRADITIONAL_FIREFIGHTING.md) |
| **Contribute code** | [../CONTRIBUTING.md](../CONTRIBUTING.md) |
| **Cite this project** | [../CITATIONS.md](../CITATIONS.md) |
| **See plots & metrics** | [../results/](../results/) |

## 📖 Reading Order for New Users

1. Start: [../README.md](../README.md)
2. Understand: [ABSTRACT.md](./ABSTRACT.md)
3. Deep dive: [ANALYSIS.md](./ANALYSIS.md)
4. Technical: [ARCHITECTURE.md](./ARCHITECTURE.md)
5. Real-world: [../AURORA_vs_TRADITIONAL_FIREFIGHTING.md](../AURORA_vs_TRADITIONAL_FIREFIGHTING.md)
6. Develop: [../CONTRIBUTING.md](../CONTRIBUTING.md)

## ❓ FAQ

**Q: How do I train the model?**  
A: See [../README.md#training](../README.md#training) and [../scripts/train_hybrid.py](../scripts/train_hybrid.py)

**Q: What's the 21% improvement?**  
A: See [ANALYSIS.md](./ANALYSIS.md) for complete verification

**Q: How do I cite AURORA?**  
A: See [../CITATIONS.md](../CITATIONS.md) for citation formats

**Q: Can I contribute?**  
A: Yes! See [../CONTRIBUTING.md](../CONTRIBUTING.md)

**Q: Where's the training data?**  
A: Real fire perimeters in `data/` folder, managed with Git LFS

**Q: How do I run the web dashboard?**  
A: See [../aurora-web/README.md](../aurora-web/README.md)

## 📞 Support

- **Issues**: Create a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Contributions**: See [../CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Last Updated**: January 25, 2026  
**Current Version**: 1.0

For more information, visit the main [README.md](../README.md)
