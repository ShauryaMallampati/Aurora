"""
Qwen2.5-1.5B-Instruct Strategy Agent for AURORA

This agent uses Qwen2.5-1.5B-Instruct (fine-tuned on wildfire data) to generate
strategic guidance for drone-based wildfire suppression.

Key Features:
- Analyzes fire state, terrain, weather, and drone status
- Generates tactical suppression strategies
- Coordinates multi-drone operations
- Adapts to changing conditions

Model: Qwen/Qwen2.5-1.5B-Instruct (fine-tuned)
"""

import json
import numpy as np
import os
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("❌ Error: transformers not available. Install with: pip install transformers torch")


class QwenStrategyAgent:
    """Qwen2.5-based strategic agent for wildfire containment coordination."""
    
    def __init__(self, 
                 model_path: str = "Qwen/Qwen2.5-1.5B-Instruct",
                 use_fine_tuned: bool = False,
                 fine_tuned_path: Optional[str] = None,
                 device: str = "auto"):
        """
        Initialize the Qwen strategy agent.
        
        Args:
            model_path: HuggingFace model path or local path to base model
            use_fine_tuned: Whether to load your fine-tuned wildfire model
            fine_tuned_path: Path to fine-tuned adapter weights (LoRA)
            device: Device to run on ('auto', 'cuda', 'cpu')
        """
        self.model_path = model_path
        self.use_fine_tuned = use_fine_tuned
        self.fine_tuned_path = fine_tuned_path or "models/qwen_wildfire_finetuned"
        
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers is required. Install: pip install transformers torch")
        
        print(f"🔄 Loading Qwen2.5-1.5B-Instruct...")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=device,
            trust_remote_code=True
        )
        
        # Load fine-tuned adapter if specified
        if use_fine_tuned and os.path.exists(self.fine_tuned_path):
            print(f"🔄 Loading fine-tuned wildfire adapter from {self.fine_tuned_path}...")
            try:
                from peft import PeftModel
                self.model = PeftModel.from_pretrained(self.model, self.fine_tuned_path)
                print("✅ Fine-tuned adapter loaded successfully!")
            except ImportError:
                print("⚠️  peft not installed. Install: pip install peft")
                print("⚠️  Using base model without fine-tuning")
            except Exception as e:
                print(f"⚠️  Failed to load fine-tuned adapter: {e}")
                print("⚠️  Using base model")
        
        self.model.eval()
        
        print(f"✅ Qwen2.5-1.5B-Instruct loaded successfully!")
        
        # Strategy history
        self.strategy_history = []
        self.current_strategy = None
    
    def _build_prompt(self,
                     fire_state: np.ndarray,
                     terrain: np.ndarray,
                     agent_positions: List[Tuple[int, int]],
                     agent_statuses: List[Dict],
                     weather: Dict,
                     step: int) -> str:
        """Build the prompt for Qwen model."""
        
        # Analyze fire state
        fire_cells = np.sum(fire_state > 0)
        total_cells = fire_state.size
        burn_percentage = (fire_cells / total_cells) * 100
        
        # Get fire front positions
        fire_positions = np.argwhere(fire_state > 0.5)
        if len(fire_positions) > 0:
            fire_center = fire_positions.mean(axis=0)
        else:
            fire_center = np.array([terrain.shape[0]//2, terrain.shape[1]//2])
        
        # Agent summary
        agent_summary = []
        for i, (pos, status) in enumerate(zip(agent_positions, agent_statuses)):
            agent_summary.append(
                f"Drone {i}: Position ({pos[0]}, {pos[1]}), "
                f"Battery: {status.get('battery', 1.0)*100:.0f}%, "
                f"Water: {status.get('water', 1.0)*100:.0f}%, "
                f"Action: {status.get('action', 'idle')}"
            )
        
        # Weather summary
        wind_speed = weather.get('windSpeed', weather.get('wind_mps', 5))
        wind_dir = weather.get('windDir', weather.get('wind_deg', 0))
        temp = weather.get('temp', weather.get('temperature_c', 25))
        humidity = weather.get('humidity', 0.3)
        
        prompt = f"""You are an expert wildfire management AI coordinating drone suppression operations. Analyze the current situation and provide strategic guidance.

## Current Situation (Step {step})

**Fire Status:**
- Burned area: {burn_percentage:.1f}% of terrain
- Active fire cells: {fire_cells}
- Fire center: ({fire_center[0]:.0f}, {fire_center[1]:.0f})
- Terrain size: {terrain.shape[0]}x{terrain.shape[1]}

**Weather Conditions:**
- Wind: {wind_speed:.1f} m/s from {wind_dir}°
- Temperature: {temp:.1f}°C
- Humidity: {humidity*100:.0f}%

**Drone Fleet Status:**
{chr(10).join(agent_summary)}

## Required Strategy

Provide a tactical strategy including:
1. **Primary Objective**: What should be the main focus right now?
2. **Drone Assignments**: Specific role and target area for each drone
3. **Suppression Priorities**: Which areas to prioritize (in order)
4. **Tactical Reasoning**: Why this strategy is optimal given conditions

Respond in JSON format:
```json
{{
  "objective": "string describing main goal",
  "drone_assignments": {{
    "drone_0": {{"role": "firefighter/scout/recharger", "priority": "high/medium/low", "target_area": "description", "coordinates": [x, y]}},
    ...
  }},
  "suppression_priorities": ["area1", "area2", "area3"],
  "reasoning": "explanation of strategy"
}}
```

Strategy:"""
        
        return prompt
    
    def generate_strategy(self,
                         fire_state: np.ndarray,
                         terrain: np.ndarray,
                         agent_positions: List[Tuple[int, int]],
                         agent_statuses: List[Dict],
                         weather: Dict,
                         step: int) -> Dict[str, Any]:
        """
        Generate strategic guidance using Qwen model.
        
        Args:
            fire_state: Current fire state array
            terrain: Terrain elevation array
            agent_positions: List of drone positions
            agent_statuses: List of drone status dictionaries
            weather: Current weather conditions
            step: Current simulation step
            
        Returns:
            Dictionary containing strategic guidance
        """
        
        # Build prompt
        prompt = self._build_prompt(
            fire_state, terrain, agent_positions, 
            agent_statuses, weather, step
        )
        
        # Prepare messages for chat template
        messages = [
            {"role": "system", "content": "You are Qwen, an expert wildfire management AI. You provide tactical guidance for drone-based wildfire suppression."},
            {"role": "user", "content": prompt}
        ]
        
        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        # Generate
        with torch.no_grad():
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        
        # Decode
        generated_ids = [
            output_ids[len(input_ids):] 
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Parse JSON response
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                strategy = json.loads(json_str)
            else:
                # Fallback if no JSON found
                strategy = self._create_fallback_strategy(agent_positions)
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse JSON response. Using fallback strategy.")
            strategy = self._create_fallback_strategy(agent_positions)
        
        # Store strategy
        self.current_strategy = strategy
        self.strategy_history.append({
            'step': step,
            'strategy': strategy,
            'timestamp': datetime.now().isoformat()
        })
        
        return strategy
    
    def _create_fallback_strategy(self, agent_positions: List[Tuple[int, int]]) -> Dict[str, Any]:
        """Create a simple fallback strategy if LLM response fails."""
        return {
            "objective": "Emergency containment - focus on immediate fire suppression",
            "drone_assignments": {
                f"drone_{i}": {
                    "role": "firefighter",
                    "priority": "high",
                    "target_area": f"zone_{i}",
                    "coordinates": list(pos)
                }
                for i, pos in enumerate(agent_positions)
            },
            "suppression_priorities": [f"zone_{i}" for i in range(len(agent_positions))],
            "reasoning": "Fallback strategy - distribute drones evenly for immediate suppression"
        }
    
    def get_drone_guidance(self, drone_id: int) -> Dict[str, Any]:
        """Get specific guidance for a drone based on current strategy."""
        if not self.current_strategy:
            return {"action": "idle", "priority": "low"}
        
        drone_key = f"drone_{drone_id}"
        assignments = self.current_strategy.get("drone_assignments", {})
        
        if drone_key in assignments:
            return assignments[drone_key]
        
        return {"action": "idle", "priority": "low"}
    
    def save_history(self, filepath: str = "results/qwen_strategy_history.json"):
        """Save strategy history to file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.strategy_history, f, indent=2)
        print(f"✅ Strategy history saved to {filepath}")


if __name__ == "__main__":
    # Test the agent
    print("Testing QwenStrategyAgent...")
    
    agent = QwenStrategyAgent(
        model_path="Qwen/Qwen2.5-1.5B-Instruct",
        use_fine_tuned=False
    )
    
    # Create dummy data
    fire_state = np.random.rand(50, 50)
    terrain = np.random.rand(50, 50) * 100
    agent_positions = [(10, 10), (20, 20), (30, 30)]
    agent_statuses = [
        {"battery": 0.8, "water": 0.6, "action": "idle"},
        {"battery": 0.9, "water": 0.8, "action": "scout"},
        {"battery": 0.5, "water": 0.3, "action": "recharge"}
    ]
    weather = {
        "windSpeed": 12.5,
        "windDir": 45,
        "temp": 28.0,
        "humidity": 0.25
    }
    
    # Generate strategy
    strategy = agent.generate_strategy(
        fire_state, terrain, agent_positions,
        agent_statuses, weather, step=10
    )
    
    print("\n📋 Generated Strategy:")
    print(json.dumps(strategy, indent=2))
