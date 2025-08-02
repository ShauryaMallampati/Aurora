"""
Advanced AI Strategy Agent for AURORA Phase 3

This module implements a sophisticated AI-based strategy layer that can:
- Analyze the current simulation state using multiple AI models
- Provide high-level strategic guidance to drone agents
- Generate patrol routes and suppression priorities
- Adapt strategies based on changing conditions
- Use world models for predictive planning

The AI acts as a "commander" that coordinates multiple drone agents.
"""

import json
import numpy as np
import os
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available. Install with: pip install transformers torch accelerate")


class AdvancedAIStrategyAgent:
    """Advanced AI-based strategic agent for wildfire containment coordination."""
    
    def __init__(self, 
                 model_name: str = "meta-llama/Llama-2-7b-chat-hf",
                 hf_token: Optional[str] = None,
                 use_mock: bool = False,
                 device: str = "auto",
                 enable_world_model: bool = True):
        """
        Initialize the advanced AI strategy agent.
        
        Args:
            model_name: Hugging Face model name
            hf_token: Hugging Face token for gated models
            use_mock: Whether to use mock responses instead of real model
            device: Device to run model on ('auto', 'cpu', 'cuda')
            enable_world_model: Whether to enable world model predictions
        """
        self.model_name = model_name
        self.use_mock = use_mock
        self.device = device
        self.enable_world_model = enable_world_model
        
        # Try to get HF token from environment if not provided
        if hf_token is None:
            hf_token = os.getenv("HF_TOKEN")
        
        # Determine if we can use real AI
        can_use_real_ai = (
            TRANSFORMERS_AVAILABLE and 
            hf_token is not None and 
            not use_mock
        )
        
        if can_use_real_ai:
            print(f"🚀 Loading Advanced AI model: {model_name}")
            try:
                # Set HF token for authentication
                os.environ["HF_TOKEN"] = hf_token
                
                # Load tokenizer and model
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name, 
                    token=hf_token,
                    trust_remote_code=True
                )
                
                # Load model with optimizations
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    token=hf_token,
                    torch_dtype=torch.float16,
                    device_map="auto" if device == "auto" else device,
                    trust_remote_code=True
                )
                
                # Initialize world model components
                if self.enable_world_model:
                    self._initialize_world_model()
                
                self.use_mock = False
                print(f"✅ Advanced AI model loaded successfully!")
                print(f"🌍 World Model: {'Enabled' if self.enable_world_model else 'Disabled'}")
                
            except Exception as e:
                print(f"❌ Error loading AI model: {e}")
                print("🔄 Falling back to mock responses...")
                self.use_mock = True
        else:
            self.use_mock = True
            if not TRANSFORMERS_AVAILABLE:
                print("⚠️  Transformers not available - using mock responses")
            elif hf_token is None:
                print("⚠️  No HF token - using mock responses")
            else:
                print("⚠️  Mock mode enabled - set use_mock=False for real AI")
        
        # Strategy history and world model state
        self.strategy_history = []
        self.current_strategy = None
        self.world_model_state = {}
        self.prediction_history = []
        
        # Advanced mock responses
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
                "communication_plan": "All drones report fire status every 3 steps",
                "world_model_prediction": "Fire expected to spread northeast in next 5 steps"
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
                "communication_plan": "Coordinate recharging to maintain continuous suppression",
                "world_model_prediction": "Optimal resource allocation for 15-step sustainability"
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
                "communication_plan": "Emergency mode - all drones suppress fire immediately",
                "world_model_prediction": "CRITICAL: Fire will double in size within 3 steps without intervention"
            },
            {
                "strategy": "predictive_containment",
                "description": "Use world model predictions to prevent fire spread before it happens",
                "drone_assignments": {
                    "drone_0": {"role": "predictor", "priority": "high", "target_area": "predicted_spread"},
                    "drone_1": {"role": "firefighter", "priority": "high", "target_area": "current_hotspots"},
                    "drone_2": {"role": "coordinator", "priority": "medium", "target_area": "command_center"}
                },
                "patrol_routes": {
                    "drone_0": [(15, 15), (16, 16), (17, 17)],
                    "drone_1": [(10, 10), (11, 11), (12, 12)],
                    "drone_2": [(5, 5), (6, 6), (7, 7)]
                },
                "suppression_priorities": ["predicted_spread", "current_hotspots"],
                "communication_plan": "Predictive mode - coordinate based on world model forecasts",
                "world_model_prediction": "Fire will spread to coordinates (15,15) in 2 steps - deploy prevention"
            }
        ]

    def _initialize_world_model(self):
        """Initialize world model components for predictive planning."""
        try:
            # Simple world model using statistical prediction
            self.world_model_state = {
                "fire_spread_model": "statistical",
                "weather_influence": True,
                "terrain_effects": True,
                "prediction_horizon": 10,
                "confidence_threshold": 0.7
            }
            print("🌍 World model initialized for predictive planning")
        except Exception as e:
            print(f"⚠️  World model initialization failed: {e}")
            self.enable_world_model = False

    def predict_fire_spread(self, fire_state: np.ndarray, terrain: np.ndarray, weather: Dict, steps_ahead: int = 5) -> Dict[str, Any]:
        """
        Predict fire spread using world model.
        
        Args:
            fire_state: Current fire state
            terrain: Terrain elevation
            weather: Weather conditions
            steps_ahead: Number of steps to predict
            
        Returns:
            Prediction results
        """
        if not self.enable_world_model:
            return {"prediction": "World model disabled", "confidence": 0.0}
        
        try:
            # Simple statistical prediction based on current fire state
            fire_locations = np.where(fire_state == 1)
            if len(fire_locations[0]) == 0:
                return {"prediction": "No active fire", "confidence": 1.0}
            
            # Calculate fire center and spread
            fire_center = (np.mean(fire_locations[0]), np.mean(fire_locations[1]))
            fire_spread = (np.std(fire_locations[0]), np.std(fire_locations[1]))
            
            # Predict spread direction based on wind
            wind_direction = weather.get("wind_direction", "N")
            wind_speed = weather.get("wind_speed", 0)
            
            # Simple wind-based prediction
            spread_prediction = self._calculate_wind_spread(fire_center, wind_direction, wind_speed, steps_ahead)
            
            # Calculate confidence based on weather conditions
            confidence = min(0.9, 0.5 + (wind_speed / 20.0))
            
            prediction = {
                "prediction": f"Fire will spread {wind_direction} to {spread_prediction}",
                "confidence": confidence,
                "predicted_coordinates": spread_prediction,
                "steps_ahead": steps_ahead,
                "fire_center": fire_center,
                "spread_rate": fire_spread
            }
            
            # Store prediction in history
            self.prediction_history.append({
                "timestamp": datetime.now().isoformat(),
                "prediction": prediction
            })
            
            return prediction
            
        except Exception as e:
            print(f"❌ World model prediction error: {e}")
            return {"prediction": "Prediction failed", "confidence": 0.0}

    def _calculate_wind_spread(self, fire_center: Tuple[float, float], wind_direction: str, wind_speed: float, steps: int) -> Tuple[int, int]:
        """Calculate predicted fire spread based on wind conditions."""
        x, y = fire_center
        
        # Wind direction mapping
        wind_offsets = {
            "N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0),
            "NE": (1, -1), "NW": (-1, -1), "SE": (1, 1), "SW": (-1, 1)
        }
        
        offset = wind_offsets.get(wind_direction, (0, 0))
        spread_factor = min(wind_speed / 10.0, 2.0)  # Cap spread factor
        
        predicted_x = int(x + offset[0] * steps * spread_factor)
        predicted_y = int(y + offset[1] * steps * spread_factor)
        
        return (predicted_x, predicted_y)

    def analyze_situation(self, 
                         fire_state: np.ndarray,
                         terrain: np.ndarray,
                         agent_positions: List[Tuple[int, int]],
                         agent_statuses: List[Dict],
                         weather: Dict,
                         step: int) -> Dict[str, Any]:
        """
        Analyze the current simulation situation with world model predictions.
        
        Args:
            fire_state: Current fire state array
            terrain: Terrain elevation array
            agent_positions: List of drone positions
            agent_statuses: List of drone status dictionaries
            weather: Current weather conditions
            step: Current simulation step
            
        Returns:
            Dictionary with situation analysis including predictions
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
        
        # World model predictions
        fire_prediction = self.predict_fire_spread(fire_state, terrain, weather, steps_ahead=5)
        
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
            },
            "world_model_predictions": {
                "fire_spread": fire_prediction,
                "model_enabled": self.enable_world_model,
                "prediction_confidence": fire_prediction.get("confidence", 0.0)
            }
        }
        
        return analysis

    def generate_strategy(self, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate strategic guidance based on situation analysis and world model predictions.
        
        Args:
            situation_analysis: Output from analyze_situation()
            
        Returns:
            Dictionary with strategic guidance
        """
        if self.use_mock:
            return self._generate_mock_strategy(situation_analysis)
        
        # Real AI call with world model integration
        prompt = self._create_advanced_strategy_prompt(situation_analysis)
        
        try:
            print(f"🤖 Calling Advanced AI for strategy generation...")
            
            # Prepare input for AI model with explicit JSON formatting instructions
            input_text = f"""Advanced Wildfire Response Commander: {prompt}

Please respond with ONLY a valid JSON object in this exact format:
{{
    "strategy": "strategy_name",
    "description": "detailed description",
    "priority": "high/medium/low",
    "drone_assignments": {{
        "drone_0": "role",
        "drone_1": "role",
        "drone_2": "role"
    }},
    "tactical_plan": "specific tactical instructions"
}}

Strategy:"""
            
            inputs = self.tokenizer.encode(input_text, return_tensors="pt").to(self.model.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=400,  # Reduced for more focused response
                    temperature=0.5,     # Lower temperature for more consistent JSON
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2  # Prevent repetition
                )
            
            # Decode response
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the generated part (after the input)
            generated_text = response_text[len(input_text):].strip()
            print(f"🤖 AI Response: {generated_text[:200]}...")
            
            # Try multiple approaches to parse JSON
            strategy = self._parse_ai_response(generated_text, situation_analysis)
            
            # Add metadata and world model integration
            strategy["ai_model"] = "advanced-ai"
            strategy["generation_timestamp"] = datetime.now().isoformat()
            strategy["situation_analysis"] = situation_analysis
            strategy["world_model_integration"] = self.enable_world_model
            
            return strategy
            
        except Exception as e:
            print(f"❌ AI model error: {e}")
            print("🔄 Falling back to mock strategy...")
            return self._generate_mock_strategy(situation_analysis)

    def _parse_ai_response(self, response_text: str, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response with multiple fallback strategies."""
        
        # Method 1: Try to extract JSON directly
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                strategy = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["strategy", "description"]
                if all(field in strategy for field in required_fields):
                    print("✅ Successfully parsed AI JSON response")
                    return strategy
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️  JSON parsing failed: {e}")
        
        # Method 2: Try to extract structured text and convert to JSON
        try:
            strategy = self._extract_structured_response(response_text)
            if strategy:
                print("✅ Successfully extracted structured response")
                return strategy
        except Exception as e:
            print(f"⚠️  Structured extraction failed: {e}")
        
        # Method 3: Use mock strategy as fallback
        print("🔄 Using mock strategy as fallback...")
        return self._generate_mock_strategy(situation_analysis)

    def _extract_structured_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract structured information from AI response text."""
        try:
            # Look for common patterns in the response
            lines = response_text.split('\n')
            strategy_info = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for strategy type
                if any(keyword in line.lower() for keyword in ['strategy', 'approach', 'plan']):
                    if 'emergency' in line.lower():
                        strategy_info['strategy'] = 'emergency_response'
                    elif 'containment' in line.lower():
                        strategy_info['strategy'] = 'containment_priority'
                    elif 'resource' in line.lower():
                        strategy_info['strategy'] = 'resource_optimization'
                    elif 'predictive' in line.lower():
                        strategy_info['strategy'] = 'predictive_containment'
                
                # Look for description
                if 'description' not in strategy_info and len(line) > 20:
                    strategy_info['description'] = line
            
            # If we found some structure, create a strategy
            if 'strategy' in strategy_info:
                return {
                    "strategy": strategy_info.get('strategy', 'resource_optimization'),
                    "description": strategy_info.get('description', 'AI-generated strategy based on current conditions'),
                    "priority": "medium",
                    "drone_assignments": {
                        "drone_0": "firefighter",
                        "drone_1": "firefighter", 
                        "drone_2": "firefighter"
                    },
                    "tactical_plan": "Execute AI-recommended strategy with coordinated drone deployment"
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️  Structured extraction error: {e}")
            return None

    def _generate_mock_strategy(self, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock strategy based on situation analysis and world model predictions."""
        threat_level = situation_analysis["threat_assessment"]["level"]
        fire_coverage = situation_analysis["fire_metrics"]["coverage_percentage"]
        
        # Check world model predictions
        world_predictions = situation_analysis.get("world_model_predictions", {})
        prediction_confidence = world_predictions.get("prediction_confidence", 0.0)
        
        # Choose strategy based on conditions and predictions
        if threat_level == "critical" or fire_coverage > 50:
            strategy = self.mock_strategies[2]  # Emergency response
        elif prediction_confidence > 0.7 and fire_coverage > 10:
            strategy = self.mock_strategies[3]  # Predictive containment
        elif fire_coverage > 25:
            strategy = self.mock_strategies[0]  # Containment priority
        else:
            strategy = self.mock_strategies[1]  # Resource optimization
        
        # Adapt strategy based on current conditions
        adapted_strategy = strategy.copy()
        adapted_strategy["situation_analysis"] = situation_analysis
        adapted_strategy["adaptation_reasoning"] = f"Selected {strategy['strategy']} based on {threat_level} threat level, {fire_coverage:.1f}% fire coverage, and {prediction_confidence:.2f} prediction confidence"
        adapted_strategy["ai_model"] = "advanced-ai-mock"
        adapted_strategy["generation_timestamp"] = datetime.now().isoformat()
        adapted_strategy["world_model_integration"] = self.enable_world_model
        
        return adapted_strategy

    def get_agent_guidance(self, 
                          agent_id: str,
                          strategy: Dict[str, Any],
                          current_position: Tuple[int, int],
                          agent_status: Dict) -> Dict[str, Any]:
        """
        Get specific guidance for an individual agent with world model integration.
        
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
        
        # Get world model prediction for this agent
        world_prediction = strategy.get("world_model_prediction", "No prediction available")
        
        if battery_low or water_low:
            guidance = {
                "action": "recharge",
                "reason": f"Low resources - battery: {agent_status.get('battery_percentage', 100)}%, water: {agent_status.get('water_percentage', 100)}%",
                "priority": "high",
                "target_area": "recharge_zone",
                "world_model_insight": world_prediction
            }
        else:
            guidance = {
                "action": assignment.get("role", "firefighter"),
                "reason": f"Assigned role: {assignment.get('role', 'firefighter')}",
                "priority": assignment.get("priority", "medium"),
                "target_area": assignment.get("target_area", "general"),
                "patrol_route": patrol_route,
                "world_model_insight": world_prediction
            }
        
        return guidance

    def _calculate_fire_spread_direction(self, fire_state: np.ndarray) -> Tuple[float, float]:
        """Calculate the primary direction of fire spread."""
        fire_locations = np.where(fire_state == 1)
        if len(fire_locations[0]) == 0:
            return (0.0, 0.0)
        
        # Calculate fire center
        fire_center = (np.mean(fire_locations[0]), np.mean(fire_locations[1]))
        
        # Calculate spread direction based on fire distribution
        spread_x = np.std(fire_locations[1])  # Spread in x direction
        spread_y = np.std(fire_locations[0])  # Spread in y direction
        
        # Normalize
        total_spread = np.sqrt(spread_x**2 + spread_y**2)
        if total_spread == 0:
            return (0.0, 0.0)
        
        return (spread_x / total_spread, spread_y / total_spread)

    def _calculate_terrain_complexity(self, terrain: np.ndarray) -> float:
        """Calculate terrain complexity based on elevation variation."""
        return float(np.std(terrain))

    def _assess_threat_level(self, 
                           fire_coverage: float, 
                           fire_intensity: int, 
                           weather: Dict) -> str:
        """Assess the threat level based on fire and weather conditions."""
        if fire_coverage > 50 or fire_intensity > 100:
            return "critical"
        elif fire_coverage > 25 or fire_intensity > 50:
            return "high"
        elif fire_coverage > 10 or fire_intensity > 20:
            return "medium"
        else:
            return "low"

    def _get_threat_description(self, threat_level: str) -> str:
        """Get description for threat level."""
        descriptions = {
            "critical": "Critical threat - immediate response required",
            "high": "High threat - aggressive suppression needed",
            "medium": "Medium threat - standard response protocol",
            "low": "Low threat - monitoring and prevention"
        }
        return descriptions.get(threat_level, "Unknown threat level")

    def _create_advanced_strategy_prompt(self, situation_analysis: Dict[str, Any]) -> str:
        """Create an advanced prompt for AI strategy generation with world model integration."""
        
        # Extract key information
        fire_metrics = situation_analysis["fire_metrics"]
        agent_metrics = situation_analysis["agent_metrics"]
        threat_assessment = situation_analysis["threat_assessment"]
        world_predictions = situation_analysis.get("world_model_predictions", {})
        
        # Create structured prompt
        prompt = f"""
You are an advanced AI wildfire response commander. Analyze the current situation and provide strategic guidance.

CURRENT SITUATION:
- Fire Coverage: {fire_metrics['coverage_percentage']:.1f}%
- Active Fires: {fire_metrics['active_cells']} cells
- Fire Intensity: Level {fire_metrics['intensity']}
- Threat Level: {threat_assessment['level']} - {threat_assessment['description']}
- Active Drones: {agent_metrics['active_agents']}/{agent_metrics['total_agents']}
- Average Battery: {agent_metrics['average_battery']:.1f}%
- Average Water: {agent_metrics['average_water']:.1f}%

WORLD MODEL PREDICTIONS:
- Fire Spread Direction: {fire_metrics['spread_direction']}
- Prediction: {world_predictions.get('prediction', 'No prediction available')}
- Confidence: {world_predictions.get('confidence', 0.0):.2f}

AVAILABLE STRATEGIES:
1. "resource_optimization" - Balance suppression with resource management
2. "containment_priority" - Focus on preventing fire spread
3. "emergency_response" - All-out firefighting mode
4. "predictive_containment" - Use predictions to prevent spread

DRONE ROLES:
- "firefighter" - Direct fire suppression
- "scout" - Monitor and report
- "coordinator" - Manage other drones
- "recharger" - Focus on resource management

Based on this analysis, provide a strategic response in JSON format.
"""
        
        return prompt

    def update_strategy_history(self, strategy: Dict[str, Any]):
        """Update strategy history."""
        self.strategy_history.append({
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy
        })
        self.current_strategy = strategy

    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get summary of strategy history with world model insights."""
        if not self.strategy_history:
            return {"total_strategies": 0}
        
        strategies = [s["strategy"]["strategy"] for s in self.strategy_history]
        strategy_counts = {}
        for strategy in strategies:
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        # World model usage statistics
        world_model_usage = sum(1 for s in self.strategy_history 
                              if s["strategy"].get("world_model_integration", False))
        
        return {
            "total_strategies": len(self.strategy_history),
            "strategy_distribution": strategy_counts,
            "current_strategy": self.current_strategy["strategy"] if self.current_strategy else None,
            "last_update": self.strategy_history[-1]["timestamp"] if self.strategy_history else None,
            "world_model_usage": world_model_usage,
            "world_model_enabled": self.enable_world_model,
            "prediction_history_length": len(self.prediction_history)
        }


def main():
    """Test the advanced AI strategy agent."""
    print("🤖 Testing Advanced AI Strategy Agent")
    print("=" * 50)
    
    # Create sample data
    fire_state = np.zeros((20, 20))
    fire_state[8:12, 8:12] = 1
    
    terrain = np.random.rand(20, 20) * 100
    agent_positions = [(5, 5), (15, 5), (10, 15)]
    agent_statuses = [
        {"is_active": True, "battery_percentage": 80, "water_percentage": 60},
        {"is_active": True, "battery_percentage": 30, "water_percentage": 90},
        {"is_active": True, "battery_percentage": 95, "water_percentage": 20}
    ]
    weather = {"temperature": 85, "humidity": 30, "wind_speed": 15, "wind_direction": "NW"}
    
    # Test with HF token
    hf_token = os.getenv("HF_TOKEN", "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")
    
    # Create advanced agent
    ai_agent = AdvancedAIStrategyAgent(
        model_name="microsoft/DialoGPT-medium",
        hf_token=hf_token,
        use_mock=False,
        enable_world_model=True
    )
    
    # Analyze situation
    situation = ai_agent.analyze_situation(
        fire_state, terrain, agent_positions, agent_statuses, weather, 0
    )
    
    print(f"Threat level: {situation['threat_assessment']['level']}")
    print(f"Fire coverage: {situation['fire_metrics']['coverage_percentage']:.1f}%")
    print(f"World model prediction: {situation['world_model_predictions']['fire_spread']['prediction']}")
    
    # Generate strategy
    strategy = ai_agent.generate_strategy(situation)
    
    print(f"Strategy: {strategy['strategy']}")
    print(f"Description: {strategy['description']}")
    print(f"AI Model: {strategy.get('ai_model', 'unknown')}")
    print(f"World Model Integration: {strategy.get('world_model_integration', False)}")
    
    print("\n✅ Advanced AI Strategy Agent Test Complete!")


if __name__ == "__main__":
    main() 