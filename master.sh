#!/bin/zsh

# Master script for AURORA project combining setup, training, validation, and simulation run commands

usage() {
    echo "Usage: $0 {setup|train|validate|run} [options]"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

mode=$1
shift

case "$mode" in
    setup)
        echo "============================================================"
        echo "AURORA Setup: Installing dependencies and running quick validation"
        echo "============================================================"
        
        # Write consolidated requirements to a temporary file
        REQUIREMENTS_FILE="/tmp/merged_requirements.txt"
        cat > "$REQUIREMENTS_FILE" << 'EOF'
# Consolidated AURORA requirements (merged from requirements files).
# This file is intended for development and training environments.

# Core Machine Learning
torch>=2.0.0
transformers>=4.37.0
stable-baselines3>=2.0.0

# Qwen Fine-Tuning (LoRA)
datasets>=2.14.0
peft>=0.7.0
accelerate>=0.24.0
bitsandbytes>=0.41.0

# Geospatial Data Processing
geopandas>=0.13.0
shapely>=2.0.0
rasterio>=1.3.0
pyproj>=3.5.0
fiona>=1.9.0

# Data Science & Numerical Computing
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0

# Weather & API Integration
requests>=2.31.0
urllib3>=2.0.0

# Training Utilities
tqdm>=4.65.0
tensorboard>=2.13.0
wandb>=0.15.0

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.14.0

# Gymnasium (RL Environment)
gymnasium>=0.28.0

# Optional / Utilities
openai
pathlib
EOF

        echo "Installing consolidated dependencies from $REQUIREMENTS_FILE..."
        pip install -r "$REQUIREMENTS_FILE"

        if [ -x "./quick_validate.sh" ]; then
            echo "Running quick validation..."
            ./quick_validate.sh
        else
            echo "quick_validate.sh not found or not executable. Skipping validation."
        fi

        rm "$REQUIREMENTS_FILE"
        echo "Setup completed."
        ;;
    train)
        echo "============================================================"
        echo "AURORA Hybrid PPO + Llama-2 Training"
        echo "============================================================"
        echo ""
        
        # Set HuggingFace token
        export HF_TOKEN="[REDACTED]"
        
        # Training parameters with defaults
        TIMESTEPS=${1:-10000}  # default 10k timesteps
        N_ENVS=${2:-1}         # default 1 environment
        LLM_FREQ=${3:-20}      # LLM guidance every 20 steps
        
        echo "Configuration:"
        echo "  Timesteps: $TIMESTEPS"
        echo "  Environments: $N_ENVS"
        echo "  LLM Frequency: every $LLM_FREQ steps"
        echo "  Model: meta-llama/Llama-2-7b-chat-hf"
        echo ""
        
        # Check for GPU
        if command -v nvidia-smi &> /dev/null; then
            echo "🎮 GPU detected:"
            nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
            echo ""
        else
            echo "⚠️  No GPU detected - will use CPU (slower)"
            echo ""
        fi
        
        echo "Starting training..."
        echo "============================================================"
        
        cd /Users/shauryamallampati/Desktop/ISEF
        ./.venv/bin/python train_hybrid.py \
            --timesteps $TIMESTEPS \
            --n_envs $N_ENVS \
            --llm_model meta-llama/Llama-3.2-1B-Instruct \
            --llm_backend gemini \
            --llm_freq $LLM_FREQ \
            --hf_token $HF_TOKEN \
            --verbose 1 >> logs/hybrid_training.log 2>&1
        
        echo ""
        echo "============================================================"
        echo "Training complete!"
        echo "Model saved to: results/aurora_hybrid_ppo_llm_model/"
        echo "Summary: results/hybrid_training_summary.json"
        echo "============================================================"
        ;;
    validate)
        echo "============================================================"
        echo "Running quick validation..."
        echo "============================================================"
        if [ -x "./quick_validate.sh" ]; then
            ./quick_validate.sh
        else
            echo "quick_validate.sh not found or not executable."
        fi
        ;;
    run)
        echo "============================================================"
        echo "Running simulation..."
        echo "============================================================"
        # You may adjust this command to run your simulation as needed
        python main_enhanced.py
        ;;
    *)
        usage
        ;;
esac
