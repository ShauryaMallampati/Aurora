#!/bin/bash

# AURORA Project Runner Script
# This script makes it easy to run the AURORA wildfire simulation

# Activate virtual environment
source .venv/bin/activate

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Error: Virtual environment not activated. Please run: source .venv/bin/activate"
    exit 1
fi

# Function to show usage
show_usage() {
    echo "AURORA - Autonomous Unified Response Orchestration for Real-world Actions"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
echo "  simulate        Run the basic wildfire simulation with heuristic agents"
echo "  enhanced        Run the enhanced simulation with advanced features"
echo "  phase3          Run Phase 3 simulation with LLM strategy"
echo "  phase3-full     Run full Phase 3 with real data and failures"
echo "  train           Train reinforcement learning agents using PPO"
echo "  train-enhanced  Train enhanced PPO agents (50k timesteps)"
echo "  generate        Generate a new terrain map"
echo "  compare         Run comparison between different agent types"
echo "  test-llm        Test LLM integration capabilities"
echo "  test-ai         Test AI strategy agent with Hugging Face models"
echo "  3d-demo         Create 3D interactive visualization demo"
echo "  generate-data   Generate massive training dataset (500 scenarios)"
echo "  generate-real-data Generate REAL training dataset from NASA, NOAA, USGS"
echo "  web-server       Start enhanced web server with real-time monitoring"
echo "  google-earth     Create Google Earth-style 3D visualization"
echo "  interactive-earth Create interactive Google Earth-style visualization"
echo "  google-maps-api   Create AURORA Google Maps API integration"
echo "  monitor          Start real-time monitoring system"
echo "  monitor-dashboard Create real-time monitoring dashboard"
echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 simulate"
    echo "  $0 enhanced"
    echo "  $0 train-enhanced"
    echo "  $0 compare"
    echo "  $0 generate --size 25 --seed 123"
    echo ""
    echo "Enhanced Features:"
echo "  - Wind and weather effects"
echo "  - Battery and water management"
echo "  - Agent communication"
echo "  - Fault simulation"
echo "  - Comprehensive logging and analysis"
echo ""
echo "Phase 3 Features:"
echo "  - Real data integration (weather, terrain, historical fires)"
echo "  - LLM strategy layer for high-level coordination"
echo "  - Mission failure simulation"
echo "  - Enhanced trajectory tracking"
}

# Function to install dependencies
install_deps() {
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "Dependencies installed successfully!"
}

# Function to run basic simulation
run_basic_sim() {
    echo "Running basic AURORA simulation..."
    python main.py
}

# Function to run enhanced simulation
run_enhanced_sim() {
    echo "Running enhanced AURORA simulation..."
    if [[ -f "main_enhanced.py" ]]; then
        python main_enhanced.py
    else
        echo "Error: Enhanced simulation not found. Run 'train-enhanced' first."
        exit 1
    fi
}

# Function to run Phase 3 simulation
run_phase3_sim() {
    echo "Running Phase 3 AURORA simulation (LLM strategy)..."
    if [[ -f "main_phase3.py" ]]; then
        python main_phase3.py
    else
        echo "Error: Phase 3 simulation not found."
        exit 1
    fi
}

# Function to run full Phase 3 simulation
run_phase3_full() {
    echo "Running full Phase 3 AURORA simulation (real data + failures)..."
    if [[ -f "main_phase3.py" ]]; then
        python -c "
from main_phase3 import Phase3Simulation
sim = Phase3Simulation(
    scenario_name='california_2023',
    num_drones=3,
    use_real_data=True,
    use_llm_strategy=True,
    enable_failures=True
)
sim.run(max_steps=50, render_interval=10)
"
    else
        echo "Error: Phase 3 simulation not found."
        exit 1
    fi
}

# Function to run basic training
run_training() {
    echo "Running basic PPO training (1k timesteps)..."
    python train.py
}

# Function to run enhanced training
run_enhanced_training() {
    echo "Running enhanced PPO training (50k timesteps)..."
    python train.py
}

# Function to run comparison between different agent types
run_comparison() {
    echo "Running AURORA agent comparison..."
    
    # Run different agent types sequentially
    echo "Running heuristic agents..."
    python main_enhanced.py
    
    echo "Running PPO agents..."
    python main_enhanced.py
    
    echo "Running mixed agents..."
    python main_enhanced.py
    
    echo "Comparison complete! Check results/ directory for analysis."
}

# Main script logic
case "${1:-help}" in
    "simulate"|"sim")
        run_basic_sim
        ;;
    "enhanced"|"enh")
        run_enhanced_sim
        ;;
    "phase3")
        run_phase3_sim
        ;;
    "phase3-full")
        run_phase3_full
        ;;
    "train")
        run_training
        ;;
    "train-enhanced"|"train-enh")
        run_enhanced_training
        ;;
    "generate"|"gen")
        shift
        echo "Generating new terrain map..."
        python data/generate_map.py "$@"
        ;;
    "compare"|"comp")
        run_comparison
        ;;
    "test-llm")
        echo "Testing LLM integration..."
        python test_llm_integration.py
        ;;
    "test-ai")
        echo "Testing AI strategy agent..."
        source .venv/bin/activate
        export HF_TOKEN="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"
        python agents/llama_strategy_agent.py
        ;;
    "3d-demo")
        echo "Creating 3D interactive demo..."
        source .venv/bin/activate
        python utils/3d_visualizer.py
        ;;
    "generate-data")
        echo "Generating massive training dataset..."
        source .venv/bin/activate
        python data/massive_training_generator.py
        ;;
    "generate-real-data")
        echo "Generating REAL training dataset from NASA, NOAA, and USGS..."
        source .venv/bin/activate
        python data/real_data_generator.py
        ;;
    "web-server")
        echo "Starting AURORA web server for 3D visualizations..."
        source .venv/bin/activate
        python utils/web_server.py
        ;;
    "enhanced-server")
        echo "Starting AURORA enhanced web server with simulation API and interactive map..."
        source .venv/bin/activate
        python utils/enhanced_web_server.py
        ;;
    "process-fire-data")
        echo "Processing 50GB+ global fire data for 3D Earth interface..."
        source .venv/bin/activate
        python utils/global_fire_data_processor.py
        ;;
    "global-3d-earth")
        echo "Opening global 3D Earth fire visualization..."
        open http://localhost:8000/results/aurora_global_3d_earth.html
        ;;
    "google-earth")
        echo "Creating Google Earth-style 3D visualization..."
        source .venv/bin/activate
        python utils/google_earth_style.py
        ;;
    "interactive-earth")
        echo "Creating interactive Google Earth-style visualization..."
        source .venv/bin/activate
        python utils/interactive_google_earth.py
        ;;
    "monitor")
        echo "Starting AURORA real-time monitoring system..."
        source .venv/bin/activate
        python utils/real_time_monitor.py
        ;;
    "monitor-dashboard")
        echo "Creating real-time monitoring dashboard..."
        source .venv/bin/activate
        python utils/real_time_monitor.py
        echo "📊 Monitoring dashboard created!"
        echo "🌐 View at: http://localhost:8000/results/aurora_monitoring_dashboard.html"
        ;;
    "google-maps-api")
        echo "Creating AURORA Google Maps API integration..."
        source .venv/bin/activate
        python utils/aurora_google_maps_working.py
        ;;
    "install"|"deps")
        install_deps
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac 