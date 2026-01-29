# AURORA - Autonomous Unified Response Orchestration for Real-world Actions

## Wildfire containment with LLM-guided PPO

AURORA trains autonomous drone swarms to contain wildfires using a hybrid stack: **Large Language Models (LLMs)** for high-level guidance + **PPO** for control. The whole point: get smarter strategies on hard fires without babysitting the agent.

**Key result:** +21% improvement over PPO baseline, with gains concentrated on hard scenarios (not just easy wins).

---

## What this is (quick vibe check)

- **Faster response:** 2-5 minutes vs 15-30 minutes in traditional workflows
- **Strategic AI:** LLM guidance informed by 116K historical fires
- **Multi-drone suppression:** coordinated perimeter attack, not single-drone whack-a-mole
- **Real data:** NOAA weather + USGS terrain + InterAgency fire perimeters

### Key results

| Metric | PPO Baseline | AURORA Hybrid | Improvement |
|--------|--------------|---------------|-------------|
| Final Return | 34.57 | 41.84 | **+21.0%** |
| Hard Scenarios | 36.26 | 58.85 | **+62.3%** |
| Easy Scenarios | 42.33 | 42.33 | 0.0% (already optimal) |
| Episodes Trained | 20,028 | 17,453 | 53,055 total |

**Takeaway:** The gains show up where strategy actually matters.

---

## Quick start (about 5 minutes)

### Prereqs
- Python 3.9+
- GPU recommended (CUDA 11.8+)
- 16GB RAM minimum

### Install

```bash
# Clone
git clone https://github.com/yourusername/AURORA.git
cd AURORA

# Virtual env
python -m venv venv
source venv/bin/activate

# Deps
pip install -r requirements.txt

# Sanity check
python preflight.py
```

### Run a quick sim

```bash
# Quick training run (10-15 min)
python train_hybrid.py --phase quick

# Sim with the trained model
python main_enhanced.py

# Web dashboard
cd aurora-web && npm run dev
# Open http://localhost:3000
```

---

## API keys (only if you want the full stack)

Create these locally (they are gitignored).

### Python backend (`/.env` or export in terminal)

```bash
# Hugging Face (needed for gated LLMs)
# Get one at: https://huggingface.co/settings/tokens
export HF_TOKEN=hf_your_token_here
```

### Web dashboard (`/aurora-web/.env.local`)

```bash
# Google Maps (map tiles)
# Get one at: https://console.cloud.google.com/apis/credentials
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_key

# Supabase (optional run history)
# Get these at: https://supabase.com/dashboard
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

**Heads up:** `.env` files are gitignored so keys stay local.

---

## Docs

- `docs/ABSTRACT.md` - 250-word research abstract
- `docs/ANALYSIS.md` - full analysis + results
- `docs/README.md` - doc index

---

## Project layout (actual repo)

```
AURORA/
+-- README.md
+-- LICENSE
+-- requirements.txt
|
+-- train_hybrid.py              # Main training script
+-- train.py                     # PPO-only training
+-- main_enhanced.py             # Run sims + logging
+-- simulate.py                  # Lightweight sim entry
+-- evaluate.py                  # Evaluation configs + helpers
+-- validate.py                  # Data validation
+-- preflight.py                 # Setup checks
+-- callbacks.py                 # Training callbacks
|
+-- agents/
|   +-- drone_agent.py           # Individual drone logic
|   +-- hybrid_ppo_llm_agent.py  # PPO + LLM agent
|
+-- data/
|   +-- real_data_integration_complete.py
|
+-- configs/
|   +-- training_phases.yaml
|
+-- results/                     # Outputs (some tracked via LFS)
|
+-- docs/
|   +-- ABSTRACT.md
|   +-- ANALYSIS.md
|   +-- README.md
|
+-- utils/
|   +-- visualizer.py
|
+-- aurora-web/                  # Web dashboard
```

---

## How it works

**1) LLM (Qwen 2.5)**
- Reads the fire state every ~50 steps
- Suggests priority zones + coordination targets

**2) PPO policy**
- Executes actions (movement + suppression)
- Learns from rewards over episodes

**Net effect:** strategy + control beats pure PPO by ~21%.

---

## Training

```bash
# Quick
python train_hybrid.py --phase quick

# Full (GPU recommended)
python train_hybrid.py --phase full

# Phased
python train_hybrid.py --phase phase_a
python train_hybrid.py --phase phase_b
python train_hybrid.py --phase phase_c
```

---

## Evaluation

```bash
# Run eval helpers (writes/reads results/metrics.csv)
python evaluate.py
```

**Artifacts:**
- `results/aurora_complete_evaluation.pdf`
- `results/aurora_metrics.csv`
- Dashboard at `http://localhost:3000`

---

## Web dashboard

```bash
cd aurora-web
npm install
npm run dev
# Open http://localhost:3000
```

Dashboard includes:
- Live metrics
- PPO vs Hybrid comparison
- Fire scenario viewer
- Training charts

---

## Real data integration (no fake wins)

| Source | Size | Usage |
|--------|------|-------|
| InterAgency Fire Perimeter | 116,337 fires | Training scenarios |
| NOAA Weather API | Historical records | Wind, temp, humidity |
| USGS 3DEP Elevation | Full resolution | Terrain effects |

**Strict mode:** if real data is missing, the system fails fast.

---

## Pretrained models

Stored under `results/`:
- `ppo_baseline_no_llm/`
- `ppo_llm_qwen2_5_3b_freq50/`
- `ppo_llm_qwen2_5_7b_freq50/`

Loaded automatically in `main_enhanced.py`.

---

## Requirements

**Core deps**
- Python 3.9+
- PyTorch 2.0+
- Stable-Baselines3 2.0+
- Gymnasium 0.27+
- Transformers 4.30+
- GeoPandas 0.12+

**Hardware**
- NVIDIA GPU recommended (CUDA 11.8+)
- 16GB RAM minimum
- ~10GB disk for models + data

See `requirements.txt` for exact versions.

---

## Contributing

Issues + PRs welcome. If you add data sources or benchmarks, please document them in `docs/ANALYSIS.md`.

---

## License

MIT - see `LICENSE`.

---

**ISEF 2025**  |  **Version 1.0**  |  **January 2025**
