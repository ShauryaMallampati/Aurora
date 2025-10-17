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

# Usage notes:
# - To resume from a checkpoint folder created by this script, pass --resume <path-to-checkpoint-folder>
#   e.g. --resume results/aurora_ppo_checkpoint_100000steps
# - The script will try to infer how many timesteps were already completed from the folder name
#   (pattern like '100000steps' or '100,000steps') and continue for the remaining timesteps.

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
import zipfile

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
    """Custom callback to log training progress with clear step tracking and checkpointing."""
    
    def __init__(self, check_freq: int = 1000, total_timesteps: int = 2000000, save_freq: int = 100000, verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.total_timesteps = total_timesteps
        self.save_freq = save_freq
        self.episode_rewards = []
        self.episode_lengths = []
        self.start_time = None
        self.last_save_step = 0
        
    def _on_training_start(self) -> None:
        """Called at the beginning of training."""
        self.start_time = datetime.now()
        print(f"\n🚀 Training started at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 Total steps: {self.total_timesteps:,} | Checkpoint every: {self.save_freq:,} steps")
        print("="*80)
        
    def _on_step(self) -> bool:
        """Called after every step."""
        
        # Progress reporting
        if self.n_calls % self.check_freq == 0 or self.n_calls == 1:
            progress = (self.n_calls / self.total_timesteps) * 100
            elapsed = datetime.now() - self.start_time
            steps_per_sec = self.n_calls / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
            remaining_steps = self.total_timesteps - self.n_calls
            eta_seconds = remaining_steps / steps_per_sec if steps_per_sec > 0 else 0
            eta = str(timedelta(seconds=int(eta_seconds)))
            elapsed_str = str(timedelta(seconds=int(elapsed.total_seconds())))
            
            # Log progress
            print(f"\n✨ STEP {self.n_calls:,} / {self.total_timesteps:,} ({progress:.1f}%) ✨")
            print(f"   ⏱️  Elapsed: {elapsed_str} | Speed: {steps_per_sec:.1f} steps/sec | ETA: {eta}")
            
            if len(self.episode_rewards) > 0:
                mean_reward = np.mean(self.episode_rewards[-10:]) if len(self.episode_rewards) >= 10 else np.mean(self.episode_rewards)
                mean_length = np.mean(self.episode_lengths[-10:]) if len(self.episode_lengths) >= 10 else np.mean(self.episode_lengths)
                print(f"   🎯 Mean reward (last 10 ep): {mean_reward:.2f}")
                print(f"   📏 Mean episode length: {mean_length:.1f}")
            print("-"*80)
        
        # Checkpoint saving
        if self.n_calls % self.save_freq == 0 and self.n_calls > self.last_save_step:
            self._save_checkpoint()
            self.last_save_step = self.n_calls
        
        return True
    
    def _save_checkpoint(self) -> None:
        """Save model checkpoint with step information."""
        results_dir = _Path(__file__).parent.resolve() / 'results'
        try:
            results_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"   ❌ Could not create results directory '{results_dir}': {e}")
            return

        checkpoint_name = f"aurora_ppo_checkpoint_{self.n_calls}steps"
        checkpoint_path = results_dir / 'checkpoints' / checkpoint_name
        checkpoint_zip_tmp = checkpoint_path.with_suffix('.zip.tmp')
        checkpoint_zip = checkpoint_path.with_suffix('.zip')

        # Ensure checkpoints dir exists
        checkpoints_dir = results_dir / 'checkpoints'
        try:
            checkpoints_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"   ❌ Could not create checkpoints directory '{checkpoints_dir}': {e}")
            return

        tmp_extract_dir = checkpoint_path.with_suffix('.tmp')
        try:
            # Save model to a temporary zip file first
            self.model.save(str(checkpoint_zip_tmp))

            # Atomically move tmp zip to final zip
            try:
                os.replace(str(checkpoint_zip_tmp), str(checkpoint_zip))
            except Exception:
                # If os.replace fails (permissions etc), fallback to rename
                os.rename(str(checkpoint_zip_tmp), str(checkpoint_zip))

            # Remove any previous partial extract
            if tmp_extract_dir.exists():
                shutil.rmtree(str(tmp_extract_dir))

            # Extract zip into a temp dir then move into place
            with zipfile.ZipFile(str(checkpoint_zip), 'r') as zf:
                zf.extractall(str(tmp_extract_dir))

            if checkpoint_path.exists():
                shutil.rmtree(str(checkpoint_path))
            os.replace(str(tmp_extract_dir), str(checkpoint_path))

            print(f"   💾 Checkpoint saved: {checkpoint_name} ({self.n_calls:,} steps)")

        except Exception as e:
            # Cleanup any partial artifacts
            try:
                if checkpoint_zip_tmp.exists():
                    checkpoint_zip_tmp.unlink()
            except Exception:
                pass
            try:
                if tmp_extract_dir.exists():
                    shutil.rmtree(str(tmp_extract_dir))
            except Exception:
                pass
            print(f"   ⚠️  Error saving checkpoint: {e}")
    
    def _on_rollout_end(self) -> None:
        """Store episode statistics."""
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
    parser.add_argument('--timesteps', type=int, default=2000000, 
                       help='Total training timesteps (default: 2M for 2 million)')
    parser.add_argument('--n_envs', type=int, default=4, 
                       help='Number of parallel environments')
    parser.add_argument('--save_freq', type=int, default=50000,
                       help='Save model every N steps (checkpoints)')
    parser.add_argument('--resume', type=str, default=None,
                       help='Path to checkpoint folder to resume from (optional)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--verbose', type=int, default=1,
                       help='Verbosity level')
    
    args = parser.parse_args()
    
    # Set seeds for reproducibility
    np.random.seed(args.seed)
    import random
    random.seed(args.seed)
    
    print("\n" + "="*80)
    print("AURORA TRAINING WITH REAL FIRE PERIMETER DATA")
    print("="*80)
    print(f"Total timesteps: {args.timesteps:,}")
    print(f"Parallel environments: {args.n_envs}")
    print(f"Save frequency: {args.save_freq:,}")
    print(f"Random seed: {args.seed}")
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

    # Helper: normalize checkpoint folder names under results/checkpoints
    def _normalize_checkpoints(results_dir: _Path):
        ckpt_dir = results_dir / 'checkpoints'
        if not ckpt_dir.exists():
            return
        for child in ckpt_dir.iterdir():
            # look for patterns like 'checkpoint_step_500' or 'checkpoint_step_1000'
            name = child.name
            m = None
            import re
            m = re.search(r"_step_(\d+)$", name)
            if m:
                steps = int(m.group(1))
                new_name = f"aurora_ppo_checkpoint_{steps}steps"
                new_path = ckpt_dir / new_name
                if not new_path.exists():
                    try:
                        child.rename(new_path)
                        print(f"🔁 Renamed checkpoint '{name}' -> '{new_name}'")
                    except Exception as e:
                        print(f"⚠️  Failed to rename {child}: {e}")

    # Normalize existing checkpoint names so resume detection works
    results_root = _Path(__file__).parent.resolve() / 'results'
    _normalize_checkpoints(results_root)

    # If resuming, we will load the model from the provided folder after env is created
    model = None
    resumed_steps = 0
    if args.resume:
        # Try to infer completed steps from folder name, e.g. '..._100000steps' or '..._100,000steps'
        import re
        # First try the new '..._12345steps' pattern
        m = re.search(r"(\d{1,3}(?:,\d{3})*)steps", args.resume)
        if not m:
            # fallback: detect '_step_123' or 'checkpoint_step_123' patterns
            m = re.search(r"_step_(\d+)", args.resume)
        if m:
            # remove commas
            resumed_steps = int(m.group(1).replace(',', ''))
            print(f"🔁 Resuming from checkpoint folder '{args.resume}' (detected {resumed_steps:,} completed steps)")
        else:
            print(f"🔁 Resuming from checkpoint folder '{args.resume}' (completed steps unknown)")
    
    # Create or load PPO model
    if args.resume:
        try:
            print("Loading model from resume path...")
            model = PPO.load(args.resume, env=env)
            print("✅ Model loaded from resume folder\n")
        except Exception as e:
            print(f"⚠️  Failed to load model from {args.resume}: {e}")
            print("   Falling back to initializing a fresh PPO model")

    if model is None:
        print("Initializing new PPO model...")
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
            seed=args.seed,
            verbose=args.verbose,
            tensorboard_log=None  # Disable tensorboard logging
        )
        print("✅ Model initialized\n")

    # Compute remaining timesteps when resuming (if we could detect previous steps)
    if args.resume and resumed_steps > 0:
        remaining_timesteps = max(0, args.timesteps - resumed_steps)
        print(f"Target total timesteps: {args.timesteps:,}, already completed: {resumed_steps:,}, remaining: {remaining_timesteps:,}")
    elif args.resume and resumed_steps == 0:
        # unknown previous progress: assume args.timesteps is the additional timesteps to run
        remaining_timesteps = args.timesteps
        print(f"Previous completed steps unknown; training will run for {remaining_timesteps:,} additional steps")
    else:
        remaining_timesteps = args.timesteps

    # Create callback with total timesteps for progress tracking
    callback = TrainingCallback(check_freq=5000, total_timesteps=remaining_timesteps, save_freq=args.save_freq, verbose=1)
    
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
