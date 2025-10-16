"""
AURORA Training with Real Fire Perimeter Data

This script trains the PPO model on REAL historical fire perimeters from:
- InterAgency Fire Perimeter History (116,337 fires from 1308-2024)
- NOAA National Weather Service API (real-time weather)
- Realistic terrain generation based on location

Author: Shaurya Mallampati  
Date: October 13, 2025
ISEF 2025 Competition
"""

import sys
import os
from pathlib import Path as _Path

# Base directory (script location) so paths work regardless of working directory
_BASE_DIR = _Path(__file__).parent.resolve()
sys.path.append(str(_BASE_DIR / 'data'))

import numpy as np
import gymnasium as gym
from gymnasium import spaces
import argparse
from typing import Dict, List, Optional
import json
from pathlib import Path
from datetime import datetime, timedelta
import shutil

# Stable-Baselines3
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

# Import AURORA modules
from env.fire_sim import FireSim
from agents.drone_agent import DroneAgent
from data.real_data_integration_complete import RealDataIntegrator


class RealFireEnv(gym.Env):
    """AURORA Environment using REAL fire perimeter data."""
    
    def __init__(self, 
                 grid_size: int = 50,
                 num_drones: int = 3,
                 max_steps: int = 100,
                 integrator: Optional[RealDataIntegrator] = None):
        super().__init__()
        
        self.grid_size = grid_size
        self.num_drones = num_drones
        self.max_steps = max_steps
        self.current_step = 0
        
        # Real data integrator
        self.integrator = integrator
        
        # Observation space: 3x3 grid around drone with 6 channels
        # [fire_intensity, terrain_type, elevation, fuel_density, battery, water]
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(3, 3, 6), dtype=np.float32
        )
        
        # Action space: 8 actions
        # 0: stay, 1-4: move (up/down/left/right), 5: suppress, 6: scan, 7: communicate
        self.action_space = spaces.Discrete(8)
        
        # Initialize environment components
        self.fire_sim = None
        self.drones = []
        self.current_scenario = None
        
    def reset(self, seed=None, options=None):
        """Reset environment with a new real fire scenario."""
        super().reset(seed=seed)
        
        # Get new real fire scenario
        if self.integrator:
            try:
                self.current_scenario = self.integrator.create_training_scenario(
                    min_year=2010,
                    min_acres=100,
                    max_acres=50000
                )
                
                # Initialize fire simulation with real data
                initial_fire = self.current_scenario['initial_fire_grid'].astype(np.uint8)
                
                self.fire_sim = FireSim(
                    grid_size=self.grid_size
                )
                
                # Reset with real fire grid
                self.fire_sim.reset(initial_fire_grid=initial_fire)
                
                # Set weather from NOAA data
                weather = self.current_scenario['weather']
                wind_dirs = {'N': (0, -1), 'NE': (1, -1), 'E': (1, 0), 'SE': (1, 1), 
                           'S': (0, 1), 'SW': (-1, 1), 'W': (-1, 0), 'NW': (-1, -1)}
                wind_dir = wind_dirs.get(weather['wind_direction'], (0, 0))
                wind_speed = weather['wind_speed_mph'] / 25.0  # Normalize
                
                self.fire_sim.set_wind(wind_dir, wind_speed)
                self.fire_sim.set_weather(
                    humidity=weather['humidity'] / 100.0,
                    temperature=weather['temperature_c']
                )
                
                # Set terrain from real data
                terrain = self.current_scenario['terrain']
                self.fire_sim.elevation = (terrain['elevation'] / 3000.0).astype(np.float32)
                self.fire_sim.fuel_density = (0.7 + terrain['slope'] * 0.3).astype(np.float32)  # Higher fuel on slopes
                
                # Assert all rasters align
                expected_shape = (self.grid_size, self.grid_size)
                assert self.fire_sim.fire_state.shape == expected_shape, f"Fire grid shape mismatch: {self.fire_sim.fire_state.shape} != {expected_shape}"
                assert self.fire_sim.elevation.shape == expected_shape, f"Elevation shape mismatch: {self.fire_sim.elevation.shape} != {expected_shape}"
                assert self.fire_sim.fuel_density.shape == expected_shape, f"Fuel density shape mismatch: {self.fire_sim.fuel_density.shape} != {expected_shape}"
                
            except Exception as e:
                print(f"⚠️  Error loading real scenario: {e}")
                # STRICT MODE: No synthetic fallback - retry with another real scenario
                if self.integrator:
                    print("   Retrying with another random real scenario...")
                    return self.reset(seed=seed)
                else:
                    raise RuntimeError("No integrator available and synthetic fallback disabled")
        else:
            raise RuntimeError("No real data integrator provided - cannot proceed without real data")
        
        # Initialize drones at random positions
        self.drones = []
        for i in range(self.num_drones):
            x = np.random.randint(0, self.grid_size)
            y = np.random.randint(0, self.grid_size)
            drone = DroneAgent(start_pos=(x, y), agent_id=f"drone_{i}")
            self.drones.append(drone)
        
        self.current_step = 0
        
        # Return observation for first drone
        obs = self._get_observation(0)
        return obs, {}
    
    def _reset_simple(self):
        """Fallback simple reset if real data fails."""
        self.fire_sim = FireSim(grid_size=self.grid_size)
        self.current_scenario = {'fire_name': 'Synthetic', 'year': 2024}
    
    def step(self, action):
        """Execute action in environment."""
        
        # Execute action for first drone using DroneAgent's act() method
        drone = self.drones[0]
        
        # Use DroneAgent's built-in act() method which handles all actions
        action_result = drone.act(action, self.fire_sim, self.drones)
        
        # Step fire simulation
        self.fire_sim.step()
        self.current_step += 1
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Check termination
        terminated = self.current_step >= self.max_steps
        truncated = drone.battery <= 0
        
        # Get observation
        obs = self._get_observation(0)
        
        return obs, reward, terminated, truncated, {}
    
    def _get_observation(self, drone_id: int) -> np.ndarray:
        """Get observation for a drone (3x3 grid around it)."""
        
        drone = self.drones[drone_id]
        x, y = drone.position
        
        obs = np.zeros((3, 3, 6), dtype=np.float32)
        
        for i in range(-1, 2):
            for j in range(-1, 2):
                nx, ny = x + i, y + j
                
                # Clip to grid bounds
                nx = max(0, min(self.grid_size - 1, nx))
                ny = max(0, min(self.grid_size - 1, ny))
                
                # Channel 0: fire intensity (1=burning, 0=safe/burnt)
                obs[i+1, j+1, 0] = 1.0 if self.fire_sim.fire_state[ny, nx] == 1 else 0.0
                
                # Channel 1: terrain type (from terrain array)
                obs[i+1, j+1, 1] = self.fire_sim.terrain[ny, nx] / 3.0
                
                # Channel 2: elevation
                obs[i+1, j+1, 2] = self.fire_sim.elevation[ny, nx] / 100.0
                
                # Channel 3: fuel density
                obs[i+1, j+1, 3] = self.fire_sim.fuel_density[ny, nx]
                
                # Channel 4: drone battery (same for all cells)
                obs[i+1, j+1, 4] = drone.battery
                
                # Channel 5: drone water (same for all cells)
                obs[i+1, j+1, 5] = drone.water
        
        return obs
    
    def _calculate_reward(self) -> float:
        """Calculate reward based on fire suppression and efficiency."""
        
        # Count burning cells
        burning_cells = np.sum(self.fire_sim.fire_state == 1)
        total_cells = self.grid_size * self.grid_size
        fire_coverage = burning_cells / total_cells
        
        # Fire coverage (lower is better)
        fire_reward = -fire_coverage * 10.0  # Penalty for fire
        
        # Suppression reward
        total_suppression = sum(d.suppression_count for d in self.drones)
        suppression_reward = total_suppression * 2.0
        
        # Battery efficiency (penalize low battery)
        avg_battery = sum(d.battery for d in self.drones) / len(self.drones)
        battery_penalty = -1.0 if avg_battery < 0.2 else 0.0
        
        # Total reward
        reward = fire_reward + suppression_reward + battery_penalty
        
        return reward


class TrainingCallback(BaseCallback):
    """Custom callback to log training progress with clear step tracking."""
    
    def __init__(self, check_freq: int = 1000, total_timesteps: int = 50000, verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.total_timesteps = total_timesteps
        self.episode_rewards = []
        self.episode_lengths = []
        self.start_time = None
        
    def _on_training_start(self) -> None:
        """Called at the beginning of training."""
        self.start_time = datetime.now()
        print(f"\n🚀 Training started at {self.start_time.strftime('%H:%M:%S')}")
        print("="*80)
        
    def _on_step(self) -> bool:
        
        if self.n_calls % self.check_freq == 0:
            # Calculate progress
            progress = (self.n_calls / self.total_timesteps) * 100
            elapsed = datetime.now() - self.start_time
            steps_per_sec = self.n_calls / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
            remaining_steps = self.total_timesteps - self.n_calls
            eta_seconds = remaining_steps / steps_per_sec if steps_per_sec > 0 else 0
            eta = str(timedelta(seconds=int(eta_seconds)))
            
            # Log progress
            print(f"\n📊 STEP {self.n_calls:,} / {self.total_timesteps:,} ({progress:.1f}%)")
            print(f"   ⏱️  Speed: {steps_per_sec:.1f} steps/sec | ETA: {eta}")
            
            if len(self.episode_rewards) > 0:
                mean_reward = np.mean(self.episode_rewards[-10:])
                mean_length = np.mean(self.episode_lengths[-10:])
                print(f"   🎯 Mean reward (last 10 ep): {mean_reward:.2f}")
                print(f"   📏 Mean episode length: {mean_length:.1f}")
            print("-"*80)
        
        return True
    
    def _on_rollout_end(self) -> None:
        # Store episode stats
        if len(self.model.ep_info_buffer) > 0:
            for ep_info in self.model.ep_info_buffer:
                if isinstance(ep_info, dict):
                    self.episode_rewards.append(ep_info.get('r', 0))
                    self.episode_lengths.append(ep_info.get('l', 0))


def make_env(rank: int):
    """Create a single environment instance.
    
    Note: Each subprocess loads its own RealDataIntegrator to avoid 
    multiprocessing/pickling issues with GeoDataFrame.
    """
    def _init():
        # Load integrator in each subprocess to avoid pickling geopandas
        integrator = RealDataIntegrator()
        
        env = RealFireEnv(
            grid_size=50,
            num_drones=3,
            max_steps=100,
            integrator=integrator
        )
        env = Monitor(env)
        return env
    return _init


def main():
    parser = argparse.ArgumentParser(description='Train AURORA with real fire data')
    parser.add_argument('--timesteps', type=int, default=500000, 
                       help='Total training timesteps')
    parser.add_argument('--n_envs', type=int, default=8, 
                       help='Number of parallel environments')
    parser.add_argument('--save_freq', type=int, default=50000,
                       help='Save model every N steps')
    parser.add_argument('--verbose', type=int, default=1,
                       help='Verbosity level')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("AURORA TRAINING WITH REAL FIRE PERIMETER DATA")
    print("="*80)
    print(f"Total timesteps: {args.timesteps:,}")
    print(f"Parallel environments: {args.n_envs}")
    print(f"Save frequency: {args.save_freq:,}")
    print("="*80 + "\n")
    
    # Create vectorized environments
    # Note: Each subprocess will load its own RealDataIntegrator
    print(f"Creating {args.n_envs} parallel environments...")
    print("(Each environment will load fire perimeter data independently)")
    
    if args.n_envs > 1:
        env = SubprocVecEnv([make_env(i) for i in range(args.n_envs)])
    else:
        env = DummyVecEnv([make_env(0)])
    
    print("✅ Environments created\n")
    
    # Create PPO model
    print("Initializing PPO model...")
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        verbose=args.verbose,
        tensorboard_log=None  # Disable tensorboard logging
    )
    
    print("✅ Model initialized\n")
    
    # Create callback with total timesteps for progress tracking
    callback = TrainingCallback(check_freq=2000, total_timesteps=args.timesteps, verbose=1)
    
    # Train
    print("="*80)
    print("STARTING TRAINING")
    print("="*80 + "\n")
    
    start_time = datetime.now()
    
    try:
        model.learn(
            total_timesteps=args.timesteps,
            callback=callback,
            progress_bar=False  # Disable progress bar to avoid tqdm dependency
        )
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "="*80)
        print("✅ TRAINING COMPLETE")
        print("="*80)
        print(f"Training time: {training_time/60:.1f} minutes")
        print(f"Timesteps: {args.timesteps:,}")
        print(f"Timesteps/sec: {args.timesteps/training_time:.0f}")
        print("="*80 + "\n")
        
        # Ensure results directory exists (next to this script)
        results_dir = _BASE_DIR / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)

        # Save final model (this creates a .zip file via Stable-Baselines3)
        save_base = results_dir / 'aurora_real_fire_model'
        model.save(str(save_base))

        # The SB3 save creates `save_base.zip`. Unpack it into a folder with the same name
        zip_path = save_base.with_suffix('.zip')
        extract_dir = save_base
        try:
            if zip_path.exists():
                shutil.unpack_archive(str(zip_path), extract_dir=str(extract_dir))
                # Remove the zip to leave only the unzipped files
                zip_path.unlink()
                print(f"💾 Model saved to {extract_dir.resolve()} (unzipped files)")
            else:
                # Fallback: if no zip was created, SB3 may have saved differently
                print(f"💾 Model saved (no zip found) at {save_base.resolve()}")
        except Exception as e:
            print(f"⚠️  Warning: failed to unpack model zip: {e}")
            print(f"💾 Model zip remains at {zip_path} if present")
        
        # Save training summary
        summary = {
            'total_timesteps': args.timesteps,
            'n_envs': args.n_envs,
            'training_time_minutes': training_time / 60,
            'fire_records_available': 116337,  # Known from dataset
            'data_source': 'InterAgency Fire Perimeter History (1308-2024)',
            'weather_source': 'NOAA National Weather Service API',
            'date': datetime.now().isoformat()
        }
        
        summary_path = results_dir / 'training_summary.json'
        with open(str(summary_path), 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📊 Training summary saved to {summary_path.resolve()}\n")
        
    except KeyboardInterrupt:
        print("\n⚠️  Training interrupted by user")
        print("Saving current model...")
        # Save interrupted model and unpack like the final save
        results_dir = _BASE_DIR / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)
        interrupted_base = results_dir / 'aurora_real_fire_model_interrupted'
        model.save(str(interrupted_base))
        interrupted_zip = interrupted_base.with_suffix('.zip')
        try:
            if interrupted_zip.exists():
                shutil.unpack_archive(str(interrupted_zip), extract_dir=str(interrupted_base))
                interrupted_zip.unlink()
                print(f"💾 Interrupted model saved to {interrupted_base.resolve()} (unzipped files)\n")
            else:
                print(f"💾 Interrupted model saved (no zip found) at {interrupted_base.resolve()}\n")
        except Exception as e:
            print(f"⚠️  Warning: failed to unpack interrupted model zip: {e}")
            print(f"💾 Interrupted model zip remains at {interrupted_zip} if present\n")
    
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        env.close()
        print("Environment closed")


if __name__ == "__main__":
    main()
