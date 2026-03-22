# AURORA

## Wildfire containment with hybrid PPO and LLM guidance

AURORA is a research codebase for training autonomous drone swarms to contain wildfires. The main system combines PPO for low-level control with optional LLM-based strategic guidance.

The repository includes:

- training entrypoints for PPO-only and hybrid runs
- evaluation helpers and callbacks
- real-data ingestion for fire perimeters, weather, and terrain features
- an ablation-study scaffold under `results/ablation_study/`

## Current status

The implementation pipeline is present and the reviewer-facing package has been scaffolded. The current empirical status is documented in:

- `results/ablation_study/REPO_AUDIT.md`
- `results/ablation_study/FINAL_AUDIT.md`
- `results/ablation_study/README.md`

Use those files as the source of truth for which experiment families are complete and which are still pending.

## Quick start

### Prerequisites

- Python 3.9+
- GPU recommended for larger training runs
- 16 GB RAM minimum

### Install

```bash
git clone https://github.com/yourusername/AURORA.git
cd AURORA

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python preflight.py
```

### Run a short training job

```bash
python train_hybrid.py --phase quick
```

### Run the simulator

```bash
python main_enhanced.py
```

### Run the web dashboard

```bash
cd aurora-web
npm install
npm run dev
```

## API keys

Local environment files are ignored by git. Keep credentials out of tracked files.

### Python backend

```bash
export HF_TOKEN=<your_huggingface_token>
```

### Web dashboard

Create `aurora-web/.env.local` with:

```bash
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=<your_google_maps_browser_key>
NEXT_PUBLIC_SUPABASE_URL=<your_supabase_url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your_supabase_anon_key>
```

A tracked example file is available at `aurora-web/.env.example`.

## Repository layout

```text
AURORA/
├── train.py
├── train_hybrid.py
├── evaluate.py
├── callbacks.py
├── agents/
├── configs/
├── data/
├── docs/
├── results/
└── aurora-web/
```

## Training and evaluation

Typical entrypoints:

- `python train.py` for PPO-only training
- `python train_hybrid.py` for hybrid PPO + strategist training
- `python evaluate.py` for evaluation helpers
- `python run_ablation_suite.py --mode audit` for the ablation-study audit flow

Phase definitions live in `configs/training_phases.yaml`. The current ablation-study settings live in `configs/ablation_study.yaml`.

## Real-data integration

The codebase can integrate:

- InterAgency Fire Perimeter data
- NOAA weather data
- terrain-derived features used by the simulator

Data loading and strict-mode behavior are summarized in `results/ablation_study/REPO_AUDIT.md`.

## Documentation

- `docs/ABSTRACT.md`
- `docs/ANALYSIS.md`
- `docs/README.md`
- `results/ablation_study/README.md`

## Requirements

Core dependencies include PyTorch, Stable-Baselines3, Gymnasium, Transformers, and GeoPandas. See `requirements.txt` for the exact versions used by the current pipeline.

## Contributing

Issues and pull requests are welcome. If you add a data source, benchmark, or new experiment variant, update the relevant documentation under `docs/` or `results/ablation_study/`.

## License

MIT. See `LICENSE`.
