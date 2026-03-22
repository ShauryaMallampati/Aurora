"""
AURORA: Hybrid PPO + LLM training.

PPO handles low-level control; the LLM adds high-level strategy.
Real data only. If it isn't real, we don't use it.
"""

import sys
import os
from pathlib import Path as _Path

# Add data/agents to sys.path so imports don't break
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

# Stable-Baselines3 imports
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

# AURORA modules
from env.fire_sim import FireSim
from agents.drone_agent import DroneAgent
from data.real_data_integration_complete import RealDataIntegrator
from agents.hybrid_ppo_llm_agent import HybridPPOLLMAgent


class HybridRealFireEnv(gym.Env):
    """
    The main gym environment. 
    It loads real fire data, simulates the burn, and lets the drones fight it.
    """
    
    def __init__(self, 
                 grid_size: int = 50,
                 num_drones: int = 3,
                 max_steps: int = 100,
                 integrator: Optional[RealDataIntegrator] = None,
                 llm_model: str = "Qwen/Qwen2.5-1.5B-Instruct",
                 llm_guidance_freq: int = 10,
                 hf_token: Optional[str] = None,
                 llm_backend: str = 'transformers'):
        super().__init__()
        self.grid_size = grid_size
        self.num_drones = num_drones
        self.max_steps = max_steps
        self.current_step = 0
        self.integrator = integrator
        
        # If LLM is off, stick to PPO
        if (llm_guidance_freq is not None and llm_guidance_freq >= 999999) or not llm_model or llm_model.lower() == 'none':
            self.hybrid_agent = None
        else:
            self.hybrid_agent = HybridPPOLLMAgent(
                llm_model=llm_model,
                llm_guidance_frequency=llm_guidance_freq,
                hf_token=hf_token,
                llm_backend=llm_backend
            )
        
        # 9 channels in [0, 1]: 6 world + 3 strategy
        # [fire, terrain, elev, fuel, batt, water, weight, x, y]
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(3, 3, 9), dtype=np.float32
        )
        
        # Action space: 8 actions
        # 0: stay, 1-4: move (up/down/left/right), 5: suppress, 6: scan, 7: communicate
        self.action_space = spaces.Discrete(8)
        
        # Env state
        self.fire_sim = None
        self.drones = []
        self.current_scenario = None
        self.current_strategy = None
        
    def reset(self, seed=None, options=None):
        """Reset environment with a new real fire scenario."""
        super().reset(seed=seed)
        
        # Pull a new real-fire scenario
        if self.integrator:
            for attempt in range(5):
                try:
                    self.current_scenario = self.integrator.create_training_scenario(
                        min_year=2010,
                        min_acres=100,
                        max_acres=50000
                    )

                    # Start fire sim with real data
                    initial_fire = self.current_scenario['initial_fire_grid'].astype(np.uint8)

                    self.fire_sim = FireSim(grid_size=self.grid_size)

                    # Reset using the real fire grid
                    self.fire_sim.reset(initial_fire_grid=initial_fire)

                    # Set NOAA weather
                    weather = self.current_scenario['weather']
                    wind_dirs = {'N': (0, -1), 'NE': (1, -1), 'E': (1, 0), 'SE': (1, 1),
                               'S': (0, 1), 'SW': (-1, 1), 'W': (-1, 0), 'NW': (-1, -1)}
                    wind_dir = wind_dirs.get(weather['wind_direction'], (0, 0))
                    wind_speed = weather['wind_speed_mph'] / 25.0  # normalize

                    self.fire_sim.set_wind(wind_dir, wind_speed)
                    self.fire_sim.set_weather(
                        humidity=weather['humidity'] / 100.0,
                        temperature=weather['temperature_c']
                    )

                    # Apply real terrain
                    terrain = self.current_scenario['terrain']
                    self.fire_sim.elevation = (terrain['elevation'] / 3000.0).astype(np.float32)
                    self.fire_sim.fuel_density = (0.7 + terrain['slope'] * 0.3).astype(np.float32)

                    # Make sure rasters align
                    expected_shape = (self.grid_size, self.grid_size)
                    assert self.fire_sim.fire_state.shape == expected_shape, f"Fire grid shape mismatch: {self.fire_sim.fire_state.shape} != {expected_shape}"
                    assert self.fire_sim.elevation.shape == expected_shape, f"Elevation shape mismatch: {self.fire_sim.elevation.shape} != {expected_shape}"
                    assert self.fire_sim.fuel_density.shape == expected_shape, f"Fuel density shape mismatch: {self.fire_sim.fuel_density.shape} != {expected_shape}"
                    break
                except Exception as e:
                    print(f"Warning: error loading real scenario (attempt {attempt + 1}/5): {e}")
                    if attempt == 4:
                        raise RuntimeError("Failed to load a real scenario after 5 attempts") from e
                    print("   Retrying with another random real scenario...")
        else:
            raise RuntimeError("No real data integrator provided - cannot proceed without real data")
        
        # Spawn drones at random positions
        self.drones = []
        for i in range(self.num_drones):
            x = np.random.randint(0, self.grid_size)
            y = np.random.randint(0, self.grid_size)
            drone = DroneAgent(start_pos=(x, y), agent_id=f"drone_{i}")
            self.drones.append(drone)
        
        self.current_step = 0
        
        # Get initial strategy snapshot
        self._update_strategy()
        
        # Return obs for first drone
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
        """Get strategic guidance from LLM (or skip if LLM disabled)."""
        if self.hybrid_agent is None:
            # LLM off for pure PPO baseline
            self.current_strategy = None
            return
        
        if self.hybrid_agent.should_request_guidance(self.current_step):
            # Prep drone state
            drone_positions = [tuple(d.position) for d in self.drones]
            drone_states = [d.get_status() for d in self.drones]
            
            # Grab weather
            weather = self.current_scenario.get('weather', {})
            
            # Request guidance
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
        
        # Apply action for first drone
        drone = self.drones[0]
        action_result = drone.act(action, self.fire_sim, self.drones)
        
        # Step fire sim
        self.fire_sim.step()
        self.current_step += 1
        
        # Compute reward (incl. strategy alignment)
        reward = self._calculate_reward()
        
        # Check terminal condition
        terminated = self.current_step >= self.max_steps
        truncated = drone.battery <= 0
        
        # Build observation
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
                
                # Base channels (0-5)
                obs[i+1, j+1, 0] = 1.0 if self.fire_sim.fire_state[ny, nx] == 1 else 0.0
                obs[i+1, j+1, 1] = self.fire_sim.terrain[ny, nx] / 3.0
                obs[i+1, j+1, 2] = self.fire_sim.elevation[ny, nx] / 100.0
                obs[i+1, j+1, 3] = self.fire_sim.fuel_density[ny, nx]
                obs[i+1, j+1, 4] = np.clip(drone.battery / max(1e-6, drone.max_battery), 0.0, 1.0)
                obs[i+1, j+1, 5] = np.clip(drone.water / max(1e-6, drone.max_water), 0.0, 1.0)
                
                # Strategy channels (6-8) from LLM guidance
                if self.current_strategy:
                    # Channel 6: priority weight (dist to nearest zone)
                    priority_zones = self.current_strategy.get('priority_zones', [])
                    if priority_zones:
                        distances = [abs(ny - z[0]) + abs(nx - z[1]) for z in priority_zones]
                        min_dist = min(distances)
                        # Closer to priority zone = higher weight
                        obs[i+1, j+1, 6] = max(0, 1.0 - min_dist / self.grid_size)
                    
                    # Channels 7-8: direction vector to assigned zone
                    assignments = self.current_strategy.get('drone_assignments', {})
                    drone_key = f"drone_{drone_id}"
                    if drone_key in assignments and priority_zones:
                        zone_idx = assignments[drone_key]
                        if zone_idx < len(priority_zones):
                            target = priority_zones[zone_idx]
                            # Normalized direction vector
                            dx = (target[1] - x) / self.grid_size
                            dy = (target[0] - y) / self.grid_size
                            obs[i+1, j+1, 7] = np.clip((dx + 1.0) * 0.5, 0.0, 1.0)
                            obs[i+1, j+1, 8] = np.clip((dy + 1.0) * 0.5, 0.0, 1.0)

        np.clip(obs, 0.0, 1.0, out=obs)
        return obs
    
    def _calculate_reward(self) -> float:
        """Calculate reward with strategic alignment bonus."""
        
        # Base suppression reward
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
        
        # Strategy alignment bonus
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
    """Custom callback with real-time progress, checkpointing, and LLM statistics."""
    
    def __init__(self, check_freq: int = 100, save_freq: int = 500, 
                 total_timesteps: int = 50000, 
                 hybrid_agent: Optional[HybridPPOLLMAgent] = None, 
                 save_path: str = "./results/checkpoints/",
                 verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq  # print progress every 100 steps
        self.save_freq = save_freq    # save checkpoint every 500 steps
        self.total_timesteps = total_timesteps
        self.hybrid_agent = hybrid_agent
        self.save_path = _Path(save_path)
        self.save_path.mkdir(parents=True, exist_ok=True)
        self.episode_rewards = []
        self.episode_lengths = []
        self.start_time = None
        self.last_save_step = 0
        
    def _on_training_start(self) -> None:
        self.start_time = datetime.now()
        print(f"\n🚀 Hybrid PPO + Qwen Training started at {self.start_time.strftime('%H:%M:%S')}")
        print(f"Checkpoints will be saved every {self.save_freq} steps to: {self.save_path}")
        print("="*80)
        
    def _on_step(self) -> bool:
        
        # Real-time progress updates (every check_freq steps)
        if self.n_calls % self.check_freq == 0:
            # Compute progress
            progress = (self.n_calls / self.total_timesteps) * 100
            elapsed = datetime.now() - self.start_time
            steps_per_sec = self.n_calls / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
            remaining_steps = self.total_timesteps - self.n_calls
            eta_seconds = remaining_steps / steps_per_sec if steps_per_sec > 0 else 0
            eta = str(timedelta(seconds=int(eta_seconds)))
            
            # Console tick (same line)
            print(f"\r� STEP {self.n_calls:,}/{self.total_timesteps:,} ({progress:.1f}%) | "
                  f"{steps_per_sec:.0f} steps/sec | ETA: {eta}", end='', flush=True)
            
            # Detailed log every 1000 steps
            if self.n_calls % 1000 == 0:
                print()  # new line for detailed log
                if len(self.episode_rewards) > 0:
                    mean_reward = np.mean(self.episode_rewards[-10:])
                    mean_length = np.mean(self.episode_lengths[-10:])
                    print(f"   Mean reward (last 10 ep): {mean_reward:.2f}")
                    print(f"   Mean episode length: {mean_length:.1f}")
                
                # LLM stats
                if self.hybrid_agent:
                    stats = self.hybrid_agent.get_statistics()
                    print(f"   LLM calls: {stats['llm_calls']}, "
                          f"Tokens: {stats['llm_tokens_used']}, "
                          f"Errors: {stats['llm_errors']}")
                print("-"*80)
        
        # Checkpoint every save_freq steps
        if self.n_calls > 0 and self.n_calls % self.save_freq == 0 and self.n_calls != self.last_save_step:
            self.last_save_step = self.n_calls
            checkpoint_path = self.save_path / f"checkpoint_step_{self.n_calls}"
            self.model.save(str(checkpoint_path))
            print(f"\nCheckpoint saved at step {self.n_calls:,} -> {checkpoint_path}")
        
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
        # Load integrator per subprocess
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
    parser = argparse.ArgumentParser(description='Train hybrid PPO with optional LLM guidance on real fire data')
    
    # Phase config
    parser.add_argument('--phase', type=str, default='full', 
                       choices=['phase_a', 'phase_b', 'phase_c', 'full', 'quick', 'test'],
                       help='Training phase: phase_a (50K), phase_b (150K), phase_c (200K), full (400K), quick (50K), or test (10K debug)')
    
    # Manual timestep override
    parser.add_argument('--timesteps', type=int, default=None, 
                       help='Total training timesteps (overrides phase setting)')
    
    # Env settings
    parser.add_argument('--n_envs', type=int, default=2, 
                       help='Number of parallel environments (2 recommended, 4096 steps/update)')
    
    # LLM settings
    parser.add_argument('--llm_model', type=str, default='Qwen/Qwen2.5-1.5B-Instruct',
                       help='HuggingFace LLM model ID')
    parser.add_argument('--llm_freq', type=int, default=500,
                       help='Steps between LLM guidance (500 recommended for speed, lower for more guidance)')
    parser.add_argument('--hf_token', type=str, default=None,
                       help='HuggingFace API token (or set HF_TOKEN env var)')
    parser.add_argument('--llm_backend', type=str, default='transformers',
                       help='LLM backend to use: transformers (preferred)')
    
    # Checkpointing + eval
    parser.add_argument('--save_freq', type=int, default=40960,
                       help='Save model every N steps (default: every 5 updates = 40960 steps)')
    parser.add_argument('--eval_freq', type=int, default=81920,
                       help='Eval every N steps (default: every 10 updates = 81920 steps)')
    parser.add_argument('--progress_freq', type=int, default=100,
                       help='How often (in steps) to print progress updates to console (default 100 for reduced IO)')
    parser.add_argument('--resume', action='store_true', default=False,
                       help='Auto-resume from latest checkpoint without prompting (y)')
    
    # Misc options
    parser.add_argument('--verbose', type=int, default=1,
                       help='Verbosity level')

    # Experimental flags
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility (optional)')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Output directory for model and logs (optional)')
    
    args = parser.parse_args()
    
    # Load phase config
    phase_configs = {
        'phase_a': {'steps': 57_344, 'name': 'Phase A: Sanity & Overfit (~50K)'},
        'phase_b': {'steps': 147_456, 'name': 'Phase B: Curriculum (~150K)'},
        'phase_c': {'steps': 196_608, 'name': 'Phase C: Full Dataset (~200K)'},
        'full': {'steps': 401_408, 'name': 'Full Training (All 3 Phases ~400K)'},
        'quick': {'steps': 50_000, 'name': 'Quick Test (50K)'},
        'test': {'steps': 10_000, 'name': 'Debug Test (10K)'}
    }

    # Set random seed
    if args.seed is not None:
        import random
        import torch
        np.random.seed(args.seed)
        random.seed(args.seed)
        torch.manual_seed(args.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(args.seed)
    
    # Compute total timesteps
    if args.timesteps:
        total_timesteps = args.timesteps
        phase_name = f'Custom ({args.timesteps:,} steps)'
    else:
        config = phase_configs[args.phase]
        total_timesteps = config['steps']
        phase_name = config['name']
    
    args.timesteps = total_timesteps
    
    # Get HuggingFace token
    hf_token = args.hf_token or os.getenv("HF_TOKEN")
    if not hf_token:
        print("Warning: no HuggingFace token provided.")
        print("   Set HF_TOKEN environment variable or use --hf_token argument")
        print("   Without token, will use heuristic fallback instead of Qwen")
        print()
    
    print("\n" + "="*80)
    print("AURORA HYBRID PPO TRAINING")
    print("="*80)
    print(f"Phase: {phase_name}")
    print(f"Total timesteps: {args.timesteps:,}")
    print(f"Updates planned: {args.timesteps // (2048 * args.n_envs)}")
    print(f"Steps per update: {2048 * args.n_envs:,} (n_steps=2048 x n_envs={args.n_envs})")
    print(f"Estimated wall time: {(args.timesteps / 200_000):.1f} - {(args.timesteps / 150_000):.1f} hours")
    print(f"\nEnvironments: {args.n_envs} parallel")
    print(f"LLM model: {args.llm_model}")
    print(f"LLM guidance frequency: every {args.llm_freq} steps")
    print(f"HF token: {'provided' if hf_token else 'missing (will use heuristic)'}")
    print(f"LLM backend: {args.llm_backend}")
    print(f"\nCheckpointing:")
    print(f"  Save frequency: every {args.save_freq // (2048 * args.n_envs)} updates ({args.save_freq:,} steps)")
    print(f"  Eval frequency: every {args.eval_freq // (2048 * args.n_envs)} updates ({args.eval_freq:,} steps)")
    print("\nReal fire data: 116,337 fires from InterAgency Fire Perimeter History")
    print("="*80 + "\n")
    
    # Set up parallel envs
    print(f"Creating {args.n_envs} parallel hybrid environments...")
    print(f"(Each environment will use {args.llm_model} for strategic guidance)")
    
    # Avoid tokenizer fork warnings
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    # Use main process for LLM
    worker_backend = args.llm_backend
    if args.n_envs > 1 and args.llm_backend == 'transformers':
        # Use a transformers/heuristic mix to avoid loading heavy models per worker
        print(f"Using transformers/heuristic mix for {args.n_envs} workers")
        env = SubprocVecEnv([make_env(i, args.llm_model, args.llm_freq, hf_token, worker_backend) 
                            for i in range(args.n_envs)])
    else:
        print(f"NOTE: Using {args.llm_backend} backend with single environment")
        env = DummyVecEnv([make_env(0, args.llm_model, args.llm_freq, hf_token, args.llm_backend)])
    
    print("Environments created\n")
    
    # Check for existing checkpoints
    checkpoint_dir = _Path("./results/checkpoints/")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Find latest checkpoint
    checkpoints = list(checkpoint_dir.glob("checkpoint_step_*.zip"))
    
    # Sort by step number
    def get_step_num(cp):
        try:
            return int(cp.stem.split("_")[-1])
        except:
            return 0
    
    checkpoints = sorted(checkpoints, key=get_step_num)
    latest_checkpoint = None
    resume_step = 0
    
    if checkpoints:
        latest_checkpoint = checkpoints[-1]
        # Extract step number from checkpoint name (strip .zip)
        try:
            # checkpoint_step_204800.zip -> 204800
            step_str = latest_checkpoint.stem.split("_")[-1]
            resume_step = int(step_str)
            print(f"Found checkpoint at step {resume_step:,}: {latest_checkpoint}")
            
            # Auto-resume if --resume is set, else ask
            if args.resume:
                user_input = 'y'
                print(f"   Auto-resuming (--resume flag set)")
            else:
                user_input = input(f"   Resume from step {resume_step:,}? (y/n): ").strip().lower()
            
            if user_input != 'y':
                latest_checkpoint = None
                resume_step = 0
                print("   Starting fresh training from step 0")
            else:
                print(f"   Resuming from step {resume_step:,}")
        except (ValueError, IndexError):
            print(f"Warning: could not parse checkpoint name: {latest_checkpoint}")
            latest_checkpoint = None
    
    # Set up PPO model
    if latest_checkpoint and resume_step > 0:
        print(f"Loading model from checkpoint: {latest_checkpoint}")
        model = PPO.load(str(latest_checkpoint), env=env)
        # Adjust timesteps for resumed runs
        remaining_timesteps = max(0, args.timesteps - resume_step)
        print(f"Model loaded - will train for {remaining_timesteps:,} more steps")
        print(f"   (Total target: {args.timesteps:,}, Already trained: {resume_step:,})\n")
        args.timesteps = remaining_timesteps
    else:
        print("Initializing new Hybrid PPO model...")
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
            policy_kwargs=dict(net_arch=[256, 256, 128]),  # larger net for hybrid
            tensorboard_log=None
        )
        print("Model initialized\n")
    
    # Set up training callback
    callback = TrainingCallback(
        check_freq=args.progress_freq,           # print progress every N steps
        save_freq=args.save_freq,                # save checkpoint every N steps
        total_timesteps=args.timesteps, 
        save_path="./results/checkpoints/",
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
        print("Training complete")
        print("="*80)
        print(f"Training time: {training_time/60:.1f} minutes")
        print(f"Timesteps: {args.timesteps:,}")
        print(f"Timesteps/sec: {args.timesteps/training_time:.0f}")
        print("="*80 + "\n")
        
        # Save final model
        if args.output_dir is not None:
            results_dir = _Path(args.output_dir)
            results_dir.mkdir(parents=True, exist_ok=True)
        else:
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
                print(f"Hybrid model saved to {extract_dir.resolve()} (unzipped files)")
            else:
                print(f"Hybrid model saved at {save_base.resolve()}")
        except Exception as e:
            print(f"Warning: failed to unpack model zip: {e}")

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

        print(f"Training summary saved to {summary_path.resolve()}\n")
        
    except KeyboardInterrupt:
        print("\nTraining interrupted by user")
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
                print(f"Interrupted model saved to {interrupted_base.resolve()} (unzipped files)\n")
            else:
                print(f"Interrupted model saved at {interrupted_base.resolve()}\n")
        except Exception as e:
            print(f"Warning: failed to unpack interrupted model zip: {e}\n")
    
    except Exception as e:
        print(f"\nTraining error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        env.close()
        print("Environment closed")


if __name__ == "__main__":
    from aurora_pipeline import cli_train

    cli_train(default_variant="ppo_only")
