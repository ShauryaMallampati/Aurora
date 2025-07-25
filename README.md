# 🌍 AURORA: Autonomous Wildfire Response Simulation

**AURORA** (Autonomous Unified Response Orchestration for Real-world Actions) is an AI-powered simulation system where autonomous drone agents learn to coordinate in containing wildfires. This project uses reinforcement learning in a custom-built fire environment based on real-world terrain types.

---

## 🔥 Project Overview

AURORA simulates the spread of wildfire over a 2D forested terrain and trains AI agents (drones) to suppress it using reinforcement learning.

* 🌲 Simulated terrain with forests, roads, and water
* 🔥 Fire spreads dynamically based on terrain and proximity
* 🤖 Multi-agent drones move, suppress fires, and learn optimal behavior via PPO
* 📈 Real-time visualization with matplotlib
* 🧠 Modular, extensible, and open to integration with LLMs or sensors

---

## 🗘️ Simulation Environment

The terrain is randomly generated from 4 cell types:

* `1 = Forest` (flammable)
* `2 = Road` (non-flammable)
* `3 = Water` (non-flammable)
* `0 = Empty` (no vegetation)

Fire starts in the center and spreads based on simple physics-inspired rules. Drones can move across the map and extinguish adjacent fires.

---

## 🧠 Drone Agents

Each drone observes a local 3x3 area and takes one of 6 actions:

```
[Stay, Move Up, Move Down, Move Left, Move Right, Suppress Fire]
```

Agents are rewarded for:

* ✅ Successfully suppressing fires
* ❌ Penalized for movement cost or idle steps during spread

Multi-agent training is handled using [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3).

---

## 🛠️ Project Structure

```
aurora/
├── env/
│   └── fire_sim.py         # Core wildfire spread logic
├── agents/
│   └── drone_agent.py      # Agent movement + suppression behavior
├── data/
│   ├── generate_map.py     # Terrain generator
│   └── terrain_map.npy     # Saved map file
├── utils/
│   └── visualizer.py       # Matplotlib-based simulation viewer
├── results/
│   └── fire_stats.png      # Plots of final fire area
├── train.py                # PPO training loop
├── main.py                 # Simulation runner
└── requirements.txt        # Dependencies
```

---

## 🚀 How to Run

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/aurora.git
cd aurora
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate Terrain

```bash
python data/generate_map.py
```

### 4. Run the Simulation

```bash
python main.py
```

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

## 🔮 Future Directions

* 🧱 Add wind + elevation models
* 🛰️ Integrate LLM strategic guidance
* 🎮 Build Unity-based 3D visualization
* 🌐 Use satellite fire/terrain data
* 🤝 Deploy swarm coordination strategies (e.g., graph-based MARL)

---

##
