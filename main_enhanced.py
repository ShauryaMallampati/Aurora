"""
Run wildfire sims with PPO + heuristics, plus optional weather logging.
"""

from __future__ import annotations

import os
import numpy as np
import matplotlib.pyplot as plt
import json
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import random

try:
    from .env.fire_sim import FireSim
    from .agents.drone_agent import DroneAgent
    from .utils.visualizer import render
except ImportError:
    from env.fire_sim import FireSim
    from agents.drone_agent import DroneAgent
    from utils.visualizer import render


class SimulationLogger:
    """Tracks what happens during a simulation run."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_data = {
            'simulation_config': {},
            'step_data': [],
            'agent_data': [],
            'fire_data': [],
            'weather_data': []
        }
    
    def log_config(self, config: Dict[str, Any]) -> None:
        """Log simulation configuration."""
        self.log_data['simulation_config'] = config
    
    def log_step(self, step: int, fire_sim: FireSim, agents: List[DroneAgent], 
                 actions: List[int], results: List[Dict[str, Any]]) -> None:
        """Log data for each simulation step."""
        step_data = {
            'step': step,
            'fire_coverage': fire_sim.get_fire_coverage(),
            'fire_intensity': fire_sim.get_fire_intensity(),
            'weather': fire_sim.get_weather_info(),
            'agent_positions': [agent.position for agent in agents],
            'agent_statuses': [agent.get_status() for agent in agents],
            'actions': actions,
            'action_results': results
        }
        self.log_data['step_data'].append(step_data)
    
    def save_logs(self, filename: str = None) -> str:
        """Save all logged data to JSON file."""
        if filename is None:
            filename = f"aurora_simulation_{self.timestamp}.json"
        
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(self.log_data, f, indent=2, default=str)
        
        return filepath


class PPOAgent:
    """Wrapper for trained PPO agents."""
    
    def __init__(self, model_path: str):
        try:
            from stable_baselines3 import PPO
            self.model = PPO.load(model_path)
            self.is_loaded = True
        except Exception as e:
            print(f"Warning: Could not load PPO model from {model_path}: {e}")
            self.is_loaded = False
    
    def predict(self, observation: np.ndarray) -> int:
        """Predict action given observation."""
        if self.is_loaded:
            action, _ = self.model.predict(observation, deterministic=True)
            return int(action)
        else:
            return 0  # default to stay (safe noop)


def create_agents(agent_configs: List[Dict[str, Any]], fire_sim: FireSim) -> List[DroneAgent]:
    """Set up drones from the given config."""
    agents = []
    navigable = np.where(fire_sim.terrain != 3)
    available_positions = list(zip(navigable[0], navigable[1]))
    np.random.shuffle(available_positions)
    
    for i, config in enumerate(agent_configs):
        pos = available_positions[i % len(available_positions)]
        agent = DroneAgent(
            start_pos=pos,
            agent_id=config.get('agent_id', f"agent_{i}"),
            max_battery=config.get('max_battery', 100.0),
            max_water=config.get('max_water', 50.0),
            sensor_range=config.get('sensor_range', 5),
            communication_range=config.get('communication_range', 8)
        )
        agents.append(agent)
    
    return agents


def heuristic_action(drone: DroneAgent, sim: FireSim) -> int:
    """Enhanced heuristic action selection."""
    # If we can suppress and a neighbor is burning, do it
    if drone.can_suppress():
        r, c = drone.position
        for dr, dc, action in [(-1, 0, 1), (1, 0, 2), (0, -1, 3), (0, 1, 4)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < sim.grid_size[0] and 0 <= nc < sim.grid_size[1]:
                if sim.fire_state[nr, nc] == 1:
                    return 5  # suppress fire
    
    # Low battery: head to recharge
    if drone.battery_percentage < 30:
        recharge_target = find_nearest_recharge_zone(drone, sim)
        if recharge_target:
            return move_toward_target(drone, recharge_target, sim)
    
    # Low water: go refill
    if drone.water_percentage < 20:
        recharge_target = find_nearest_recharge_zone(drone, sim)
        if recharge_target:
            return move_toward_target(drone, recharge_target, sim)
    
    # Otherwise chase nearest burning cell
    target = find_nearest_burning_target(drone, sim)
    if target:
        return move_toward_target(drone, target, sim)
    
    # No clear target: maybe scan
    if random.random() < 0.1:  # 10% chance to scan
        return 6  # scan
    
    return 0  # stay put


def find_nearest_burning_target(drone: DroneAgent, sim: FireSim) -> Optional[Tuple[int, int]]:
    """Find the nearest burning cell."""
    burning_coords = np.argwhere(sim.fire_state == 1)
    if burning_coords.size == 0:
        return None
    
    pos = np.array(drone.position)
    distances = np.sum(np.abs(burning_coords - pos), axis=1)
    idx = int(np.argmin(distances))
    return tuple(int(x) for x in burning_coords[idx])


def find_nearest_recharge_zone(drone: DroneAgent, sim: FireSim) -> Optional[Tuple[int, int]]:
    """Find the nearest recharge zone (road or water)."""
    recharge_coords = np.argwhere(np.isin(sim.terrain, [2, 3]))  # road or water
    if recharge_coords.size == 0:
        return None
    
    pos = np.array(drone.position)
    distances = np.sum(np.abs(recharge_coords - pos), axis=1)
    idx = int(np.argmin(distances))
    return tuple(int(x) for x in recharge_coords[idx])


def move_toward_target(drone: DroneAgent, target: Tuple[int, int], sim: FireSim) -> int:
    """Move toward a target using Manhattan distance."""
    tr, tc = target
    r, c = drone.position
    
    # Move by row first, then column
    if tr < r and r > 0:
        return 1  # up
    if tr > r and r < sim.grid_size[0] - 1:
        return 2  # down
    if tc < c and c > 0:
        return 3  # left
    if tc > c and c < sim.grid_size[1] - 1:
        return 4  # right
    
    return 0  # stay put


def run_enhanced_simulation(
    num_drones: int = 3,
    steps: int = 50,
    render_every: int = 1,
    agent_type: str = "heuristic",  # "heuristic", "ppo", "mixed"
    ppo_model_path: str = "ppo_aurora_enhanced.zip",
    wind_direction: Tuple[float, float] = (0.5, 0.5),
    wind_intensity: float = 1.5,
    humidity: float = 0.3,
    temperature: float = 30.0,
    save_logs: bool = True
) -> Dict[str, Any]:
    """Run an enhanced wildfire simulation with configurable agents and conditions."""
    
    # Spin up logger
    logger = SimulationLogger()
    
    # Log config
    config = {
        'num_drones': num_drones,
        'steps': steps,
        'agent_type': agent_type,
        'wind_direction': wind_direction,
        'wind_intensity': wind_intensity,
        'humidity': humidity,
        'temperature': temperature,
        'timestamp': datetime.now().isoformat()
    }
    logger.log_config(config)
    
    # Start fire sim
    sim = FireSim(
        wind_direction=wind_direction,
        wind_intensity=wind_intensity,
        humidity=humidity,
        temperature=temperature
    )
    
    # Create agents
    agent_configs = []
    for i in range(num_drones):
        config = {
            'agent_id': f"{agent_type}_agent_{i}",
            'max_battery': 100.0,
            'max_water': 50.0,
            'sensor_range': 5,
            'communication_range': 8
        }
        agent_configs.append(config)
    
    agents = create_agents(agent_configs, sim)
    
    # Load PPO if needed
    ppo_agent = None
    if agent_type in ["ppo", "mixed"]:
        ppo_agent = PPOAgent(ppo_model_path)
    
    # Track metrics over time
    coverage_history = []
    battery_history = []
    water_history = []
    suppression_history = []
    
    print(f"Starting enhanced AURORA simulation:")
    print(f"  Agents: {num_drones} {agent_type} drones")
    print(f"  Wind: {wind_direction} (intensity: {wind_intensity})")
    print(f"  Weather: {temperature}°C, {humidity*100:.0f}% humidity")
    print(f"  Steps: {steps}")
    print("-" * 50)
    
    for step_idx in range(steps):
        actions = []
        results = []
        
        # Pick actions per drone
        for i, drone in enumerate(agents):
            if agent_type == "heuristic":
                action = heuristic_action(drone, sim)
            elif agent_type == "ppo":
                if ppo_agent and ppo_agent.is_loaded:
                    obs = drone.observe(sim)
                    action = ppo_agent.predict(obs)
                else:
                    action = heuristic_action(drone, sim)
            elif agent_type == "mixed":
                if i < num_drones // 2:  # first half use PPO
                    if ppo_agent and ppo_agent.is_loaded:
                        obs = drone.observe(sim)
                        action = ppo_agent.predict(obs)
                    else:
                        action = heuristic_action(drone, sim)
                else:  # second half use heuristic
                    action = heuristic_action(drone, sim)
            else:
                action = 0
            
            actions.append(action)
            result = drone.act(action, sim, agents)
            results.append(result)
        
        # Log this step
        logger.log_step(step_idx, sim, agents, actions, results)
        
        # Update metrics
        coverage = sim.get_fire_coverage() * 100.0
        active_drones = sum(1 for d in agents if d.is_active)
        avg_battery = np.mean([d.battery_percentage for d in agents])
        avg_water = np.mean([d.water_percentage for d in agents])
        total_suppressions = sum(1 for r in results if r['suppressed'])
        
        coverage_history.append(coverage)
        battery_history.append(avg_battery)
        water_history.append(avg_water)
        suppression_history.append(total_suppressions)
        
        # Print status
        print(f"Step {step_idx:2d}: fire {coverage:.1f}% | "
              f"drones {active_drones}/{num_drones} | "
              f"battery {avg_battery:.1f}% | "
              f"water {avg_water:.1f}% | "
              f"suppressions {total_suppressions}")
        
        # Render if needed
        if render_every > 0 and (step_idx % render_every == 0 or step_idx == steps - 1):
            output_dir = os.path.join(os.path.dirname(__file__), 'results')
            os.makedirs(output_dir, exist_ok=True)
            frame_path = os.path.join(output_dir, f'enhanced_frame_{step_idx:03d}.png')
            render(sim, agents, step=step_idx, save_path=frame_path)
        
        # Advance fire
        sim.step()
        
        # Stop if done
        if not sim.is_fire_active():
            print("Fire extinguished - simulation complete!")
            break
        
        if active_drones == 0:
            print("All drones inactive - simulation complete!")
            break
    
    # Save logs
    if save_logs:
        log_file = logger.save_logs()
        print(f"Simulation logs saved to: {log_file}")
    
    # Analyze run
    analysis = generate_analysis(
        coverage_history, battery_history, water_history, 
        suppression_history, agents, sim, config
    )
    
    # Save plots
    save_analysis_plots(analysis, config)
    
    return analysis


def generate_analysis(coverage_history: List[float], battery_history: List[float],
                     water_history: List[float], suppression_history: List[int],
                     agents: List[DroneAgent], sim: FireSim, config: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze how well the simulation went."""
    
    analysis = {
        'config': config,
        'agent_type': config.get('agent_type', 'unknown'),
        'final_metrics': {
            'final_fire_coverage': coverage_history[-1] if coverage_history else 0,
            'total_suppressions': sum(suppression_history),
            'avg_battery_remaining': battery_history[-1] if battery_history else 0,
            'avg_water_remaining': water_history[-1] if water_history else 0,
            'active_agents_final': sum(1 for a in agents if a.is_active),
            'total_distance_traveled': sum(a.distance_traveled for a in agents),
            'total_communications': sum(len(a.sent_messages) for a in agents)
        },
        'time_series': {
            'fire_coverage': coverage_history,
            'battery_levels': battery_history,
            'water_levels': water_history,
            'suppressions': suppression_history
        },
        'agent_details': [agent.get_status() for agent in agents]
    }
    
    return analysis


def save_analysis_plots(analysis: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Save charts showing what happened."""
    output_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    agent_type = analysis.get('agent_type', config.get('agent_type', 'unknown'))
    fig.suptitle(f'AURORA Enhanced Simulation Analysis\n{agent_type.title()} Agents', fontsize=16)
    
    # Fire coverage over time
    axes[0, 0].plot(analysis['time_series']['fire_coverage'], 'r-', linewidth=2)
    axes[0, 0].set_title('Fire Coverage Over Time')
    axes[0, 0].set_xlabel('Step')
    axes[0, 0].set_ylabel('Fire Coverage (%)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Resource levels over time
    axes[0, 1].plot(analysis['time_series']['battery_levels'], 'b-', label='Battery', linewidth=2)
    axes[0, 1].plot(analysis['time_series']['water_levels'], 'g-', label='Water', linewidth=2)
    axes[0, 1].set_title('Resource Levels Over Time')
    axes[0, 1].set_xlabel('Step')
    axes[0, 1].set_ylabel('Level (%)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Suppressions over time
    axes[1, 0].plot(analysis['time_series']['suppressions'], 'orange', linewidth=2)
    axes[1, 0].set_title('Fire Suppressions Per Step')
    axes[1, 0].set_xlabel('Step')
    axes[1, 0].set_ylabel('Number of Suppressions')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Final metrics summary
    metrics = analysis['final_metrics']
    summary_text = f"""
Final Fire Coverage: {metrics['final_fire_coverage']:.1f}%
Total Suppressions: {metrics['total_suppressions']}
Active Agents: {metrics['active_agents_final']}/{len(analysis['agent_details'])}
Avg Battery: {metrics['avg_battery_remaining']:.1f}%
Avg Water: {metrics['avg_water_remaining']:.1f}%
Total Distance: {metrics['total_distance_traveled']}
Communications: {metrics['total_communications']}
    """.strip()
    
    axes[1, 1].text(0.1, 0.5, summary_text, transform=axes[1, 1].transAxes,
                   fontsize=12, verticalalignment='center',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
    axes[1, 1].set_title('Final Metrics Summary')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = os.path.join(output_dir, f'enhanced_analysis_{agent_type}_{timestamp}.png')
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Analysis plots saved to: {plot_path}")


def main() -> None:
    """Run enhanced simulation with different configurations."""
    
    # CLI options
    configs = [
        {
            'name': 'Heuristic Agents',
            'agent_type': 'heuristic',
            'num_drones': 3,
            'wind_direction': (0.5, 0.5),
            'wind_intensity': 1.5
        },
        {
            'name': 'PPO Agents (if available)',
            'agent_type': 'ppo',
            'num_drones': 3,
            'wind_direction': (0.5, 0.5),
            'wind_intensity': 1.5
        },
        {
            'name': 'Mixed Agents',
            'agent_type': 'mixed',
            'num_drones': 4,
            'wind_direction': (0.5, 0.5),
            'wind_intensity': 1.5
        }
    ]
    
    print("AURORA Enhanced Simulation")
    print("=" * 50)
    
    for i, config in enumerate(configs):
        print(f"\n{i+1}. {config['name']}")
    
    # If no stdin, default to heuristic
    import sys
    if not sys.stdin.isatty():
        # No stdin: run heuristic by default
        selected_config = configs[0]
        print(f"\nAutomated mode: Running {selected_config['name']}")
    else:
        # Interactive: ask for input
        try:
            choice = input("\nSelect configuration (1-3) or press Enter for heuristic: ").strip()
            
            if choice == "2":
                selected_config = configs[1]
            elif choice == "3":
                selected_config = configs[2]
            else:
                selected_config = configs[0]
        except (EOFError, KeyboardInterrupt):
            # If input fails, use heuristic
            selected_config = configs[0]
            print(f"\nInput error: Running {selected_config['name']}")
    
    print(f"\nRunning: {selected_config['name']}")
    
    # Run simulation
    analysis = run_enhanced_simulation(
        num_drones=selected_config['num_drones'],
        steps=50,
        render_every=2,
        agent_type=selected_config['agent_type'],
        wind_direction=selected_config['wind_direction'],
        wind_intensity=selected_config['wind_intensity'],
        humidity=0.3,
        temperature=30.0
    )
    
    print(f"\nSimulation complete!")
    print(f"Final fire coverage: {analysis['final_metrics']['final_fire_coverage']:.1f}%")
    print(f"Total suppressions: {analysis['final_metrics']['total_suppressions']}")


if __name__ == '__main__':
    main() 
