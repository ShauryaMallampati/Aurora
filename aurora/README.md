# AURORA: Autonomous Wildfire Response System

AURORA (Autonomous Unified Response Orchestration for Real-time Action) is an advanced AI-powered wildfire suppression system that uses reinforcement learning to train autonomous drone agents to coordinate and contain wildfires effectively.

## 🚀 Project Overview

AURORA simulates the spread of wildfire over realistic 2D forested terrain and trains AI agents (drones) to suppress it using state-of-the-art reinforcement learning techniques. The system integrates real-world fire data, advanced AI models, and comprehensive simulation capabilities.

## 🌟 Key Features

### 🔥 Advanced Fire Simulation
- **Realistic Fire Spread**: Dynamic fire propagation based on terrain, wind, humidity, and elevation
- **Weather Integration**: Wind direction, intensity, temperature, and humidity effects
- **Terrain Modeling**: Forests, roads, water bodies, and elevation maps
- **Fuel Density**: Variable flammability based on terrain type

### 🤖 AI-Powered Drone Agents
- **PPO Reinforcement Learning**: Proximal Policy Optimization for optimal behavior
- **Multi-Agent Coordination**: Drones communicate and coordinate strategies
- **Resource Management**: Battery and water level tracking
- **Fault Tolerance**: Malfunction simulation and recovery
- **Sensor Simulation**: Limited field of view and environmental scanning

### 🧠 LLM Strategy Integration
- **Llama Model**: Advanced AI strategy generation using Hugging Face models
- **Real-time Analysis**: Fire assessment and suppression planning
- **Adaptive Strategies**: Dynamic strategy adjustment based on conditions
- **Risk Assessment**: Evacuation recommendations and threat evaluation

### 📊 Real-World Data Integration
- **NASA FIRMS Data**: 50GB+ of real fire detection data
- **Global Coverage**: Fire data from multiple satellites and regions
- **Shapefile Processing**: Geographic data extraction and analysis
- **Country Classification**: Automatic fire location identification

### 🗺️ Interactive Visualization
- **3D Global Earth**: Leaflet.js-based interactive map
- **Real-time Metrics**: Fire coverage, suppression progress, drone status
- **Country Filtering**: Filter fires by geographic region
- **Simulation Controls**: Start, stop, and reset simulation capabilities

### 📈 Comprehensive Logging
- **Performance Metrics**: Fire coverage, suppression efficiency, agent coordination
- **Training Logs**: PPO training progress and model checkpoints
- **Simulation Analysis**: Detailed step-by-step logging
- **Visualization**: Matplotlib-based performance plots

## 🏗️ System Architecture

```
AURORA/
├── agents/                 # AI agent implementations
│   ├── drone_agent.py     # Enhanced drone agent with RL
│   └── llama_strategy_agent.py  # LLM-based strategy agent
├── env/                   # Simulation environment
│   └── fire_sim.py       # Advanced fire simulation engine
├── utils/                 # Utility modules
│   ├── global_fire_data_processor.py  # Real data processing
│   └── enhanced_web_server.py  # Web interface server
├── results/               # Output files and visualizations
│   └── aurora_global_3d_earth.html  # Interactive 3D map
├── data/                  # Training and simulation data
├── Fire_Data/            # Real NASA FIRMS fire datasets (50GB+)
├── train.py              # PPO training script
├── main_enhanced.py      # Enhanced simulation runner
└── requirements.txt      # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- 8GB+ RAM (for large datasets)
- Hugging Face token for LLM access

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ShauryaMallampati/ISEF.git
cd ISEF/aurora
```

2. **Set up virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up Hugging Face token**
```bash
export HF_TOKEN="your_huggingface_token_here"
```

### Running the System

1. **Process real fire data**
```bash
python utils/global_fire_data_processor.py
```

2. **Train PPO agents**
```bash
python train.py --episodes 10000 --save-model
```

3. **Run enhanced simulation**
```bash
python main_enhanced.py --num-drones 5 --steps 100
```

4. **Start web interface**
```bash
python utils/enhanced_web_server.py
```

5. **Open 3D Earth interface**
```bash
open http://localhost:8000/results/aurora_global_3d_earth.html
```

## 🔬 Research Components

### Reinforcement Learning
- **Environment**: Custom Gymnasium environment with 6-channel observations
- **Actions**: 8 discrete actions (move, suppress, scan, communicate)
- **Rewards**: Sophisticated reward shaping for suppression, survival, cooperation
- **Algorithm**: PPO with parameter sharing for multi-agent learning

### AI Strategy Generation
- **Model**: Llama-3.3-70B-Instruct for high-level strategy
- **Input**: Fire state, terrain, weather, agent positions
- **Output**: Deployment strategies, suppression plans, risk assessments
- **Integration**: Real-time strategy updates during simulation

### Real Data Processing
- **Datasets**: 18 NASA FIRMS datasets (50GB+)
- **Format**: Shapefile (.shp, .dbf, .shx) processing
- **Extraction**: Coordinates, intensities, satellite types, dates
- **Integration**: Real fire data in simulation and visualization

## 📊 Performance Metrics

The system tracks comprehensive metrics including:
- **Fire Coverage**: Percentage of terrain affected by fire
- **Suppression Efficiency**: Fires extinguished per time step
- **Agent Coordination**: Communication effectiveness
- **Resource Utilization**: Battery and water consumption
- **Training Progress**: PPO learning curves and convergence

## 🎯 ISEF Research Standards

This project meets ISEF-level research standards with:
- ✅ **Real AI Training**: Actual PPO model training with checkpoints
- ✅ **Real Data Integration**: 50GB+ of NASA FIRMS fire data
- ✅ **Advanced Simulation**: Realistic fire spread with environmental factors
- ✅ **LLM Integration**: Llama model for strategic decision-making
- ✅ **Comprehensive Logging**: Detailed metrics and analysis
- ✅ **Interactive Interface**: Real-time visualization and control

## 🤝 Contributing

This is a research project for ISEF (International Science and Engineering Fair). The system demonstrates advanced AI techniques for real-world disaster response applications.

## 📄 License

This project is developed for educational and research purposes as part of ISEF competition.

## 🔗 Links

- **GitHub Repository**: https://github.com/ShauryaMallampati/ISEF
- **NASA FIRMS Data**: https://firms.modaps.eosdis.nasa.gov/
- **Hugging Face Models**: https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct

---

**AURORA: Advancing Autonomous Wildfire Response Through AI Innovation** 🔥🤖🚁