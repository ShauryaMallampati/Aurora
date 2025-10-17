"""
AURORA Hybrid Model Inference & Demo Script

This script loads the trained hybrid PPO+LLM model and runs it on test fire scenarios,
generating visualization data for the web interface.

Author: Shaurya Mallampati
Date: October 13, 2025
ISEF 2025 Competition
"""

import sys
import os
from pathlib import Path
import numpy as np
import json
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

# Add project paths
BASE_DIR = Path(__file__).parent.resolve()
sys.path.append(str(BASE_DIR / 'data'))
sys.path.append(str(BASE_DIR / 'agents'))

from stable_baselines3 import PPO
from env.fire_sim import FireSim
from agents.drone_agent import DroneAgent
from data.real_data_integration_complete import RealDataIntegrator
from agents.hybrid_ppo_llm_agent import HybridPPOLLMAgent


class HybridModelDemo:
    """Demo runner for trained hybrid PPO+LLM model."""
    
    def __init__(self, model_path: str, llm_model: str = "meta-llama/Llama-3.2-1B-Instruct",
                 llm_backend: str = "transformers", hf_token: str = None):
        """Initialize demo with trained model.
        
        Args:
            model_path: Path to trained PPO model directory
            llm_model: LLM model ID for strategic guidance
                    llm_backend: Backend to use (transformers)
            hf_token: HuggingFace token (if using transformers)
        """
        print(f"Loading trained model from {model_path}...")
        self.model = PPO.load(model_path)
        print("✅ Model loaded")
        
        # Initialize hybrid agent for strategic guidance
        self.hybrid_agent = HybridPPOLLMAgent(
            llm_model=llm_model,
            llm_guidance_frequency=50,  # Request guidance every 50 steps
            hf_token=hf_token,
            llm_backend=llm_backend
        )
        
        # Initialize real data integrator
        self.integrator = RealDataIntegrator()
        
        self.grid_size = 50
        self.num_drones = 3
        
    def run_scenario(self, scenario_name: str = None, max_steps: int = 200) -> Dict:
        """Run trained model on a fire scenario and return telemetry.
        
        Args:
            scenario_name: Specific fire name, or None for random
            max_steps: Maximum simulation steps
            
        Returns:
            Dictionary with simulation telemetry and visualization data
        """
        print(f"\n{'='*80}")
        print(f"RUNNING SCENARIO: {scenario_name or 'Random Fire'}")
        print(f"{'='*80}\n")
        
        # Load scenario
        scenario = self.integrator.create_training_scenario(
            min_year=2015,
            min_acres=500,
            max_acres=10000
        )
        
        fire_name = scenario.get('fire_name', 'Unknown')
        fire_year = scenario.get('year', 'Unknown')
        fire_acres = scenario.get('size_acres', scenario.get('acres', 0))
        print(f"📍 Fire: {fire_name} ({fire_year})")
        print(f"📊 Size: {fire_acres:.1f} acres")
        
        # Initialize simulation
        fire_sim = FireSim(grid_size=self.grid_size)
        fire_sim.fire_state = scenario['initial_fire_grid'].astype(np.uint8)
        
        # Set weather
        weather = scenario['weather']
        wind_dirs = {'N': (0, -1), 'NE': (1, -1), 'E': (1, 0), 'SE': (1, 1),
                    'S': (0, 1), 'SW': (-1, 1), 'W': (-1, 0), 'NW': (-1, -1)}
        wind_dir = wind_dirs.get(weather['wind_direction'], (0, 0))
        wind_speed = weather['wind_speed_mph'] / 25.0
        fire_sim.set_wind(wind_dir, wind_speed)
        fire_sim.set_weather(
            humidity=weather['humidity'] / 100.0,
            temperature=weather['temperature_c']
        )
        
        # Set terrain
        terrain = scenario['terrain']
        fire_sim.elevation = (terrain['elevation'] / 3000.0).astype(np.float32)
        fire_sim.fuel_density = (0.7 + terrain['slope'] * 0.3).astype(np.float32)
        
        # Initialize drones
        drones = []
        for i in range(self.num_drones):
            x = np.random.randint(0, self.grid_size)
            y = np.random.randint(0, self.grid_size)
            drone = DroneAgent(start_pos=(x, y), agent_id=f"drone_{i}")
            drones.append(drone)
        
        # Telemetry storage
        telemetry = {
            'scenario': {
                'fire_name': fire_name,
                'fire_year': fire_year,
                'size_acres': float(fire_acres),
                'location': scenario.get('location', {}),
                'weather': weather
            },
            'steps': [],
            'summary': {}
        }
        
        # Run simulation
        current_strategy = None
        total_reward = 0
        
        for step in range(max_steps):
            # Get strategic guidance from LLM
            if self.hybrid_agent.should_request_guidance(step):
                drone_positions = [tuple(d.position) for d in drones]
                drone_states = [d.get_status() for d in drones]
                
                current_strategy = self.hybrid_agent.get_strategic_guidance(
                    fire_state=fire_sim.fire_state,
                    drone_positions=drone_positions,
                    drone_states=drone_states,
                    weather=weather,
                    step=step
                )
                
                print(f"\n🧠 Step {step}: LLM Strategic Guidance")
                print(f"   Priority zones: {current_strategy.get('priority_zones', [])}")
                print(f"   Rationale: {current_strategy.get('rationale', 'N/A')}")
            
            # Get observation and action for each drone
            step_data = {
                'step': step,
                'fire_state': fire_sim.fire_state.tolist(),
                'drones': [],
                'strategy': current_strategy,
                'metrics': {}
            }
            
            for i, drone in enumerate(drones):
                # Build observation
                obs = self._get_observation(fire_sim, drone, i, drones, current_strategy)
                
                # Get action from trained model
                action, _states = self.model.predict(obs, deterministic=True)
                
                # Execute action
                result = drone.act(action, fire_sim, drones)
                
                step_data['drones'].append({
                    'id': drone.agent_id,
                    'position': list(drone.position) if hasattr(drone.position, '__iter__') else [drone.position],
                    'battery': float(drone.battery),
                    'water': float(drone.water),
                    'action': int(action),
                    'is_active': bool(drone.is_active)
                })
            
            # Step fire simulation
            fire_sim.step()
            
            # Calculate metrics
            burning_cells = np.sum(fire_sim.fire_state == 1)
            burnt_cells = np.sum(fire_sim.fire_state == 2)
            containment = 1.0 - (burning_cells / (self.grid_size * self.grid_size))
            
            step_data['metrics'] = {
                'burning_cells': int(burning_cells),
                'burnt_cells': int(burnt_cells),
                'containment': float(containment),
                'active_drones': sum(1 for d in drones if d.is_active)
            }
            
            telemetry['steps'].append(step_data)
            
            # Progress logging
            if step % 20 == 0:
                print(f"Step {step}/{max_steps}: {burning_cells} burning, "
                      f"{containment*100:.1f}% containment")
            
            # Early stop if fire is contained
            if burning_cells == 0:
                print(f"\n🎯 Fire contained at step {step}!")
                break
        
        # Calculate summary statistics
        llm_stats = self.hybrid_agent.get_statistics()
        telemetry['summary'] = {
            'total_steps': len(telemetry['steps']),
            'fire_contained': int(burning_cells == 0),
            'final_containment': float(containment),
            'final_burning_cells': int(burning_cells),
            'total_suppression_actions': int(sum(d.suppression_count for d in drones)),
            'llm_calls': int(llm_stats['llm_calls']),
            'llm_tokens': int(llm_stats['llm_tokens_used']),
            'llm_errors': int(llm_stats['llm_errors'])
        }
        
        print(f"\n{'='*80}")
        print("SIMULATION COMPLETE")
        print(f"{'='*80}")
        print(f"Final containment: {containment*100:.1f}%")
        print(f"Total steps: {len(telemetry['steps'])}")
        print(f"LLM guidance calls: {llm_stats['llm_calls']}")
        print(f"{'='*80}\n")
        
        return telemetry
    
    def _get_observation(self, fire_sim: FireSim, drone: DroneAgent, 
                        drone_id: int, all_drones: List[DroneAgent],
                        strategy: Dict) -> np.ndarray:
        """Build observation for drone with strategic overlay."""
        x, y = drone.position
        obs = np.zeros((3, 3, 9), dtype=np.float32)
        
        for i in range(-1, 2):
            for j in range(-1, 2):
                nx, ny = x + i, y + j
                nx = max(0, min(self.grid_size - 1, nx))
                ny = max(0, min(self.grid_size - 1, ny))
                
                # Original channels
                obs[i+1, j+1, 0] = 1.0 if fire_sim.fire_state[ny, nx] == 1 else 0.0
                obs[i+1, j+1, 1] = fire_sim.terrain[ny, nx] / 3.0
                obs[i+1, j+1, 2] = fire_sim.elevation[ny, nx] / 100.0
                obs[i+1, j+1, 3] = fire_sim.fuel_density[ny, nx]
                obs[i+1, j+1, 4] = drone.battery
                obs[i+1, j+1, 5] = drone.water
                
                # Strategic channels from LLM
                if strategy:
                    priority_zones = strategy.get('priority_zones', [])
                    if priority_zones:
                        distances = [abs(ny - z[0]) + abs(nx - z[1]) for z in priority_zones]
                        min_dist = min(distances)
                        obs[i+1, j+1, 6] = max(0, 1.0 - min_dist / self.grid_size)
                    
                    assignments = strategy.get('drone_assignments', {})
                    drone_key = f"drone_{drone_id}"
                    if drone_key in assignments and priority_zones:
                        zone_idx = assignments[drone_key]
                        if zone_idx < len(priority_zones):
                            target = priority_zones[zone_idx]
                            dx = (target[1] - x) / self.grid_size
                            dy = (target[0] - y) / self.grid_size
                            obs[i+1, j+1, 7] = dx
                            obs[i+1, j+1, 8] = dy
        
        return obs
    
    def save_telemetry(self, telemetry: Dict, output_path: str):
        """Save telemetry to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(telemetry, f, indent=2)
        print(f"💾 Telemetry saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Run trained hybrid model on test scenarios')
    parser.add_argument('--model_path', type=str, 
                       default='results/aurora_hybrid_ppo_llm_model/policy.pth',
                       help='Path to trained model')
    parser.add_argument('--llm_backend', type=str, default='transformers',
                       help='LLM backend (transformers)')
    parser.add_argument('--max_steps', type=int, default=200,
                       help='Maximum simulation steps')
    parser.add_argument('--output', type=str, default='results/demo_telemetry.json',
                       help='Output path for telemetry JSON')
    
    args = parser.parse_args()
    
    # Initialize demo
    demo = HybridModelDemo(
        model_path=args.model_path,
        llm_backend=args.llm_backend,
        hf_token=os.getenv("HF_TOKEN")
    )
    
    # Run scenario
    telemetry = demo.run_scenario(max_steps=args.max_steps)
    
    # Save telemetry
    demo.save_telemetry(telemetry, args.output)
    
    print("\n✅ Demo complete! Use the telemetry JSON to generate web visualization.")
    print(f"   Run: python generate_web_demo.py --telemetry {args.output}")


if __name__ == "__main__":
    main()
