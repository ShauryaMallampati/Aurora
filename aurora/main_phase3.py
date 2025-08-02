"""
AURORA Phase 3 Enhanced Simulation

This module implements the complete Phase 3 system with:
- Real data integration (weather, terrain, historical fires)
- LLM strategy layer for high-level coordination
- Enhanced sensor simulation and fault tolerance
- Comprehensive trajectory tracking and analysis
- Mission failure simulation

This represents the cutting-edge of AI-powered wildfire simulation.
"""

import numpy as np
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import our modules
try:
    from env.fire_sim import FireSim
    from agents.drone_agent import DroneAgent
    from agents.llm_strategy_agent import LLMStrategyAgent
    from data.real_data_integration import RealDataIntegrator
    from utils.visualizer import render
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('.')
    from env.fire_sim import FireSim
    from agents.drone_agent import DroneAgent
    from agents.llm_strategy_agent import LLMStrategyAgent
    from data.real_data_integration import RealDataIntegrator
    from utils.visualizer import render


class Phase3SimulationLogger:
    """Enhanced logger for Phase 3 simulation with real data and LLM strategy."""
    
    def __init__(self, output_dir: str = "results/phase3_logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.output_dir / f"phase3_simulation_{self.timestamp}.json"
        
        self.data = {
            "simulation_config": {},
            "real_data_sources": {},
            "llm_strategy_history": [],
            "step_data": [],
            "trajectories": {
                "fire_trajectory": [],
                "agent_trajectories": [],
                "strategy_changes": []
            },
            "performance_metrics": {},
            "mission_failures": []
        }
    
    def log_config(self, config: Dict[str, Any]):
        """Log simulation configuration."""
        self.data["simulation_config"] = config
    
    def log_real_data_sources(self, sources: Dict[str, Any]):
        """Log real data sources used."""
        self.data["real_data_sources"] = sources
    
    def log_step(self, step_data: Dict[str, Any]):
        """Log step data."""
        self.data["step_data"].append(step_data)
    
    def log_strategy(self, strategy: Dict[str, Any]):
        """Log LLM strategy."""
        self.data["llm_strategy_history"].append(strategy)
    
    def log_trajectory(self, trajectory_type: str, data: Any):
        """Log trajectory data."""
        if trajectory_type in self.data["trajectories"]:
            self.data["trajectories"][trajectory_type].append(data)
    
    def log_mission_failure(self, failure_data: Dict[str, Any]):
        """Log mission failure events."""
        self.data["mission_failures"].append(failure_data)
    
    def save(self):
        """Save all logged data to file."""
        with open(self.log_file, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)
        print(f"Phase 3 simulation logs saved to: {self.log_file}")


class Phase3Simulation:
    """Phase 3 enhanced simulation with real data and LLM strategy."""
    
    def __init__(self, 
                 scenario_name: str = "california_2023",
                 num_drones: int = 3,
                 use_real_data: bool = True,
                 use_llm_strategy: bool = True,
                 enable_failures: bool = True):
        """
        Initialize Phase 3 simulation.
        
        Args:
            scenario_name: Name of the scenario to load
            num_drones: Number of drone agents
            use_real_data: Whether to use real data sources
            use_llm_strategy: Whether to use LLM strategy layer
            enable_failures: Whether to simulate mission failures
        """
        self.scenario_name = scenario_name
        self.num_drones = num_drones
        self.use_real_data = use_real_data
        self.use_llm_strategy = use_llm_strategy
        self.enable_failures = enable_failures
        
        # Initialize components
        self.logger = Phase3SimulationLogger()
        self.real_data_integrator = RealDataIntegrator() if use_real_data else None
        self.llm_strategy_agent = LLMStrategyAgent(use_mock=True) if use_llm_strategy else None
        
        # Load scenario
        self.scenario = self._load_scenario()
        
        # Initialize simulation components
        self.fire_sim = None
        self.drones = []
        self.current_strategy = None
        
        # Performance tracking
        self.performance_metrics = {
            "fire_coverage_history": [],
            "suppression_actions": [],
            "strategy_effectiveness": [],
            "resource_utilization": [],
            "communication_events": []
        }
        
        self._initialize_simulation()
    
    def _load_scenario(self) -> Dict[str, Any]:
        """Load or create simulation scenario."""
        if self.use_real_data:
            return self.real_data_integrator.create_realistic_simulation_scenario(
                self.scenario_name, map_size=50
            )
        else:
            # Fallback to basic scenario
            return {
                "name": self.scenario_name,
                "map_size": 50,
                "simulation_config": {
                    "wind_direction": [0.5, 0.5],
                    "wind_intensity": 1.5,
                    "humidity": 0.3,
                    "temperature": 30.0
                }
            }
    
    def _initialize_simulation(self):
        """Initialize simulation components."""
        print(f"Initializing Phase 3 simulation: {self.scenario_name}")
        
        # Initialize fire simulation
        config = self.scenario["simulation_config"]
        self.fire_sim = FireSim(
            wind_direction=tuple(config["wind_direction"]),
            wind_intensity=config["wind_intensity"],
            humidity=config["humidity"],
            temperature=config["temperature"]
        )
        
        # Initialize drone agents
        self.drones = []
        for i in range(self.num_drones):
            # Calculate starting positions around the map
            start_x = (i * 5) % self.fire_sim.grid_size[0]
            start_y = (i * 3) % self.fire_sim.grid_size[1]
            start_pos = (start_x, start_y)
            
            drone = DroneAgent(
                agent_id=f"phase3_drone_{i}",
                start_pos=start_pos,
                max_battery=100,
                max_water=50,
                sensor_range=8,
                communication_range=8
            )
            self.drones.append(drone)
        
        # Log configuration
        self.logger.log_config({
            "scenario_name": self.scenario_name,
            "num_drones": self.num_drones,
            "use_real_data": self.use_real_data,
            "use_llm_strategy": self.use_llm_strategy,
            "enable_failures": self.enable_failures,
            "simulation_config": config
        })
        
        if self.use_real_data:
            self.logger.log_real_data_sources({
                "wildfire_data": len(self.scenario["wildfire_data"]),
                "weather_data": len(self.scenario["weather_data"]),
                "terrain_data": self.scenario["terrain_data"]["elevation"].shape
            })
    
    def _simulate_mission_failures(self, step: int):
        """Simulate mission failures (drone crashes, communication loss, etc.)."""
        if not self.enable_failures:
            return
        
        failure_chance = 0.001  # 0.1% chance per step per drone
        
        for i, drone in enumerate(self.drones):
            if np.random.random() < failure_chance:
                failure_type = np.random.choice([
                    "communication_loss", "sensor_malfunction", "partial_crash"
                ])
                
                failure_data = {
                    "step": step,
                    "drone_id": drone.agent_id,
                    "failure_type": failure_type,
                    "timestamp": datetime.now().isoformat()
                }
                
                if failure_type == "communication_loss":
                    drone.communication_range = 0
                    failure_data["description"] = "Drone lost communication capability"
                elif failure_type == "sensor_malfunction":
                    drone.sensor_range = 2
                    failure_data["description"] = "Drone sensor range reduced"
                elif failure_type == "partial_crash":
                    drone.is_active = False
                    failure_data["description"] = "Drone crashed and is inactive"
                
                self.logger.log_mission_failure(failure_data)
                print(f"⚠️  Mission failure: {failure_data['description']}")
    
    def _get_llm_strategy(self, step: int):
        """Get LLM strategy for current situation."""
        if not self.use_llm_strategy or not self.llm_strategy_agent:
            return None
        
        # Analyze current situation
        agent_positions = [drone.position for drone in self.drones]
        agent_statuses = [drone.get_status() for drone in self.drones]
        weather = self.fire_sim.get_weather_info()
        
        situation_analysis = self.llm_strategy_agent.analyze_situation(
            self.fire_sim.fire_state,
            self.fire_sim.terrain,
            agent_positions,
            agent_statuses,
            weather,
            step
        )
        
        # Generate strategy
        strategy = self.llm_strategy_agent.generate_strategy(situation_analysis)
        self.llm_strategy_agent.update_strategy_history(strategy)
        
        # Log strategy
        self.logger.log_strategy({
            "step": step,
            "situation_analysis": situation_analysis,
            "strategy": strategy
        })
        
        return strategy
    
    def _execute_agent_actions(self, step: int, strategy: Optional[Dict] = None):
        """Execute actions for all agents."""
        actions_taken = []
        
        for i, drone in enumerate(self.drones):
            if not drone.is_active:
                continue
            
            # Get LLM guidance if available
            guidance = None
            if strategy and self.llm_strategy_agent:
                guidance = self.llm_strategy_agent.get_agent_guidance(
                    f"drone_{i}", strategy, drone.position, drone.get_status()
                )
            
            # Determine action (heuristic with LLM guidance)
            if guidance and guidance.get("action") == "recharge":
                action = self._find_recharge_action(drone)
            elif guidance and guidance.get("action") == "firefighter":
                action = self._find_firefighting_action(drone)
            else:
                action = self._heuristic_action(drone)
            
            # Execute action
            action_result = drone.act(action, self.fire_sim, self.drones)
            
            # Apply fire suppression
            if action == 5 and action_result.get('suppressed', False):
                self.fire_sim.fire_state[drone.position] = 0
            
            actions_taken.append({
                "drone_id": drone.agent_id,
                "action": action,
                "result": action_result,
                "guidance": guidance
            })
        
        return actions_taken
    
    def _find_recharge_action(self, drone: DroneAgent) -> int:
        """Find action to move toward recharge zone."""
        # Find nearest water or road
        min_dist = float('inf')
        best_action = 0  # stay
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                new_x = drone.position[0] + dx
                new_y = drone.position[1] + dy
                
                if (0 <= new_x < self.fire_sim.grid_size[0] and 
                    0 <= new_y < self.fire_sim.grid_size[1]):
                    
                    terrain_type = self.fire_sim.terrain[new_x, new_y]
                    if terrain_type in [2, 3]:  # road or water
                        dist = abs(dx) + abs(dy)
                        if dist < min_dist:
                            min_dist = dist
                            best_action = self._direction_to_action(dx, dy)
        
        return best_action
    
    def _find_firefighting_action(self, drone: DroneAgent) -> int:
        """Find action to fight fire."""
        # Find nearest burning cell
        min_dist = float('inf')
        best_action = 0  # stay
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                new_x = drone.position[0] + dx
                new_y = drone.position[1] + dy
                
                if (0 <= new_x < self.fire_sim.grid_size[0] and 
                    0 <= new_y < self.fire_sim.grid_size[1]):
                    
                    if self.fire_sim.fire_state[new_x, new_y] == 1:  # burning
                        dist = abs(dx) + abs(dy)
                        if dist < min_dist:
                            min_dist = dist
                            if dist == 1:  # adjacent to fire
                                best_action = 5  # suppress
                            else:
                                best_action = self._direction_to_action(dx, dy)
        
        return best_action
    
    def _heuristic_action(self, drone: DroneAgent) -> int:
        """Basic heuristic action selection."""
        # Check if we can suppress nearby fire
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                new_x = drone.position[0] + dx
                new_y = drone.position[1] + dy
                
                if (0 <= new_x < self.fire_sim.grid_size[0] and 
                    0 <= new_y < self.fire_sim.grid_size[1]):
                    
                    if self.fire_sim.fire_state[new_x, new_y] == 1:  # burning
                        return 5  # suppress
        
        # Move toward fire if we can see it
        fire_direction = self._find_fire_direction(drone)
        if fire_direction:
            return self._direction_to_action(*fire_direction)
        
        # Random movement
        return np.random.randint(1, 5)
    
    def _direction_to_action(self, dx: int, dy: int) -> int:
        """Convert direction to action number."""
        if dx == -1 and dy == 0: return 1  # up
        if dx == 1 and dy == 0: return 2   # down
        if dx == 0 and dy == -1: return 3  # left
        if dx == 0 and dy == 1: return 4   # right
        return 0  # stay
    
    def _find_fire_direction(self, drone: DroneAgent) -> Optional[Tuple[int, int]]:
        """Find direction toward fire."""
        # Simple fire-seeking behavior
        fire_locations = np.where(self.fire_sim.fire_state == 1)
        if len(fire_locations[0]) == 0:
            return None
        
        # Find nearest fire
        min_dist = float('inf')
        nearest_fire = None
        
        for i, j in zip(fire_locations[0], fire_locations[1]):
            dist = abs(i - drone.position[0]) + abs(j - drone.position[1])
            if dist < min_dist:
                min_dist = dist
                nearest_fire = (i, j)
        
        if nearest_fire:
            dx = 1 if nearest_fire[0] > drone.position[0] else -1 if nearest_fire[0] < drone.position[0] else 0
            dy = 1 if nearest_fire[1] > drone.position[1] else -1 if nearest_fire[1] < drone.position[1] else 0
            return (dx, dy)
        
        return None
    
    def run(self, max_steps: int = 100, render_interval: int = 5):
        """Run the Phase 3 simulation."""
        print(f"\n🚀 Starting Phase 3 AURORA Simulation")
        print(f"Scenario: {self.scenario_name}")
        print(f"Drones: {self.num_drones}")
        print(f"Real Data: {'✅' if self.use_real_data else '❌'}")
        print(f"LLM Strategy: {'✅' if self.use_llm_strategy else '❌'}")
        print(f"Mission Failures: {'✅' if self.enable_failures else '❌'}")
        print("=" * 60)
        
        start_time = time.time()
        
        for step in range(max_steps):
            # Simulate mission failures
            self._simulate_mission_failures(step)
            
            # Get LLM strategy
            strategy = self._get_llm_strategy(step)
            
            # Execute agent actions
            actions_taken = self._execute_agent_actions(step, strategy)
            
            # Update fire simulation
            self.fire_sim.step()
            
            # Track performance
            fire_coverage = self.fire_sim.get_fire_coverage()
            self.performance_metrics["fire_coverage_history"].append(fire_coverage)
            
            # Log step data
            step_data = {
                "step": step,
                "fire_coverage": fire_coverage,
                "fire_intensity": self.fire_sim.get_fire_intensity(),
                "agent_positions": [drone.position for drone in self.drones],
                "agent_statuses": [drone.get_status() for drone in self.drones],
                "actions_taken": actions_taken,
                "strategy": strategy,
                "weather": self.fire_sim.get_weather_info()
            }
            self.logger.log_step(step_data)
            
            # Log trajectories
            self.logger.log_trajectory("fire_trajectory", {
                "step": step,
                "fire_state": self.fire_sim.fire_state.tolist()
            })
            
            self.logger.log_trajectory("agent_trajectories", {
                "step": step,
                "positions": [drone.position for drone in self.drones],
                "statuses": [drone.get_status() for drone in self.drones]
            })
            
            # Render if needed
            if step % render_interval == 0:
                render(
                    self.fire_sim,
                    self.drones,
                    step=step,
                    show_weather=True
                )
            
            # Print progress
            if step % 10 == 0:
                active_drones = sum(1 for drone in self.drones if drone.is_active)
                strategy_name = strategy["strategy"] if strategy else "none"
                print(f"Step {step:3d}: fire {fire_coverage*100:5.1f}% | "
                      f"drones {active_drones}/{self.num_drones} | "
                      f"strategy: {strategy_name}")
            
            # Check if fire is extinguished
            if not self.fire_sim.is_fire_active():
                print(f"\n🔥 Fire extinguished at step {step}!")
                break
        
        # Finalize simulation
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate final metrics
        final_metrics = {
            "total_steps": step + 1,
            "final_fire_coverage": fire_coverage * 100,
            "total_suppressions": sum(1 for step_data in self.logger.data["step_data"] 
                                    for action in step_data.get("actions_taken", [])
                                    if action.get("action") == 5),
            "simulation_duration": duration,
            "strategy_summary": self.llm_strategy_agent.get_strategy_summary() if self.llm_strategy_agent else None
        }
        
        self.logger.data["performance_metrics"] = final_metrics
        self.logger.save()
        
        print(f"\n✅ Phase 3 simulation complete!")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Final fire coverage: {fire_coverage*100:.1f}%")
        print(f"Total suppressions: {final_metrics['total_suppressions']}")
        
        return final_metrics


def main():
    """Run Phase 3 simulation with different configurations."""
    print("AURORA Phase 3 - Real Data + LLM Strategy Simulation")
    print("=" * 60)
    
    # Configuration options
    configs = [
        {
            "name": "Basic Phase 3",
            "use_real_data": False,
            "use_llm_strategy": True,
            "enable_failures": False
        },
        {
            "name": "Full Phase 3",
            "use_real_data": True,
            "use_llm_strategy": True,
            "enable_failures": True
        }
    ]
    
    for i, config in enumerate(configs):
        print(f"\n🔧 Running Configuration {i+1}: {config['name']}")
        
        sim = Phase3Simulation(
            scenario_name=f"phase3_test_{i+1}",
            num_drones=3,
            use_real_data=config["use_real_data"],
            use_llm_strategy=config["use_llm_strategy"],
            enable_failures=config["enable_failures"]
        )
        
        results = sim.run(max_steps=50, render_interval=10)
        
        print(f"Results: {results}")


if __name__ == "__main__":
    main() 