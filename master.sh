#!/bin/zsh

# Master script for AURORA ISEF 2025 - Phased training support

usage() {
    echo "Usage: $0 {setup|train|validate|run} [options]"
    echo ""
    echo "Commands:"
    echo "  setup          - Install dependencies and validate environment"
    echo "  train          - Train AURORA model with phased training"
    echo "  validate       - Run validation on trained model"
    echo "  run            - Run simulation with trained model"
    echo ""
    echo "Train Options:"
    echo "  --phase <name> - Training phase: phase_a, phase_b, phase_c, phase_d, full, quick"
    echo "  --timesteps N  - Custom number of timesteps (overrides phase)"
    echo "  --n_envs N     - Number of parallel environments (default: 4)"
    echo "  --llm_freq N   - LLM guidance frequency (default: 50)"
    echo ""
    echo "Examples:"
    echo "  $0 train --phase full               # All phases (13M steps)"
    echo "  $0 train --phase phase_a            # Phase A only (2M steps)"
    echo "  $0 train --phase quick              # Quick test (500K steps)"
    echo "  $0 train --timesteps 10000000       # Custom 10M steps"
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
        echo "🔥 AURORA ISEF 2025 - Hybrid PPO + Qwen Training"
        echo "============================================================"
        echo ""
        
        # Set HuggingFace token
        export HF_TOKEN="[REDACTED]"
        
        # Create logs directory if it doesn't exist
        mkdir -p logs
        
        # Pass all arguments to train_hybrid.py
        # This supports --phase, --timesteps, --n_envs, etc.
        echo "Starting training with arguments: $@"
        echo "Log file: logs/hybrid_training.log"
        echo ""
        
    # Stream output to both console and log file so interactive per-step updates are visible
    python train_hybrid.py "$@" 2>&1 | tee -a logs/hybrid_training.log
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Training completed successfully!"
            echo "📂 Model saved to: results/aurora_hybrid_ppo_llm_model/"
            echo "📊 Training log: logs/hybrid_training.log"
        else
            echo ""
            echo "❌ Training failed. Check logs/hybrid_training.log for details."
            exit 1
        fi
        ;;
    validate)
        echo "============================================================"
        echo "🔍 AURORA Model Validation"
        echo "============================================================"
        echo "Running validation on trained model..."
        
        if [ -x "./validate_strict_mode.py" ]; then
            python validate_strict_mode.py "$@"
        else
            echo "validate_strict_mode.py not found"
            echo "Using quick_validate.sh instead..."
            if [ -x "./quick_validate.sh" ]; then
                ./quick_validate.sh
            else
                echo "❌ No validation script found."
                exit 1
            fi
        fi
        ;;
    run)
        echo "============================================================"
        echo "🚁 Running AURORA Simulation"
        echo "============================================================"
        python main_enhanced.py "$@"
        ;;
    *)
        usage
        ;;
esac
