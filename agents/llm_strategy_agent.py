"""
LLM Strategy Agent for AURORA Phase 3

This module implements an LLM-based strategy layer that can:
- Analyze the current simulation state
- Provide high-level strategic guidance to drone agents
- Generate patrol routes and suppression priorities
- Adapt strategies based on changing conditions

The LLM acts as a "commander" that coordinates multiple drone agents.

REAL LLM INTEGRATION:
To enable real LLM (GPT-4o-mini) instead of mock responses:
1. Get OpenAI API key from https://platform.openai.com/api-keys
2. Set environment variable: export OPENAI_API_KEY="your-key-here"
3. Or pass api_key parameter when initializing LLMStrategyAgent
4. Set use_mock=False when creating the agent

Example:
    llm_agent = LLMStrategyAgent(
        model="gpt-4o-mini",
        api_key="your-openai-api-key",
        use_mock=False
    )
"""

import json
import numpy as np
import os
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai not available. Install with: pip install openai")

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available. Install with: pip install transformers torch")


class LLMStrategyAgent:
    """LLM-based strategic agent for wildfire containment coordination."""
    
    def __init__(self, 
                 model: str = "Qwen/Qwen2.5-1.5B-Instruct",
                 api_key: Optional[str] = None,
                 use_mock: bool = False,
                 use_local_llm: bool = True,
                 hf_token: Optional[str] = None):
        """
        Initialize the LLM strategy agent.
        
        Args:
            model: Model to use (e.g. Qwen/Qwen2.5-1.5B-Instruct, gpt-4o-mini, etc.)
            api_key: OpenAI API key (if None, tries environment variable)
            use_mock: Whether to use mock responses instead of real API calls
            use_local_llm: Whether to use local HuggingFace model (True) or OpenAI API (False)
            hf_token: HuggingFace token for gated models
        """
        self.model = model
        self.use_mock = use_mock
        self.use_local_llm = use_local_llm
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        
        # Initialize local LLaMA model if requested
        self.local_tokenizer = None
        self.local_model = None
        
        if use_local_llm and not use_mock:
            if TRANSFORMERS_AVAILABLE:
                try:
                    print(f"🔄 Loading local LLM: {model}...")
                    self.local_tokenizer = AutoTokenizer.from_pretrained(
                        model,
                        token=self.hf_token,
                        trust_remote_code=True
                    )
                    self.local_model = AutoModelForCausalLM.from_pretrained(
                        model,
                        token=self.hf_token,
                        device_map="auto",
                        torch_dtype=torch.float16,
                        trust_remote_code=True
                    )
                    self.use_mock = False
                    print(f"✅ Local LLM loaded: {model}")
                except Exception as e:
                    print(f"❌ Failed to load local LLM: {e}")
                    print("⚠️  Falling back to mock responses")
                    self.use_mock = True
            else:
                print("⚠️  Transformers not available - using mock responses")
                self.use_mock = True
        elif not use_mock:
            # Try OpenAI API
            if api_key is None:
                api_key = os.getenv("OPENAI_API_KEY")
            
            can_use_openai = OPENAI_AVAILABLE and api_key is not None
            
            if can_use_openai:
                openai.api_key = api_key
                self.use_mock = False
                print(f"✅ OpenAI API enabled: {model}")
            else:
                self.use_mock = True
                if not OPENAI_AVAILABLE:
                    print("⚠️  OpenAI not available - using mock responses")
                elif api_key is None:
                    print("⚠️  No OpenAI API key - using mock responses")
        else:
            print("⚠️  Mock mode enabled")
        
        # Strategy history
        self.strategy_history = []
        self.current_strategy = None
        
        # Mock responses for demonstration
        self.mock_strategies = [
            {
                "strategy": "containment_priority",
                "description": "Focus on containing fire spread to prevent further expansion",
                "drone_assignments": {
                    "drone_0": {"role": "firefighter", "priority": "high", "target_area": "northeast"},
                    "drone_1": {"role": "scout", "priority": "medium", "target_area": "southwest"},
                    "drone_2": {"role": "firefighter", "priority": "high", "target_area": "northwest"}
                },
                "patrol_routes": {
                    "drone_0": [(10, 15), (12, 16), (14, 17)],
                    "drone_1": [(5, 5), (8, 8), (10, 10)],
                    "drone_2": [(15, 10), (17, 12), (19, 14)]
                },
                "suppression_priorities": ["northeast", "northwest", "southwest"],
                "communication_plan": "All drones report fire status every 3 steps"
            },
            {
                "strategy": "resource_optimization",
                "description": "Optimize resource usage while maintaining effective suppression",
                "drone_assignments": {
                    "drone_0": {"role": "firefighter", "priority": "high", "target_area": "center"},
                    "drone_1": {"role": "recharger", "priority": "low", "target_area": "water_zones"},
                    "drone_2": {"role": "firefighter", "priority": "medium", "target_area": "east"}
                },
                "patrol_routes": {
                    "drone_0": [(12, 12), (13, 13), (14, 14)],
                    "drone_1": [(3, 3), (5, 5), (7, 7)],
                    "drone_2": [(15, 8), (16, 9), (17, 10)]
                },
                "suppression_priorities": ["center", "east", "water_zones"],
                "communication_plan": "Coordinate recharging to maintain continuous suppression"
            },
            {
                "strategy": "emergency_response",
                "description": "Emergency response mode - all drones focus on immediate fire threats",
                "drone_assignments": {
                    "drone_0": {"role": "firefighter", "priority": "critical", "target_area": "all"},
                    "drone_1": {"role": "firefighter", "priority": "critical", "target_area": "all"},
                    "drone_2": {"role": "firefighter", "priority": "critical", "target_area": "all"}
                },
                "patrol_routes": {
                    "drone_0": [(10, 10), (11, 11), (12, 12)],
                    "drone_1": [(8, 8), (9, 9), (10, 10)],
                    "drone_2": [(12, 12), (13, 13), (14, 14)]
                },
                "suppression_priorities": ["all_areas"],
                "communication_plan": "Emergency mode - all drones suppress fire immediately"
            }
        ]
        
        self.strategy_index = 0
    
    def analyze_situation(self, 
                         fire_state: np.ndarray,
                         terrain: np.ndarray,
                         agent_positions: List[Tuple[int, int]],
                         agent_statuses: List[Dict],
                         weather: Dict,
                         step: int) -> Dict[str, Any]:
        """
        Analyze the current simulation situation.
        
        Args:
            fire_state: Current fire state array
            terrain: Terrain elevation array
            agent_positions: List of drone positions
            agent_statuses: List of drone status dictionaries
            weather: Current weather conditions
            step: Current simulation step
            
        Returns:
            Dictionary with situation analysis
        """
        # Calculate fire metrics
        fire_coverage = np.sum(fire_state > 0) / fire_state.size * 100
        fire_intensity = np.sum(fire_state == 1)  # Active fires
        
        # Calculate agent metrics
        active_agents = sum(1 for status in agent_statuses if status.get("is_active", True))
        avg_battery = np.mean([status.get("battery_percentage", 100) for status in agent_statuses])
        avg_water = np.mean([status.get("water_percentage", 100) for status in agent_statuses])
        
        # Analyze fire spread direction
        fire_direction = self._calculate_fire_spread_direction(fire_state)
        
        # Assess terrain complexity
        terrain_complexity = self._calculate_terrain_complexity(terrain)
        
        # Assess threat level
        threat_level = self._assess_threat_level(fire_coverage, fire_intensity, weather)
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "fire_metrics": {
                "coverage_percentage": fire_coverage,
                "intensity": fire_intensity,
                "spread_direction": fire_direction,
                "active_cells": int(fire_intensity)
            },
            "agent_metrics": {
                "total_agents": len(agent_positions),
                "active_agents": active_agents,
                "average_battery": avg_battery,
                "average_water": avg_water,
                "positions": agent_positions,
                "statuses": agent_statuses
            },
            "environmental_metrics": {
                "terrain_complexity": terrain_complexity,
                "weather_conditions": weather,
                "elevation_range": (float(np.min(terrain)), float(np.max(terrain)))
            },
            "threat_assessment": {
                "level": threat_level,
                "description": self._get_threat_description(threat_level),
                "urgency": "high" if threat_level in ["critical", "high"] else "medium"
            }
        }
        
        return analysis
    
    def generate_strategy(self, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate strategic guidance based on situation analysis.
        
        Args:
            situation_analysis: Output from analyze_situation()
            
        Returns:
            Dictionary with strategic guidance
        """
        if self.use_mock:
            return self._generate_mock_strategy(situation_analysis)
        
        # Real LLM call
        prompt = self._create_strategy_prompt(situation_analysis)
        
        # Use local LLaMA model if available
        if self.use_local_llm and self.local_model is not None:
            try:
                print(f"🤖 Calling local LLM ({self.model}) for strategy generation...")
                
                # Format prompt for LLaMA-2 chat format
                formatted_prompt = f"[INST] <<SYS>>\nYou are a wildfire response commander coordinating drone agents. Provide strategic guidance in JSON format.\n<</SYS>>\n\n{prompt} [/INST]"
                
                inputs = self.local_tokenizer(formatted_prompt, return_tensors="pt").to(self.local_model.device)
                
                with torch.no_grad():
                    outputs = self.local_model.generate(
                        **inputs,
                        max_new_tokens=512,
                        temperature=0.7,
                        do_sample=True,
                        top_p=0.9
                    )
                
                strategy_text = self.local_tokenizer.decode(outputs[0], skip_special_tokens=True)
                # Extract only the response part (after [/INST])
                if "[/INST]" in strategy_text:
                    strategy_text = strategy_text.split("[/INST]")[1].strip()
                
                print(f"🤖 LLM Response: {strategy_text[:200]}...")
                
                # Try to parse JSON response
                try:
                    strategy = json.loads(strategy_text)
                except json.JSONDecodeError:
                    print("⚠️  LLM response not valid JSON, using mock strategy")
                    return self._generate_mock_strategy(situation_analysis)
                
                # Add metadata
                strategy["llm_model"] = self.model
                strategy["generation_timestamp"] = datetime.now().isoformat()
                strategy["situation_analysis"] = situation_analysis
                
                return strategy
                
            except Exception as e:
                print(f"❌ Local LLM error: {e}")
                print("🔄 Falling back to mock strategy...")
                return self._generate_mock_strategy(situation_analysis)
        
        # Otherwise try OpenAI API
        try:
            print(f"🤖 Calling OpenAI API ({self.model}) for strategy generation...")
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a wildfire response commander coordinating drone agents. Provide strategic guidance in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            strategy_text = response.choices[0].message.content
            print(f"🤖 LLM Response: {strategy_text[:200]}...")
            
            # Try to parse JSON response
            try:
                strategy = json.loads(strategy_text)
            except json.JSONDecodeError:
                print("⚠️  LLM response not valid JSON, using mock strategy")
                return self._generate_mock_strategy(situation_analysis)
            
            # Add metadata
            strategy["llm_model"] = self.model
            strategy["generation_timestamp"] = datetime.now().isoformat()
            strategy["situation_analysis"] = situation_analysis
            
            return strategy
            
        except Exception as e:
            print(f"❌ LLM API error: {e}")
            print("🔄 Falling back to mock strategy...")
            return self._generate_mock_strategy(situation_analysis)
    
    def _generate_mock_strategy(self, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock strategy based on situation analysis."""
        threat_level = situation_analysis["threat_assessment"]["level"]
        fire_coverage = situation_analysis["fire_metrics"]["coverage_percentage"]
        
        # Choose strategy based on conditions
        if threat_level == "critical" or fire_coverage > 50:
            strategy = self.mock_strategies[2]  # Emergency response
        elif fire_coverage > 25:
            strategy = self.mock_strategies[0]  # Containment priority
        else:
            strategy = self.mock_strategies[1]  # Resource optimization
        
        # Adapt strategy based on current conditions
        adapted_strategy = strategy.copy()
        adapted_strategy["situation_analysis"] = situation_analysis
        adapted_strategy["adaptation_reasoning"] = f"Selected {strategy['strategy']} based on {threat_level} threat level and {fire_coverage:.1f}% fire coverage"
        adapted_strategy["llm_model"] = "mock"
        adapted_strategy["generation_timestamp"] = datetime.now().isoformat()
        
        return adapted_strategy
    
    def get_agent_guidance(self, 
                          agent_id: str,
                          strategy: Dict[str, Any],
                          current_position: Tuple[int, int],
                          agent_status: Dict) -> Dict[str, Any]:
        """
        Get specific guidance for an individual agent.
        
        Args:
            agent_id: Agent identifier
            strategy: Current strategy
            current_position: Agent's current position
            agent_status: Agent's current status
            
        Returns:
            Dictionary with agent-specific guidance
        """
        if agent_id not in strategy.get("drone_assignments", {}):
            return {"action": "continue", "reason": "No specific guidance available"}
        
        assignment = strategy["drone_assignments"][agent_id]
        patrol_route = strategy.get("patrol_routes", {}).get(agent_id, [])
        
        # Check if agent needs to recharge
        battery_low = agent_status.get("battery_percentage", 100) < 30
        water_low = agent_status.get("water_percentage", 100) < 20
        
        if battery_low or water_low:
            guidance = {
                "action": "recharge",
                "reason": f"Low resources - battery: {agent_status.get('battery_percentage', 100)}%, water: {agent_status.get('water_percentage', 100)}%",
                "priority": "high",
                "target_area": "recharge_zone"
            }
        else:
            guidance = {
                "action": assignment.get("role", "firefighter"),
                "reason": f"Assigned role: {assignment.get('role', 'firefighter')}",
                "priority": assignment.get("priority", "medium"),
                "target_area": assignment.get("target_area", "general"),
                "patrol_route": patrol_route
            }
        
        return guidance
    
    def _calculate_fire_spread_direction(self, fire_state: np.ndarray) -> Tuple[float, float]:
        """Calculate the dominant direction of fire spread."""
        fire_locations = np.where(fire_state == 1)
        if len(fire_locations[0]) < 2:
            return (0.0, 0.0)
        
        # Calculate centroid and spread direction
        centroid = (np.mean(fire_locations[0]), np.mean(fire_locations[1]))
        
        # Simple direction calculation
        max_dist = 0
        direction = (0.0, 0.0)
        
        for i, j in zip(fire_locations[0], fire_locations[1]):
            dist = np.sqrt((i - centroid[0])**2 + (j - centroid[1])**2)
            if dist > max_dist:
                max_dist = dist
                direction = ((i - centroid[0]) / dist, (j - centroid[1]) / dist)
        
        return direction
    
    def _calculate_terrain_complexity(self, terrain: np.ndarray) -> float:
        """Calculate terrain complexity score."""
        # Simple complexity based on variety of terrain types
        unique_terrain = len(np.unique(terrain))
        return unique_terrain / 4.0  # Normalize to 0-1
    
    def _assess_threat_level(self, 
                           fire_coverage: float, 
                           fire_intensity: int, 
                           weather: Dict) -> str:
        """Assess the overall threat level."""
        if fire_coverage > 0.5 or fire_intensity > 50:
            return "critical"
        elif fire_coverage > 0.25 or fire_intensity > 20:
            return "high"
        elif fire_coverage > 0.1 or fire_intensity > 5:
            return "medium"
        else:
            return "low"
    
    def _get_threat_description(self, threat_level: str) -> str:
        """Get description for threat level."""
        descriptions = {
            "critical": "Immediate response required - fire spreading rapidly",
            "high": "Significant fire activity - coordinated response needed",
            "medium": "Moderate fire activity - standard response procedures",
            "low": "Minimal fire activity - monitoring and prevention focus"
        }
        return descriptions.get(threat_level, "Unknown threat level")
    
    def _create_strategy_prompt(self, situation_analysis: Dict[str, Any]) -> str:
        """Create prompt for LLM strategy generation."""
        return f"""
        Analyze this wildfire situation and provide strategic guidance:
        
        Fire Coverage: {situation_analysis['fire_metrics']['coverage_percentage']:.1f}%
        Fire Intensity: {situation_analysis['fire_metrics']['intensity']} cells
        Active Agents: {situation_analysis['agent_metrics']['active_agents']}
        Average Battery: {situation_analysis['agent_metrics']['average_battery']:.1f}%
        Average Water: {situation_analysis['agent_metrics']['average_water']:.1f}%
        Threat Level: {situation_analysis['threat_assessment']['level']}
        
        Provide a JSON response with:
        - strategy: containment_priority, resource_optimization, or emergency_response
        - description: brief strategy explanation
        - drone_assignments: role and priority for each drone
        - patrol_routes: suggested routes for each drone
        - suppression_priorities: areas to focus on
        - communication_plan: coordination instructions
        """
    
    def update_strategy_history(self, strategy: Dict[str, Any]):
        """Update strategy history."""
        self.strategy_history.append({
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy
        })
        self.current_strategy = strategy
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get summary of strategy history."""
        if not self.strategy_history:
            return {"message": "No strategy history available"}
        
        strategies_used = [s["strategy"]["strategy"] for s in self.strategy_history]
        strategy_counts = {}
        for strategy in strategies_used:
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            "total_strategies": len(self.strategy_history),
            "strategy_distribution": strategy_counts,
            "current_strategy": self.current_strategy["strategy"] if self.current_strategy else None,
            "last_update": self.strategy_history[-1]["timestamp"] if self.strategy_history else None
        }


def main():
    """Demo the LLM strategy agent."""
    agent = LLMStrategyAgent(use_mock=True)
    
    # Create mock situation
    fire_state = np.zeros((20, 20))
    fire_state[10:15, 10:15] = 1  # Some fire
    terrain = np.random.choice([0, 1, 2, 3], size=(20, 20))
    agent_positions = [(5, 5), (15, 15), (10, 10)]
    agent_statuses = [
        {"is_active": True, "battery_percentage": 80, "water_percentage": 60},
        {"is_active": True, "battery_percentage": 90, "water_percentage": 40},
        {"is_active": True, "battery_percentage": 70, "water_percentage": 80}
    ]
    weather = {"wind_direction": [0.5, 0.5], "wind_intensity": 1.5, "humidity": 0.3, "temperature": 30.0}
    
    # Analyze situation
    analysis = agent.analyze_situation(fire_state, terrain, agent_positions, agent_statuses, weather, 10)
    print("Situation Analysis:")
    # Convert numpy types to Python types for JSON serialization
    analysis_json = json.loads(json.dumps(analysis, default=lambda x: int(x) if isinstance(x, np.integer) else float(x) if isinstance(x, np.floating) else x))
    print(json.dumps(analysis_json, indent=2))
    
    # Generate strategy
    strategy = agent.generate_strategy(analysis)
    print("\nGenerated Strategy:")
    # Convert numpy types to Python types for JSON serialization
    strategy_json = json.loads(json.dumps(strategy, default=lambda x: int(x) if isinstance(x, np.integer) else float(x) if isinstance(x, np.floating) else x))
    print(json.dumps(strategy_json, indent=2))
    
    # Get agent guidance
    guidance = agent.get_agent_guidance("drone_0", strategy, (5, 5), agent_statuses[0])
    print("\nAgent Guidance:")
    print(json.dumps(guidance, indent=2))


if __name__ == "__main__":
    main() 