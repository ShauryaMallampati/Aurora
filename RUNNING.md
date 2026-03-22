# Aurora Project - Running Guide

## Installation Status ✅
- **Node.js (web)**: ✅ Installed (in `aurora-web/node_modules`)
- **Python (ML)**: ✅ Installed (in `.venv` using Python 3.11)

## Running the Project

### 1. Start the Web Dashboard
```bash
npm run dev
# Opens dashboard at http://localhost:3001 (or 3000 if 3001 is free)

# Alternate command (same result)
./master.sh web
```

### 2. Run Python Scripts

Activate the venv first OR prepend the Python path:

```bash
# Option A: Activate venv (recommended for interactive work)
source .venv/bin/activate
python train_hybrid.py --phase quick

# Option B: Direct venv path (for single commands)
.venv/bin/python train_hybrid.py --phase quick
```

### 3. Available Commands

```bash
# Quick training (10-15 min)
.venv/bin/python train_hybrid.py --phase quick

# Full training (~12-20 hours on GPU)
.venv/bin/python train_hybrid.py --phase full

# Run simulation with trained model
.venv/bin/python main_enhanced.py

# Run evaluation
.venv/bin/python evaluate.py

# Preflight validation
.venv/bin/python preflight.py
```

## 🚨 Note on Geospatial Packages

The full `requirements.txt` includes Fiona, Rasterio, and Geopandas which failed to install due to GDAL dependency issues on macOS. These are only needed for:
- Loading real fire perimeter data
- Advanced terrain analysis

For quick training without real data loading, use `requirements-core.txt` (already installed).

To install full stack later with GDAL support:
```bash
# Requires Homebrew + system dependencies
brew install gdal
pip install -r requirements.txt
```

## Quick Test

Verify everything is set up:
```bash
.venv/bin/python -c "import torch; import transformers; print('✅ ML stack ready')"
npm run dev  # Should open http://localhost:3001
```

---

**Next steps**: Run a quick training or start the web dashboard!
