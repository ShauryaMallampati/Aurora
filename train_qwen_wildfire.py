"""
Fine-tune Qwen2.5-1.5B-Instruct on AURORA Wildfire Strategy Data

This script:
1. Loads your real wildfire scenarios from data/real_training_data/
2. Converts them into instruction-tuning format
3. Fine-tunes Qwen2.5-1.5B-Instruct using LoRA (parameter-efficient)
4. Saves the trained adapter for use in simulations

Training approach: LoRA (Low-Rank Adaptation)
- Only trains ~1-2% of parameters
- Fast training (hours instead of days)
- Works on single GPU (or even CPU with patience)
- Preserves base model knowledge
"""

import json
import os
from typing import List, Dict, Any
import numpy as np

try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForSeq2Seq
    )
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    import torch
    TRAINING_AVAILABLE = True
except ImportError as e:
    TRAINING_AVAILABLE = False
    print(f"❌ Training dependencies not available: {e}")
    print("Install with: pip install transformers datasets peft accelerate bitsandbytes")


class QwenWildfireTrainer:
    """Fine-tune Qwen2.5 for wildfire strategy generation."""
    
    def __init__(self,
                 base_model: str = "Qwen/Qwen2.5-1.5B-Instruct",
                 output_dir: str = "models/qwen_wildfire_finetuned",
                 use_4bit: bool = True):
        """
        Initialize trainer.
        
        Args:
            base_model: Base model to fine-tune
            output_dir: Where to save the trained model
            use_4bit: Whether to use 4-bit quantization (saves memory)
        """
        if not TRAINING_AVAILABLE:
            raise ImportError("Training dependencies not installed")
        
        self.base_model = base_model
        self.output_dir = output_dir
        self.use_4bit = use_4bit
        
        print(f"🔄 Initializing Qwen wildfire trainer...")
        print(f"   Base model: {base_model}")
        print(f"   Output: {output_dir}")
        print(f"   4-bit quantization: {use_4bit}")
    
    def load_training_data(self, scenarios_path: str = "data/real_training_data/real_scenarios.json") -> List[Dict]:
        """Load and prepare training data from scenarios."""
        
        print(f"\n📂 Loading training data from {scenarios_path}...")
        
        with open(scenarios_path, 'r') as f:
            scenarios = json.load(f)
        
        print(f"✅ Loaded {len(scenarios)} scenarios")
        
        return scenarios
    
    def scenario_to_training_example(self, scenario: Dict) -> Dict[str, str]:
        """
        Convert a wildfire scenario into instruction-tuning format.
        
        Input scenario format:
        {
          "scenario_id": "...",
          "fire_state": [...],
          "terrain": [...],
          "weather": {...},
          "agents": [...],
          ...
        }
        
        Output format:
        {
          "instruction": "system instruction",
          "input": "situation description",
          "output": "strategic guidance"
        }
        """
        
        # Extract key information
        fire_info = scenario.get('fire_info', {})
        weather = scenario.get('weather', {})
        terrain_info = scenario.get('terrain_info', {})
        agents = scenario.get('agents', [])
        
        # Build input description
        input_text = f"""## Wildfire Scenario

**Fire Status:**
- Scenario: {scenario.get('scenario_name', 'Unknown')}
- Active fire area: {fire_info.get('burned_percentage', 0):.1f}%
- Fire intensity: {fire_info.get('avg_intensity', 'medium')}
- Fire center: {fire_info.get('center', 'unknown')}

**Weather:**
- Wind: {weather.get('windSpeed', 5)} m/s from {weather.get('windDir', 0)}°
- Temperature: {weather.get('temp', 25)}°C
- Humidity: {weather.get('humidity', 0.3)*100:.0f}%

**Terrain:**
- Type: {terrain_info.get('type', 'mixed')}
- Elevation range: {terrain_info.get('elevation_range', 'unknown')}

**Available Drones:** {len(agents)}

**Task:** Generate a tactical suppression strategy for this wildfire scenario."""
        
        # Generate target output (strategic guidance)
        # This is where you'd ideally have expert-labeled strategies
        # For now, we'll create structured strategy templates
        output_text = self._generate_strategy_output(scenario, fire_info, weather, agents)
        
        return {
            "instruction": "You are an expert wildfire management AI. Analyze the scenario and provide tactical guidance for drone-based suppression.",
            "input": input_text,
            "output": output_text
        }
    
    def _generate_strategy_output(self, scenario: Dict, fire_info: Dict, weather: Dict, agents: List) -> str:
        """
        Generate strategy output for training.
        
        In a real deployment, these would be expert-labeled strategies.
        For training, we'll create structured strategies based on scenario conditions.
        """
        
        # Determine strategy based on conditions
        wind_speed = weather.get('windSpeed', 5)
        burn_pct = fire_info.get('burned_percentage', 0)
        
        # Strategy selection logic
        if burn_pct > 50 or wind_speed > 15:
            strategy_type = "emergency_containment"
            objective = "Emergency containment of rapidly spreading fire"
            reasoning = f"High burn percentage ({burn_pct:.1f}%) and strong winds ({wind_speed} m/s) require aggressive immediate suppression"
        elif burn_pct > 25:
            strategy_type = "active_suppression"
            objective = "Active suppression with containment focus"
            reasoning = f"Moderate fire spread ({burn_pct:.1f}%) requires coordinated suppression across multiple fronts"
        else:
            strategy_type = "preventive_containment"
            objective = "Preventive containment to limit fire growth"
            reasoning = f"Early stage fire ({burn_pct:.1f}%) - focus on preventing spread before it escalates"
        
        # Generate drone assignments
        num_drones = len(agents)
        assignments = {}
        
        if strategy_type == "emergency_containment":
            # All drones fight fire
            for i in range(num_drones):
                assignments[f"drone_{i}"] = {
                    "role": "firefighter",
                    "priority": "critical",
                    "target_area": f"fire_front_{i}",
                    "coordinates": fire_info.get('fire_front_positions', [[10+i*5, 10+i*5]])[0] if 'fire_front_positions' in fire_info else [10+i*5, 10+i*5]
                }
        elif strategy_type == "active_suppression":
            # Mix of fighters and scouts
            for i in range(num_drones):
                if i < num_drones * 0.7:  # 70% fighters
                    assignments[f"drone_{i}"] = {
                        "role": "firefighter",
                        "priority": "high",
                        "target_area": f"suppression_zone_{i}",
                        "coordinates": [10+i*3, 10+i*3]
                    }
                else:  # 30% scouts
                    assignments[f"drone_{i}"] = {
                        "role": "scout",
                        "priority": "medium",
                        "target_area": "perimeter_monitoring",
                        "coordinates": [20+i*2, 20+i*2]
                    }
        else:
            # Balanced approach
            for i in range(num_drones):
                if i < num_drones * 0.5:
                    assignments[f"drone_{i}"] = {
                        "role": "firefighter",
                        "priority": "high",
                        "target_area": "containment_line",
                        "coordinates": [15+i*2, 15+i*2]
                    }
                elif i < num_drones * 0.8:
                    assignments[f"drone_{i}"] = {
                        "role": "scout",
                        "priority": "medium",
                        "target_area": "threat_assessment",
                        "coordinates": [25+i, 25+i]
                    }
                else:
                    assignments[f"drone_{i}"] = {
                        "role": "recharger",
                        "priority": "low",
                        "target_area": "support_operations",
                        "coordinates": [5+i, 5+i]
                    }
        
        # Build JSON output
        strategy_json = {
            "objective": objective,
            "strategy_type": strategy_type,
            "drone_assignments": assignments,
            "suppression_priorities": [
                "windward_fire_front",
                "high_intensity_zones",
                "containment_perimeter"
            ],
            "reasoning": reasoning
        }
        
        return json.dumps(strategy_json, indent=2)
    
    def prepare_dataset(self, scenarios: List[Dict]) -> Dataset:
        """Convert scenarios to HuggingFace Dataset."""
        
        print("\n🔄 Converting scenarios to training format...")
        
        training_examples = []
        for scenario in scenarios:
            try:
                example = self.scenario_to_training_example(scenario)
                training_examples.append(example)
            except Exception as e:
                print(f"⚠️  Skipping scenario: {e}")
                continue
        
        print(f"✅ Prepared {len(training_examples)} training examples")
        
        # Create HuggingFace Dataset
        dataset = Dataset.from_list(training_examples)
        
        return dataset
    
    def train(self,
              scenarios_path: str = "data/real_training_data/real_scenarios.json",
              epochs: int = 3,
              batch_size: int = 4,
              learning_rate: float = 2e-4):
        """
        Fine-tune the model.
        
        Args:
            scenarios_path: Path to training scenarios
            epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate
        """
        
        print("\n" + "="*60)
        print("🔥 QWEN WILDFIRE FINE-TUNING")
        print("="*60)
        
        # Load data
        scenarios = self.load_training_data(scenarios_path)
        dataset = self.prepare_dataset(scenarios)
        
        # Split train/val
        split_dataset = dataset.train_test_split(test_size=0.1, seed=42)
        train_dataset = split_dataset['train']
        eval_dataset = split_dataset['test']
        
        print(f"\n📊 Dataset split:")
        print(f"   Training: {len(train_dataset)} examples")
        print(f"   Validation: {len(eval_dataset)} examples")
        
        # Load model and tokenizer
        print(f"\n🔄 Loading {self.base_model}...")
        
        tokenizer = AutoTokenizer.from_pretrained(
            self.base_model,
            trust_remote_code=True,
            padding_side="right"
        )
        
        # Ensure pad token exists
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Prepare for LoRA training
        print("\n🔄 Configuring LoRA...")
        
        if self.use_4bit:
            model = prepare_model_for_kbit_training(model)
        
        # LoRA configuration
        lora_config = LoraConfig(
            r=16,  # Rank
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        
        # Tokenize dataset
        def tokenize_function(examples):
            # Format as chat
            texts = []
            for instruction, input_text, output in zip(
                examples["instruction"],
                examples["input"],
                examples["output"]
            ):
                messages = [
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": input_text},
                    {"role": "assistant", "content": output}
                ]
                text = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=False
                )
                texts.append(text)
            
            return tokenizer(
                texts,
                truncation=True,
                max_length=2048,
                padding="max_length"
            )
        
        print("\n🔄 Tokenizing dataset...")
        tokenized_train = train_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=train_dataset.column_names
        )
        tokenized_eval = eval_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=eval_dataset.column_names
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=learning_rate,
            logging_steps=10,
            eval_strategy="steps",
            eval_steps=50,
            save_steps=100,
            save_total_limit=3,
            warmup_steps=50,
            fp16=torch.cuda.is_available(),
            report_to="none",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss"
        )
        
        # Data collator
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=tokenizer,
            model=model,
            padding=True
        )
        
        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_train,
            eval_dataset=tokenized_eval,
            data_collator=data_collator
        )
        
        # Train!
        print("\n" + "="*60)
        print("🚀 STARTING TRAINING")
        print("="*60 + "\n")
        
        trainer.train()
        
        # Save final model
        print(f"\n✅ Training complete! Saving model to {self.output_dir}")
        trainer.save_model(self.output_dir)
        tokenizer.save_pretrained(self.output_dir)
        
        print("\n" + "="*60)
        print("🎉 TRAINING FINISHED!")
        print("="*60)
        print(f"\nYour fine-tuned model is saved at: {self.output_dir}")
        print("\nTo use it in simulations:")
        print("  agent = QwenStrategyAgent(")
        print("      model_path='Qwen/Qwen2.5-1.5B-Instruct',")
        print("      use_fine_tuned=True,")
        print(f"      fine_tuned_path='{self.output_dir}'")
        print("  )")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tune Qwen2.5 for wildfire strategy")
    parser.add_argument("--scenarios", type=str, default="data/real_training_data/real_scenarios.json",
                       help="Path to training scenarios")
    parser.add_argument("--output", type=str, default="models/qwen_wildfire_finetuned",
                       help="Output directory for trained model")
    parser.add_argument("--epochs", type=int, default=3,
                       help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4,
                       help="Training batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-4,
                       help="Learning rate")
    parser.add_argument("--no-4bit", action="store_true",
                       help="Disable 4-bit quantization")
    
    args = parser.parse_args()
    
    # Create trainer
    trainer = QwenWildfireTrainer(
        base_model="Qwen/Qwen2.5-1.5B-Instruct",
        output_dir=args.output,
        use_4bit=not args.no_4bit
    )
    
    # Train
    trainer.train(
        scenarios_path=args.scenarios,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )
