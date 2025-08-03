# 🌍 AURORA: Autonomous Wildfire Response Simulation

**AURORA** (Autonomous Unified Response Orchestration for Real-world Actions) is an AI-powered simulation system where autonomous drone agents learn to coordinate in containing wildfires. This project uses reinforcement learning in a custom-built fire environment based on real-world terrain types.

---

## 🔥 Project Overview

AURORA simulates the spread of wildfire over a 2D forested terrain and trains AI agents (drones) to suppress it using reinforcement learning.

* 🌲 Simulated terrain with forests, roads, and water
* 🔥 Fire spreads dynamically based on terrain, wind, elevation, and fuel density
* 🤖 Multi-agent drones move, suppress fires, and learn optimal behavior via PPO
* 📈 Real-time visualization with matplotlib and interactive web interfaces
* 🧠 LLaMA integration for strategic decision-making
* 🌍 Real-world data integration (NASA FIRMS, NOAA Weather, USGS Elevation)

---

## 🗘️ Simulation Environment

The terrain is randomly generated from 4 cell types:

* `1 = Forest` (flammable)
* `2 = Road` (non-flammable)
* `3 = Water` (non-flammable)
* `0 = Empty` (no vegetation)

Fire starts in the center and spreads based on realistic physics-inspired rules including wind effects, elevation changes, and fuel density. Drones can move across the map and extinguish adjacent fires.

---

## 🧠 Drone Agents

Each drone observes a local 3x3 area and takes one of 8 actions:

```
[Stay, Move Up, Move Down, Move Left, Move Right, Suppress Fire, Scan, Communicate]
```

Agents are rewarded for:

* ✅ Successfully suppressing fires
* ❌ Penalized for movement cost or idle steps during spread
* 🔋 Battery and water management
* 📡 Communication with other agents

Multi-agent training is handled using [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3).

---

## 🛠️ Project Structure

```
aurora/
├── env/
│   └── fire_sim.py              # Core wildfire spread logic with wind/elevation
├── agents/
│   ├── drone_agent.py           # Enhanced drone agent with resource management
│   ├── llama_strategy_agent.py  # LLaMA integration for strategic decisions
│   ├── llm_strategy_agent.py    # LLM strategy coordination
│   └── working_llama_agent.py   # Working LLaMA agent implementation
├── data/
│   ├── generate_map.py          # Terrain generator
│   ├── real_data_integration.py # NASA/NOAA/USGS data integration
│   ├── real_data_generator.py   # Real data processing
│   ├── massive_training_generator.py # Training data generation
│   └── terrain_map.npy          # Saved map file
├── utils/
│   ├── visualizer.py            # Matplotlib-based simulation viewer
│   ├── 3d_visualizer.py         # 3D terrain visualization
│   ├── enhanced_web_server.py   # Interactive web server
│   ├── aurora_google_maps_api.py # Google Maps integration
│   ├── interactive_google_earth.py # Google Earth-style interface
│   ├── google_earth_style.py    # Earth visualization styling
│   └── global_fire_data_processor.py # Global fire data processing
├── results/
│   ├── logs/                    # Simulation logs and metrics
│   ├── best_model/              # Best trained PPO model
│   └── *.html                   # Interactive web interfaces
├── ppo_aurora_agent/            # Trained PPO model files
├── train.py                     # PPO training script
├── main_enhanced.py             # Enhanced simulation runner
├── main_phase3.py               # Phase 3 simulation with real data
├── main.py                      # Basic simulation runner
├── run.sh                       # Setup and run script
├── index.html                   # Main web dashboard
└── requirements.txt             # Dependencies
```

---

## 🚀 How to Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Terrain

```bash
python data/generate_map.py
```

### 3. Run the Simulation

```bash
# Basic simulation
python main.py

# Enhanced simulation with real data
python main_enhanced.py

# Phase 3 simulation with full features
python main_phase3.py
```

### 4. Start Web Server

```bash
python utils/enhanced_web_server.py
```

Then visit: http://localhost:8000

### 5. Train the Agents

```bash
python train.py
```

---

## 📈 Sample Output

* 🔴 Red = burning
* 🔵 Blue = water
* ⚫️ Black = burnt
* 🟩 Green = untouched forest
* 🟨 Yellow = drones

The simulation updates step-by-step with fire spread and agent movement visualized.

---

## 🔮 Advanced Features

* 🧱 Wind + elevation models for realistic fire spread
* 🛰️ LLaMA integration for strategic guidance
* 🌐 Real NASA FIRMS satellite data integration
* 🎮 Interactive 3D visualization
* 🤝 Multi-agent coordination strategies
* 📊 Comprehensive logging and analysis

---

## 📊 Results

The system generates:
- Real-time simulation visualizations
- Interactive web dashboards
- 3D terrain and fire spread animations
- Comprehensive performance metrics
- Trained PPO models for autonomous agents

---

## 🏆 ISEF Project

This represents a cutting-edge AI research project suitable for top-tier science fair competition, featuring:
- Real government data sources (NASA, NOAA, USGS)
- Advanced reinforcement learning techniques
- State-of-the-art LLM integration
- Comprehensive experimental logging
- Interactive visualization systems
