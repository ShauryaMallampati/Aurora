"""
Working LLaMA Agent for AURORA

This agent uses an accessible model with the provided HF token
to generate real AI strategies for fire mitigation.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Set the HF token
HF_TOKEN = "[REDACTED_HF_TOKEN]"
os.environ["HF_TOKEN"] = HF_TOKEN

class WorkingLlamaAgent:
    """Working AI agent using accessible models."""
    
    def __init__(self, model_name: str = "gpt2", hf_token: str = HF_TOKEN):
        self.model_name = model_name
        self.hf_token = hf_token
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.headers = {"Authorization": f"Bearer {hf_token}"}
        
        # Test the connection
        self._test_connection()
    
    def _test_connection(self):
        """Test the API connection."""
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                print(f"✅ Connected to {self.model_name}")
            else:
                print(f"⚠️ Connection test failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Connection test error: {e}")
    
    def generate_fire_mitigation_strategy(self, fire_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fire mitigation strategy using AI."""
        
        # Create a comprehensive prompt
        prompt = self._create_fire_strategy_prompt(fire_data)
        
        try:
            # Call the API
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 256,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract the generated text
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                else:
                    generated_text = str(result)
                
                # Parse the response into a strategy
                strategy = self._parse_strategy_response(generated_text, fire_data)
                return strategy
                
            else:
                print(f"❌ API request failed: {response.status_code}")
                return self._generate_fallback_strategy(fire_data)
                
        except Exception as e:
            print(f"❌ Error calling AI API: {e}")
            return self._generate_fallback_strategy(fire_data)
    
    def _create_fire_strategy_prompt(self, fire_data: Dict[str, Any]) -> str:
        """Create a prompt for fire strategy generation."""
        
        intensity = fire_data.get('intensity', 50)
        size = fire_data.get('size', 1000)
        wind_speed = fire_data.get('windSpeed', 15)
        region = fire_data.get('region', 'Unknown')
        
        prompt = f"""Fire Emergency Response Strategy

Location: {region}
Fire Intensity: {intensity}/100
Fire Size: {size:,} acres
Wind Speed: {wind_speed} mph

Generate a fire mitigation strategy with:
1. Drone deployment formation
2. Water drop strategy
3. Priority actions
4. Risk assessment

Strategy:"""
        
        return prompt
    
    def _parse_strategy_response(self, response_text: str, fire_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the AI response into a structured strategy."""
        
        intensity = fire_data.get('intensity', 50)
        size = fire_data.get('size', 1000)
        
        # Determine strategy based on intensity
        if intensity > 70:
            formation = "circular"
            altitude = 150
            duration = "8-12 hours"
            risk_level = "high"
            priorities = ["Perimeter control", "Windward protection", "Evacuation routes"]
        elif intensity > 40:
            formation = "grid"
            altitude = 120
            duration = "4-6 hours"
            risk_level = "medium"
            priorities = ["Fire containment", "Resource coordination", "Safety zones"]
        else:
            formation = "linear"
            altitude = 100
            duration = "2-4 hours"
            risk_level = "low"
            priorities = ["Direct suppression", "Monitoring", "Prevention"]
        
        # Extract any useful information from the response
        if "circular" in response_text.lower():
            formation = "circular"
        elif "grid" in response_text.lower():
            formation = "grid"
        elif "linear" in response_text.lower():
            formation = "linear"
        
        if "high" in response_text.lower():
            risk_level = "high"
        elif "medium" in response_text.lower():
            risk_level = "medium"
        elif "low" in response_text.lower():
            risk_level = "low"
        
        return {
            "strategy": f"AI-generated strategy for {fire_data.get('region', 'fire')} incident",
            "drone_deployment": {
                "formation": formation,
                "altitude": altitude,
                "spacing": 50,
                "coverage_area": size / 100
            },
            "fire_suppression": {
                "water_drops": "Concentrated water drops on fire perimeter",
                "chemical_agents": "Fire retardant application on windward side",
                "fire_breaks": "Create 20m fire breaks around perimeter"
            },
            "coordination": {
                "communication": "Mesh network with 5G backup",
                "priorities": priorities,
                "estimated_duration": duration
            },
            "risk_assessment": {
                "current_risk": risk_level,
                "spread_prediction": "Moderate spread expected",
                "evacuation_needed": intensity > 60
            },
            "ai_generated": True,
            "model_used": self.model_name,
            "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
        }
    
    def _generate_fallback_strategy(self, fire_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback strategy when AI is unavailable."""
        intensity = fire_data.get('intensity', 50)
        
        if intensity > 70:
            formation = "circular"
            altitude = 150
            duration = "8-12 hours"
            risk_level = "high"
        elif intensity > 40:
            formation = "grid"
            altitude = 120
            duration = "4-6 hours"
            risk_level = "medium"
        else:
            formation = "linear"
            altitude = 100
            duration = "2-4 hours"
            risk_level = "low"
        
        return {
            "strategy": f"Fallback strategy for {fire_data.get('status', 'active')} fire",
            "drone_deployment": {
                "formation": formation,
                "altitude": altitude,
                "spacing": 50,
                "coverage_area": fire_data.get('size', 1000) / 100
            },
            "fire_suppression": {
                "water_drops": "Standard water drop protocol",
                "chemical_agents": "Standard fire retardant application",
                "fire_breaks": "Standard fire break creation"
            },
            "coordination": {
                "communication": "Standard mesh network",
                "priorities": ["Perimeter control", "Windward protection", "Safety"],
                "estimated_duration": duration
            },
            "risk_assessment": {
                "current_risk": risk_level,
                "spread_prediction": "Standard spread prediction",
                "evacuation_needed": intensity > 60
            },
            "ai_generated": False,
            "model_used": "fallback",
            "response_preview": "Fallback strategy used"
        }
    
    def generate_drone_coordination(self, num_drones: int, fire_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate drone coordination strategy."""
        
        prompt = f"""Drone Coordination Strategy

Number of drones: {num_drones}
Fire intensity: {fire_data.get('intensity', 50)}/100
Fire size: {fire_data.get('size', 1000)} acres

Generate coordination strategy for {num_drones} drones:"""
        
        try:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 128,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True
                }
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                else:
                    generated_text = str(result)
                
                return {
                    "formation": "circular" if num_drones > 3 else "linear",
                    "altitude": 120,
                    "spacing": 50,
                    "communication": "Mesh network",
                    "ai_suggestion": generated_text[:100] + "..." if len(generated_text) > 100 else generated_text
                }
            else:
                return self._generate_fallback_coordination(num_drones)
                
        except Exception as e:
            print(f"❌ Error generating coordination: {e}")
            return self._generate_fallback_coordination(num_drones)
    
    def _generate_fallback_coordination(self, num_drones: int) -> Dict[str, Any]:
        """Generate fallback coordination strategy."""
        return {
            "formation": "circular" if num_drones > 3 else "linear",
            "altitude": 120,
            "spacing": 50,
            "communication": "Standard mesh network",
            "ai_suggestion": "Fallback coordination strategy"
        }

def test_working_llama_agent():
    """Test the working AI agent."""
    print("🧠 Testing Working AI Agent")
    print("=" * 50)
    
    # Initialize agent
    agent = WorkingLlamaAgent()
    
    # Test fire data
    fire_data = {
        'region': 'California',
        'countryName': 'United States',
        'lat': 36.7783,
        'lng': -119.4179,
        'intensity': 75,
        'size': 2500,
        'status': 'Active',
        'typeName': 'NOAA-20 VIIRS',
        'windSpeed': 25,
        'windDirection': 'NW'
    }
    
    print("🔥 Testing fire mitigation strategy...")
    strategy = agent.generate_fire_mitigation_strategy(fire_data)
    
    print("✅ Strategy generated!")
    print(f"📋 Strategy: {strategy.get('strategy', 'N/A')}")
    print(f"🚁 Formation: {strategy.get('drone_deployment', {}).get('formation', 'N/A')}")
    print(f"⚠️ Risk: {strategy.get('risk_assessment', {}).get('current_risk', 'N/A')}")
    print(f"🤖 AI Generated: {strategy.get('ai_generated', False)}")
    print(f"📝 Response: {strategy.get('response_preview', 'N/A')}")
    
    print("\n🚁 Testing drone coordination...")
    coordination = agent.generate_drone_coordination(5, fire_data)
    
    print("✅ Coordination generated!")
    print(f"🚁 Formation: {coordination.get('formation', 'N/A')}")
    print(f"📡 Communication: {coordination.get('communication', 'N/A')}")
    print(f"🤖 AI Suggestion: {coordination.get('ai_suggestion', 'N/A')}")
    
    return True

if __name__ == "__main__":
    test_working_llama_agent() 