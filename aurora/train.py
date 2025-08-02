"""
Enhanced training script for AURORA drone agents using PPO.

This module defines an enhanced OpenAI Gymnasium environment that wraps the
``FireSim`` simulator and a single :class:`DroneAgent`.  The environment
now supports:

- Enhanced observation space with 6 channels (terrain, fire, elevation, fuel, battery, water)
- 8 discrete actions including scan and communicate
- Sophisticated reward shaping for suppression, survival, cooperation
- Battery and water management
- Fault simulation and recovery
- Multi-agent communication capabilities

The training uses PPO with parameter sharing across multiple parallel environments
to approximate multi-agent learning.
"""

from __future__ import annotations

import os
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Tuple, Any, Dict, List
import random

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import BaseCallback

try:
    from .env.fire_sim import FireSim
    from .agents.drone_agent import DroneAgent
except ImportError:
    from env.fire_sim import FireSim
    from agents.drone_agent import DroneAgent


class TrainingCallback(BaseCallback):
    """Custom callback to track training progress and save intermediate models."""
    
    def __init__(self, verbose: int = 0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.suppression_counts = []
        self.survival_times = []
        
    def _on_step(self) -> bool:
        # Log metrics every 1000 steps
        if self.n_calls % 1000 == 0:
            if len(self.training_env.buf_rews) > 0:
                mean_reward = np.mean([np.sum(rews) for rews in self.training_env.buf_rews])
                self.episode_rewards.append(mean_reward)
                
                if self.verbose > 0:
                    print(f"Step {self.n_calls}: Mean reward = {mean_reward:.2f}")
        
        return True


class EnhancedDroneFireEnv(gym.Env):
    """Enhanced Gymnasium environment for training a single drone against a fire.

    The observation consists of a 3×3×6 neighbourhood (terrain, fire state,
    elevation, fuel density, battery, water) around the drone.  The action
    space contains eight discrete actions: stay, move up/down/left/right,
    suppress, scan, and communicate.  The reward system is sophisticated
    and includes:

    - +10 for successful fire suppression
    - -1 per timestep for fire spread
    - +2 for staying in communication range with other agents
    - +1 for efficient resource management
    - -5 for battery depletion
    - +0.1 for each step of survival
    """

    metadata = {"render.modes": ["human"]}

    def __init__(self, grid_size: int = 20, max_steps: int = 50, seed: int | None = None,
                 wind_direction: Tuple[float, float] = (0.0, 0.0),
                 wind_intensity: float = 1.0,
                 humidity: float = 0.5,
                 temperature: float = 25.0) -> None:
        super().__init__()
        
        # Initialize enhanced fire simulator
        self.sim = FireSim(wind_direction=wind_direction, 
                          wind_intensity=wind_intensity,
                          humidity=humidity,
                          temperature=temperature)
        
        if seed is not None:
            # Optionally regenerate terrain for reproducibility
            try:
                from .data.generate_map import generate_map
            except ImportError:
                from data.generate_map import generate_map
            terrain = generate_map(size=grid_size, seed=seed)
            map_path = os.path.join(os.path.dirname(__file__), 'data', 'terrain_map.npy')
            np.save(map_path, terrain)
            # Reload the simulator with the new map
            self.sim = FireSim(wind_direction=wind_direction, 
                              wind_intensity=wind_intensity,
                              humidity=humidity,
                              temperature=temperature)
        
        self.max_steps = max_steps
        
        # Create a drone at a random navigable location
        start = self._random_start_position()
        self.drone = DroneAgent(start, agent_id="training_drone")
        
        # Create some dummy agents for communication testing
        self.other_agents = self._create_dummy_agents(3)
        
        # Enhanced observation space: 3×3×6 values
        self.observation_space = spaces.Box(low=0, high=1, shape=(3, 3, 6), dtype=np.float32)
        
        # Enhanced action space: 8 discrete actions
        self.action_space = spaces.Discrete(8)
        
        # Internal step counter and metrics
        self.current_step = 0
        self.total_suppressions = 0
        self.total_reward = 0.0
        self.initial_fire_intensity = 0

    def _random_start_position(self) -> Tuple[int, int]:
        """Select a random starting position for the drone on a navigable cell."""
        navigable = np.where(self.sim.terrain != 3)  # Not water
        idx = np.random.choice(len(navigable[0]))
        return int(navigable[0][idx]), int(navigable[1][idx])

    def _create_dummy_agents(self, num_agents: int) -> List[DroneAgent]:
        """Create dummy agents for communication testing."""
        agents = []
        for i in range(num_agents):
            pos = self._random_start_position()
            agent = DroneAgent(pos, agent_id=f"dummy_{i}")
            agents.append(agent)
        return agents

    def _calculate_reward(self, action_result: Dict[str, Any]) -> float:
        """Calculate sophisticated reward based on action results and environment state."""
        reward = 0.0
        
        # Fire suppression reward
        if action_result['suppressed']:
            reward += 10.0
            self.total_suppressions += 1
        
        # Fire spread penalty (negative reward for fire growth)
        current_fire_intensity = self.sim.get_fire_intensity()
        if hasattr(self, 'previous_fire_intensity'):
            fire_growth = current_fire_intensity - self.previous_fire_intensity
            reward -= fire_growth * 2.0  # Penalize fire growth
        self.previous_fire_intensity = current_fire_intensity
        
        # Resource management rewards
        if self.drone.battery_percentage > 50:
            reward += 0.1  # Reward for maintaining good battery
        if self.drone.water_percentage > 30:
            reward += 0.1  # Reward for maintaining water supply
        
        # Communication reward
        if action_result['messages_sent'] > 0:
            reward += 2.0  # Reward for communication
        
        # Survival reward
        reward += 0.1  # Small reward for each step of survival
        
        # Battery depletion penalty
        if not self.drone.is_active:
            reward -= 5.0
        
        # Efficiency rewards
        if action_result['distance_moved'] > 0:
            # Small penalty for movement to encourage efficiency
            reward -= 0.05
        
        # Recharge zone reward
        if self.drone.is_at_recharge_zone(self.sim):
            reward += 0.2  # Reward for being at recharge zone
        
        return reward

    def reset(self, *, seed: int | None = None, options: Dict[str, Any] | None = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the environment to its initial state and return the first observation."""
        super().reset(seed=seed, options=options)
        
        # Reset fire simulator and drone
        self.sim.reset()
        self.current_step = 0
        self.total_suppressions = 0
        self.total_reward = 0.0
        
        # Random start position for the drone
        start = self._random_start_position()
        self.drone.reset(start)
        
        # Reset dummy agents
        self.other_agents = self._create_dummy_agents(3)
        
        # Record initial fire intensity
        self.initial_fire_intensity = self.sim.get_fire_intensity()
        self.previous_fire_intensity = self.initial_fire_intensity
        
        obs = self.drone.observe(self.sim)
        return obs, {}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Perform one environment step given an action.

        Args:
            action: integer in the range [0, 7]

        Returns:
            observation: the new local neighbourhood
            reward: calculated reward
            terminated: whether the episode is finished
            truncated: whether the episode was truncated by the step limit
            info: auxiliary diagnostic information
        """
        # Apply the drone action and get results
        action_result = self.drone.act(action, self.sim, self.other_agents)
        
        # Calculate reward
        reward = self._calculate_reward(action_result)
        self.total_reward += reward
        
        # Advance fire dynamics
        self.sim.step()
        self.current_step += 1
        
        # Check termination conditions
        terminated = not self.sim.is_fire_active() or not self.drone.is_active
        truncated = self.current_step >= self.max_steps
        
        # Get new observation
        obs = self.drone.observe(self.sim)
        
        # Prepare info dictionary
        info = {
            'step': self.current_step,
            'fire_coverage': self.sim.get_fire_coverage(),
            'fire_intensity': self.sim.get_fire_intensity(),
            'battery': self.drone.battery_percentage,
            'water': self.drone.water_percentage,
            'suppressions': self.total_suppressions,
            'total_reward': self.total_reward,
            'action_result': action_result,
            'weather': self.sim.get_weather_info()
        }
        
        return obs, reward, terminated, truncated, info

    def render(self) -> None:
        """Optional human‑readable rendering of the environment state."""
        try:
            from .utils.visualizer import render as render_fn
        except ImportError:
            from utils.visualizer import render as render_fn
        render_fn(self.sim, [self.drone] + self.other_agents, step=self.current_step)


def main() -> None:
    """Run enhanced PPO training for the drone agent."""
    print("Starting enhanced AURORA training...")
    
    # Create callback for tracking progress
    callback = TrainingCallback(verbose=1)
    
    # Use 8 parallel environments for better experience collection
    env = make_vec_env(lambda: EnhancedDroneFireEnv(
        wind_direction=(0.5, 0.5),  # Diagonal wind
        wind_intensity=1.5,
        humidity=0.3,  # Dry conditions
        temperature=30.0  # Hot conditions
    ), n_envs=8)
    
    # Create PPO model with enhanced parameters
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01  # Encourage exploration
    )
    
    # Train for extended period (50k timesteps)
    timesteps = 50000
    print(f"Training for {timesteps} timesteps...")
    model.learn(total_timesteps=timesteps, callback=callback)
    
    # Save the trained agent
    model.save("ppo_aurora_enhanced")
    print("Enhanced training complete, model saved to ppo_aurora_enhanced.zip")
    
    # Test the trained model
    print("\nTesting trained model...")
    test_env = EnhancedDroneFireEnv()
    obs, _ = test_env.reset()
    
    total_reward = 0
    for step in range(50):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = test_env.step(action)
        total_reward += reward
        
        if step % 10 == 0:
            print(f"Test step {step}: reward={reward:.2f}, fire_coverage={info['fire_coverage']:.2%}, "
                  f"battery={info['battery']:.1f}%")
        
        if terminated or truncated:
            break
    
    print(f"\nTest completed: Total reward = {total_reward:.2f}")


if __name__ == "__main__":
    main()