"""
AURORA Training with Hybrid PPO + LLM Strategy

This script trains a hybrid model that combines:
1. PPO (Proximal Policy Optimization) - for low-level action execution
2. LLM (GPT-4o-mini or LLaMA) - for high-level strategic guidance

The LLM provides strategic context every N steps, which is fed into the PPO
observation space to guide learning.

Training on REAL fire data:
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
sys.path.append(str(_BASE_DIR / 'agents'))

import numpy as np
import gymnasium as gym
from gymnasium import spaces
import argparse
from typing import Dict, List, Optional
import json
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
from agents.hybrid_ppo_llm_agent import HybridPPOLLMAgent


class HybridRealFireEnv(gym.Env):
    """AURORA Environment using REAL fire perimeter data + LLM strategic guidance."""
    
    def __init__(self, 
                 grid_size: int = 50,
                 num_drones: int = 3,
                 max_steps: int = 100,
                 integrator: Optional[RealDataIntegrator] = None,
                 llm_model: str = "meta-llama/Llama-2-7b-chat-hf",
                 llm_guidance_freq: int = 10,
                 hf_token: Optional[str] = None,
                 llm_backend: str = 'transformers'):
        super().__init__()
        
        self.grid_size = grid_size
        self.num_drones = num_drones
        self.max_steps = max_steps
        self.current_step = 0
        
        # Real data integrator
        self.integrator = integrator
        
        # Hybrid LLM agent
        self.hybrid_agent = HybridPPOLLMAgent(
            llm_model=llm_model,
            llm_guidance_frequency=llm_guidance_freq,
            hf_token=hf_token,
            llm_backend=llm_backend
        )
        
        # Observation space: 3x3 grid around drone with 9 channels
        # Original 6 channels + 3 strategic channels from LLM:
        # [fire_intensity, terrain_type, elevation, fuel_density, battery, water,
        #  priority_weight, strategic_direction_x, strategic_direction_y]
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(3, 3, 9), dtype=np.float32
        )
        
        # Action space: 8 actions
        # 0: stay, 1-4: move (up/down/left/right), 5: suppress, 6: scan, 7: communicate
        self.action_space = spaces.Discrete(8)
        
        # Initialize environment components
        self.fire_sim = None
        self.drones = []
        self.current_scenario = None
        self.current_strategy = None
        
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
                self.fire_sim = FireSim(
                    grid_size=self.grid_size
                )
                
                # Set fire grid from real perimeter
                self.fire_sim.fire_state = self.current_scenario['initial_fire_grid'].astype(np.uint8)
                
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
                self.fire_sim.fuel_density = (0.7 + terrain['slope'] * 0.3).astype(np.float32)
                
            except Exception as e:
                print(f"⚠️  Error loading real scenario: {e}")
                self._reset_simple()
        else:
            self._reset_simple()
        
        # Initialize drones at random positions
        self.drones = []
        for i in range(self.num_drones):
            x = np.random.randint(0, self.grid_size)
            y = np.random.randint(0, self.grid_size)
            drone = DroneAgent(start_pos=(x, y), agent_id=f"drone_{i}")
            self.drones.append(drone)
        
        self.current_step = 0
        
        # Get initial strategic guidance
        self._update_strategy()
        
        # Return observation for first drone
        obs = self._get_observation(0)
        return obs, {}
    
    def _reset_simple(self):
        """Fallback simple reset if real data fails."""
        self.fire_sim = FireSim(grid_size=self.grid_size)
        self.current_scenario = {
            'fire_name': 'Synthetic', 
            'year': 2024,
            'weather': {
                'temperature_f': 75,
                'wind_speed_mph': 10,
                'wind_direction': 'N',
                'humidity': 40
            }
        }
    
    def _update_strategy(self):
        """Get strategic guidance from LLM."""
        if self.hybrid_agent.should_request_guidance(self.current_step):
            # Prepare drone states
            drone_positions = [tuple(d.position) for d in self.drones]
            drone_states = [d.get_status() for d in self.drones]
            
            # Get weather
            weather = self.current_scenario.get('weather', {})
            
            # Request strategic guidance
            self.current_strategy = self.hybrid_agent.get_strategic_guidance(
                fire_state=self.fire_sim.fire_state,
                drone_positions=drone_positions,
                drone_states=drone_states,
                weather=weather,
                step=self.current_step
            )
    
    def step(self, action):
        """Execute action in environment."""
        
        # Update strategy if needed
        self._update_strategy()
        
        # Execute action for first drone
        drone = self.drones[0]
        action_result = drone.act(action, self.fire_sim, self.drones)
        
        # Step fire simulation
        self.fire_sim.step()
        self.current_step += 1
        
        # Calculate reward (enhanced with strategic alignment)
        reward = self._calculate_reward()
        
        # Check termination
        terminated = self.current_step >= self.max_steps
        truncated = drone.battery <= 0
        
        # Get observation
        obs = self._get_observation(0)
        
        return obs, reward, terminated, truncated, {}
    
    def _get_observation(self, drone_id: int) -> np.ndarray:
        """Get observation for a drone (3x3 grid with strategic overlay)."""
        
        drone = self.drones[drone_id]
        x, y = drone.position
        
        obs = np.zeros((3, 3, 9), dtype=np.float32)
        
        for i in range(-1, 2):
            for j in range(-1, 2):
                nx, ny = x + i, y + j
                
                # Clip to grid bounds
                nx = max(0, min(self.grid_size - 1, nx))
                ny = max(0, min(self.grid_size - 1, ny))
                
                # Original channels (0-5)
                obs[i+1, j+1, 0] = 1.0 if self.fire_sim.fire_state[ny, nx] == 1 else 0.0
                obs[i+1, j+1, 1] = self.fire_sim.terrain[ny, nx] / 3.0
                obs[i+1, j+1, 2] = self.fire_sim.elevation[ny, nx] / 100.0
                obs[i+1, j+1, 3] = self.fire_sim.fuel_density[ny, nx]
                obs[i+1, j+1, 4] = drone.battery
                obs[i+1, j+1, 5] = drone.water
                
                # Strategic channels (6-8) from LLM guidance
                if self.current_strategy:
                    # Channel 6: Priority weight (distance to nearest priority zone)
                    priority_zones = self.current_strategy.get('priority_zones', [])
                    if priority_zones:
                        distances = [abs(ny - z[0]) + abs(nx - z[1]) for z in priority_zones]
                        min_dist = min(distances)
                        # Closer to priority zone = higher weight
                        obs[i+1, j+1, 6] = max(0, 1.0 - min_dist / self.grid_size)
                    
                    # Channels 7-8: Strategic direction vector to assigned zone
                    assignments = self.current_strategy.get('drone_assignments', {})
                    drone_key = f"drone_{drone_id}"
                    if drone_key in assignments and priority_zones:
                        zone_idx = assignments[drone_key]
                        if zone_idx < len(priority_zones):
                            target = priority_zones[zone_idx]
                            # Normalized direction vector
                            dx = (target[1] - x) / self.grid_size
                            dy = (target[0] - y) / self.grid_size
                            obs[i+1, j+1, 7] = dx
                            obs[i+1, j+1, 8] = dy
        
        return obs
    
    def _calculate_reward(self) -> float:
        """Calculate reward with strategic alignment bonus."""
        
        # Base fire suppression reward
        burning_cells = np.sum(self.fire_sim.fire_state == 1)
        total_cells = self.grid_size * self.grid_size
        fire_coverage = burning_cells / total_cells
        
        fire_reward = -fire_coverage * 10.0
        
        # Suppression reward
        total_suppression = sum(d.suppression_count for d in self.drones)
        suppression_reward = total_suppression * 2.0
        
        # Battery efficiency
        avg_battery = sum(d.battery for d in self.drones) / len(self.drones)
        battery_penalty = -1.0 if avg_battery < 0.2 else 0.0
        
        # Strategic alignment bonus
        strategic_bonus = 0.0
        if self.current_strategy:
            priority_zones = self.current_strategy.get('priority_zones', [])
            if priority_zones:
                # Reward drones near priority zones
                for drone in self.drones:
                    distances = [abs(drone.position[0] - z[0]) + abs(drone.position[1] - z[1]) 
                               for z in priority_zones]
                    min_dist = min(distances)
                    # Closer = better (max bonus 1.0 per drone)
                    strategic_bonus += max(0, 1.0 - min_dist / (self.grid_size / 2))
        
        # Total reward
        reward = fire_reward + suppression_reward + battery_penalty + strategic_bonus
        
        return reward


class TrainingCallback(BaseCallback):
    """Custom callback with LLM statistics tracking."""
    
    def __init__(self, check_freq: int = 1000, total_timesteps: int = 50000, 
                 hybrid_agent: Optional[HybridPPOLLMAgent] = None, verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.total_timesteps = total_timesteps
        self.hybrid_agent = hybrid_agent
        self.episode_rewards = []
        self.episode_lengths = []
        self.start_time = None
        
    def _on_training_start(self) -> None:
        self.start_time = datetime.now()
        print(f"\n🚀 Hybrid PPO + LLM Training started at {self.start_time.strftime('%H:%M:%S')}")
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
            
            # LLM statistics
            if self.hybrid_agent:
                stats = self.hybrid_agent.get_statistics()
                print(f"   🧠 LLM calls: {stats['llm_calls']}, "
                      f"Tokens: {stats['llm_tokens_used']}, "
                      f"Errors: {stats['llm_errors']}")
            
            print("-"*80)
        
        return True
    
    def _on_rollout_end(self) -> None:
        if len(self.model.ep_info_buffer) > 0:
            for ep_info in self.model.ep_info_buffer:
                if isinstance(ep_info, dict):
                    self.episode_rewards.append(ep_info.get('r', 0))
                    self.episode_lengths.append(ep_info.get('l', 0))


def make_env(rank: int, llm_model: str, llm_freq: int, hf_token: str, llm_backend: str = 'transformers'):
    """Create a single hybrid environment instance."""
    def _init():
        # Load integrator in each subprocess
        integrator = RealDataIntegrator()
        
        env = HybridRealFireEnv(
            grid_size=50,
            num_drones=3,
            max_steps=100,
            integrator=integrator,
            llm_model=llm_model,
            llm_guidance_freq=llm_freq,
            hf_token=hf_token,
            llm_backend=llm_backend
        )
        env = Monitor(env)
        return env
    return _init


def main():
    parser = argparse.ArgumentParser(description='Train Hybrid PPO + Llama-2 on real fire data - ISEF 2025')
    
    # === PHASE SELECTION (ISEF-optimized) ===
    parser.add_argument('--phase', type=str, default='full', 
                       choices=['phase_a', 'phase_b', 'phase_c', 'phase_d', 'full', 'quick'],
                       help='Training phase: phase_a (2M), phase_b (4M), phase_c (5M), phase_d (2M), full (13M), or quick (500K test)')
    
    # === MANUAL OVERRIDE (if not using phases) ===
    parser.add_argument('--timesteps', type=int, default=None, 
                       help='Total training timesteps (overrides phase setting)')
    
    # === ENVIRONMENT SETTINGS ===
    parser.add_argument('--n_envs', type=int, default=4, 
                       help='Number of parallel environments (4 recommended, 8192 steps/update)')
    
    # === LLM SETTINGS ===
    parser.add_argument('--llm_model', type=str, default='Qwen/Qwen2.5-7B-Instruct',
                       help='HuggingFace LLM model ID (Qwen recommended for ISEF)')
    parser.add_argument('--llm_freq', type=int, default=50,
                       help='Steps between LLM guidance (50 recommended, 75 if too frequent)')
    parser.add_argument('--hf_token', type=str, default=None,
                       help='HuggingFace API token (or set HF_TOKEN env var)')
    parser.add_argument('--llm_backend', type=str, default='transformers',
                       help='LLM backend to use: transformers or gemini')
    
    # === CHECKPOINTING & EVALUATION ===
    parser.add_argument('--save_freq', type=int, default=40960,
                       help='Save model every N steps (default: every 5 updates = 40960 steps)')
    parser.add_argument('--eval_freq', type=int, default=81920,
                       help='Eval every N steps (default: every 10 updates = 81920 steps)')
    
    # === OTHER ===
    parser.add_argument('--verbose', type=int, default=1,
                       help='Verbosity level')
    
    args = parser.parse_args()
    
    # === PHASE CONFIGURATION ===
    phase_configs = {
        'phase_a': {'steps': 2_048_000, 'name': 'Phase A: Sanity & Overfit'},
        'phase_b': {'steps': 4_096_000, 'name': 'Phase B: Curriculum'},
        'phase_c': {'steps': 4_915_200, 'name': 'Phase C: Full Dataset'},
        'phase_d': {'steps': 2_048_000, 'name': 'Phase D: Qwen Fine-tune'},
        'full': {'steps': 13_120_000, 'name': 'Full Training (All Phases)'},
        'quick': {'steps': 500_000, 'name': 'Quick Test (500K)'}
    }
    
    # Determine timesteps
    if args.timesteps:
        total_timesteps = args.timesteps
        phase_name = f'Custom ({args.timesteps:,} steps)'
    else:
        config = phase_configs[args.phase]
        total_timesteps = config['steps']
        phase_name = config['name']
    
    args.timesteps = total_timesteps
    
    # Get HF token from args or env
    hf_token = args.hf_token or os.getenv("HF_TOKEN")
    if not hf_token:
        print("⚠️  WARNING: No HuggingFace token provided!")
        print("   Set HF_TOKEN environment variable or use --hf_token argument")
        print("   Without token, will use heuristic fallback instead of Qwen")
        print()
    
    print("\n" + "="*80)
    print("🔥 AURORA ISEF 2025 - HYBRID PPO + QWEN TRAINING")
    print("="*80)
    print(f"Phase: {phase_name}")
    print(f"Total timesteps: {args.timesteps:,}")
    print(f"Updates planned: {args.timesteps // (2048 * args.n_envs)}")
    print(f"Steps per update: {2048 * args.n_envs:,} (n_steps=2048 × n_envs={args.n_envs})")
    print(f"Estimated wall time: {(args.timesteps / 200_000):.1f} - {(args.timesteps / 150_000):.1f} hours")
    print(f"\nEnvironments: {args.n_envs} parallel")
    print(f"LLM model: {args.llm_model}")
    print(f"LLM guidance frequency: every {args.llm_freq} steps")
    print(f"HF token: {'✅ Provided' if hf_token else '❌ Missing (will use heuristic)'}")
    print(f"LLM backend: {args.llm_backend}")
    print(f"\nCheckpointing:")
    print(f"  Save frequency: every {args.save_freq // (2048 * args.n_envs)} updates ({args.save_freq:,} steps)")
    print(f"  Eval frequency: every {args.eval_freq // (2048 * args.n_envs)} updates ({args.eval_freq:,} steps)")
    print("\n📊 Real Fire Data: 116,337 fires from InterAgency Fire Perimeter History")
    print("="*80 + "\n")
    
    # Create vectorized environments
    print(f"Creating {args.n_envs} parallel hybrid environments...")
    print("(Each environment has Llama-2 strategic guidance)")
    print("NOTE: This may take a few minutes to load Llama-2 model...")
    
    if args.n_envs > 1:
        env = SubprocVecEnv([make_env(i, args.llm_model, args.llm_freq, hf_token, args.llm_backend) 
                            for i in range(args.n_envs)])
    else:
        env = DummyVecEnv([make_env(0, args.llm_model, args.llm_freq, hf_token, args.llm_backend)])
    
    print("✅ Environments created\n")
    
    # Create PPO model (larger network for richer observations)
    print("Initializing Hybrid PPO model...")
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
        policy_kwargs=dict(net_arch=[256, 256, 128]),  # Larger network for hybrid
        tensorboard_log=None
    )
    
    print("✅ Model initialized\n")
    
    # Create callback
    # Note: hybrid_agent will be accessed through env, stats collected separately
    callback = TrainingCallback(
        check_freq=2000, 
        total_timesteps=args.timesteps, 
        verbose=1
    )
    
    # Train
    print("="*80)
    print("STARTING HYBRID TRAINING")
    print("="*80 + "\n")
    
    start_time = datetime.now()
    
    try:
        model.learn(
            total_timesteps=args.timesteps,
            callback=callback,
            progress_bar=False
        )
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "="*80)
        print("✅ TRAINING COMPLETE")
        print("="*80)
        print(f"Training time: {training_time/60:.1f} minutes")
        print(f"Timesteps: {args.timesteps:,}")
        print(f"Timesteps/sec: {args.timesteps/training_time:.0f}")
        print("="*80 + "\n")
        
        # Save final model
        results_dir = _BASE_DIR / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)
        
        save_base = results_dir / 'aurora_hybrid_ppo_llm_model'
        model.save(str(save_base))
        
        zip_path = save_base.with_suffix('.zip')
        extract_dir = save_base
        try:
            if zip_path.exists():
                shutil.unpack_archive(str(zip_path), extract_dir=str(extract_dir))
                zip_path.unlink()
                print(f"💾 Hybrid model saved to {extract_dir.resolve()} (unzipped files)")
            else:
                print(f"💾 Hybrid model saved at {save_base.resolve()}")
        except Exception as e:
            print(f"⚠️  Warning: failed to unpack model zip: {e}")
        
        # Save training summary
        summary = {
            'model_type': 'hybrid_ppo_llm',
            'total_timesteps': args.timesteps,
            'n_envs': args.n_envs,
            'llm_model': args.llm_model,
            'llm_guidance_frequency': args.llm_freq,
            'training_time_minutes': training_time / 60,
            'fire_records_available': 116337,
            'data_source': 'InterAgency Fire Perimeter History (1308-2024)',
            'weather_source': 'NOAA National Weather Service API',
            'date': datetime.now().isoformat()
        }
        
        summary_path = results_dir / 'hybrid_training_summary.json'
        with open(str(summary_path), 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📊 Training summary saved to {summary_path.resolve()}\n")
        
    except KeyboardInterrupt:
        print("\n⚠️  Training interrupted by user")
        print("Saving current model...")
        results_dir = _BASE_DIR / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)
        interrupted_base = results_dir / 'aurora_hybrid_ppo_llm_model_interrupted'
        model.save(str(interrupted_base))
        interrupted_zip = interrupted_base.with_suffix('.zip')
        try:
            if interrupted_zip.exists():
                shutil.unpack_archive(str(interrupted_zip), extract_dir=str(interrupted_base))
                interrupted_zip.unlink()
                print(f"💾 Interrupted model saved to {interrupted_base.resolve()} (unzipped files)\n")
            else:
                print(f"💾 Interrupted model saved at {interrupted_base.resolve()}\n")
        except Exception as e:
            print(f"⚠️  Warning: failed to unpack interrupted model zip: {e}\n")
    
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        env.close()
        print("Environment closed")


if __name__ == "__main__":
    main()
