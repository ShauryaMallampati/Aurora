# AURORA Quick Setup Guide

## Prerequisites
- Python 3.8+ 
- pip

## Installation

1. **Clone or download the project**
   ```bash
   cd aurora
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Project

### Option 1: Using the runner script (Recommended)
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run simulation
./run.sh simulate

# Train agents
./run.sh train

# Generate new terrain
./run.sh generate --size 25 --seed 123

# Show help
./run.sh help
```

### Option 2: Direct Python commands
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run simulation
python main.py

# Train agents
python train.py

# Generate terrain
python data/generate_map.py --size 20 --seed 42
```

## What You'll See

### Simulation Output
- **Console**: Real-time fire coverage and drone status
- **Images**: Individual simulation frames in `results/frame_XXX.png`
- **Statistics**: Fire coverage plot in `results/fire_stats.png`

### Training Output
- **Console**: Training progress and metrics
- **Model**: Trained PPO agent saved as `ppo_aurora_agent.zip`

## Troubleshooting

**Import Error**: Make sure you're in the virtual environment:
```bash
source .venv/bin/activate
```

**Module not found**: Reinstall dependencies:
```bash
pip install -r requirements.txt
```

**Permission denied**: Make runner script executable:
```bash
chmod +x run.sh
```

## Project Structure
```
aurora/
├── main.py              # Main simulation runner
├── train.py             # RL training script
├── run.sh               # Easy runner script
├── requirements.txt     # Python dependencies
├── agents/              # Drone agent implementation
├── env/                 # Fire simulation engine
├── data/                # Terrain generation and maps
├── utils/               # Visualization utilities
└── results/             # Output files and images
``` 