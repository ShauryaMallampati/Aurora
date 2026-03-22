"""Shared experiment pipeline for AURORA training, evaluation, and ablations."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import gymnasium as gym
from gymnasium import spaces
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import safe_mean
from stable_baselines3.common.vec_env import DummyVecEnv

from agents.drone_agent import DroneAgent
from agents.hybrid_ppo_llm_agent import HybridPPOLLMAgent
from data.real_data_integration_complete import RealDataIntegrator
from env.fire_sim import FireSim
from evaluate import EVALUATION_FIRES


BASE_DIR = Path(__file__).parent.resolve()
RESULTS_ROOT = BASE_DIR / "results" / "ablation_study"
STUDY_CONFIG_PATH = BASE_DIR / "configs" / "ablation_study.yaml"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=json_default), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def get_git_commit_hash() -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def str2bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def slugify(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_").lower()


def set_global_seed(seed: int) -> None:
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_study_definition(config_path: Path = STUDY_CONFIG_PATH) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@dataclass
class ExperimentConfig:
    family: str
    variant_name: str
    run_name: str
    model_label: str
    seed: int
    total_timesteps: int
    n_envs: int
    grid_size: int
    num_drones: int
    max_steps: int
    guidance_interval: int
    llm_model: str
    llm_backend: str
    use_llm_guidance: bool
    use_heuristic_strategist: bool
    use_strategic_obs_channels: bool
    use_strategy_reward: bool
    output_dir: Path
    phase: str = "full"
    hf_token: Optional[str] = None
    require_llm: bool = False
    ppo: Dict[str, Any] = field(default_factory=dict)
    llm_decoding: Dict[str, Any] = field(default_factory=dict)
    reward_coefficients: Dict[str, float] = field(default_factory=dict)
    normalization_radius: int = 50
    eval_scenarios: List[Dict[str, Any]] = field(default_factory=list)
    eval_seeds: List[int] = field(default_factory=list)
    easy_seeds: List[int] = field(default_factory=list)
    hard_seeds: List[int] = field(default_factory=list)
    training_budget_note: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def checkpoints_dir(self) -> Path:
        return self.output_dir / "checkpoints"

    @property
    def model_dir(self) -> Path:
        return self.output_dir / "model"

    @property
    def model_zip_path(self) -> Path:
        return self.output_dir / f"{self.model_label}.zip"

    @property
    def manifest_path(self) -> Path:
        return self.output_dir / "run_manifest.json"

    @property
    def train_curve_path(self) -> Path:
        return self.output_dir / "training_curve.csv"

    @property
    def train_monitor_path(self) -> Path:
        return self.output_dir / "train_monitor.csv"

    @property
    def eval_csv_path(self) -> Path:
        return self.output_dir / "evaluation_metrics.csv"

    @property
    def eval_json_path(self) -> Path:
        return self.output_dir / "evaluation_summary.json"

    @property
    def training_summary_path(self) -> Path:
        return self.output_dir / "training_summary.json"

    @property
    def guidance_log_path(self) -> Path:
        return self.output_dir / "guidance_log.jsonl"

    def to_manifest_payload(self) -> Dict[str, Any]:
        return {
            "git_commit_hash": get_git_commit_hash(),
            "timestamp": now_iso(),
            "seed": self.seed,
            "variant_name": self.variant_name,
            "run_name": self.run_name,
            "model_label": self.model_label,
            "K": self.guidance_interval,
            "use_llm_guidance": self.use_llm_guidance,
            "use_heuristic_strategist": self.use_heuristic_strategist,
            "use_strategic_obs_channels": self.use_strategic_obs_channels,
            "use_strategy_reward": self.use_strategy_reward,
            "training_budget": {
                "total_timesteps": self.total_timesteps,
                "episodes": None,
                "phase": self.phase,
                "note": self.training_budget_note,
            },
            "evaluation_scenario_list": [scenario["name"] for scenario in self.eval_scenarios],
            "evaluation_seeds": self.eval_seeds,
            "easy_seeds": self.easy_seeds,
            "hard_seeds": self.hard_seeds,
            "llm_model": self.llm_model,
            "llm_backend": self.llm_backend,
            "model_path": str(self.model_zip_path),
            "metric_file_paths": {
                "training_curve": str(self.train_curve_path),
                "training_monitor": str(self.train_monitor_path),
                "evaluation_csv": str(self.eval_csv_path),
                "evaluation_summary": str(self.eval_json_path),
                "training_summary": str(self.training_summary_path),
                "guidance_log": str(self.guidance_log_path),
            },
            "output_dir": str(self.output_dir),
            "config": {
                "grid_size": self.grid_size,
                "num_drones": self.num_drones,
                "max_steps": self.max_steps,
                "n_envs": self.n_envs,
                "ppo": self.ppo,
                "llm_decoding": self.llm_decoding,
                "reward_coefficients": self.reward_coefficients,
                "normalization_radius": self.normalization_radius,
            },
            "metadata": self.metadata,
        }


def resolve_variant_definition(study: Dict[str, Any], variant_key: str) -> Dict[str, Any]:
    defaults = study["defaults"]
    if variant_key in study["variants"]:
        resolved = deep_merge(defaults, study["variants"][variant_key])
        resolved["variant_name"] = variant_key
        return resolved

    model_variants = study.get("model_variants", {})
    if variant_key in model_variants:
        model_variant = model_variants[variant_key]
        base_variant = model_variant["base_variant"]
        resolved = deep_merge(defaults, study["variants"][base_variant])
        resolved = deep_merge(resolved, model_variant)
        resolved["variant_name"] = variant_key
        return resolved

    raise KeyError(f"Unknown variant '{variant_key}' in {STUDY_CONFIG_PATH}")


def build_experiment_config(
    study: Dict[str, Any],
    family: str,
    variant_key: str,
    seed: int,
    output_dir: Path,
    run_name: Optional[str] = None,
    guidance_interval: Optional[int] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> ExperimentConfig:
    resolved = resolve_variant_definition(study, variant_key)
    if overrides:
        resolved = deep_merge(resolved, overrides)

    if guidance_interval is not None:
        resolved["guidance_interval"] = int(guidance_interval)

    hf_token = os.getenv("HF_TOKEN")
    variant_name = resolved["variant_name"]
    resolved_run_name = run_name or f"{variant_name}_seed_{seed}"

    return ExperimentConfig(
        family=family,
        variant_name=variant_name,
        run_name=resolved_run_name,
        model_label=resolved.get("model_label", variant_name),
        seed=int(seed),
        total_timesteps=int(resolved["total_timesteps"]),
        n_envs=int(resolved["n_envs"]),
        grid_size=int(resolved["grid_size"]),
        num_drones=int(resolved["num_drones"]),
        max_steps=int(resolved["max_steps"]),
        guidance_interval=int(resolved["guidance_interval"]),
        llm_model=str(resolved["llm_model"]),
        llm_backend=str(resolved["llm_backend"]),
        use_llm_guidance=bool(resolved["use_llm_guidance"]),
        use_heuristic_strategist=bool(resolved["use_heuristic_strategist"]),
        use_strategic_obs_channels=bool(resolved["use_strategic_obs_channels"]),
        use_strategy_reward=bool(resolved["use_strategy_reward"]),
        output_dir=output_dir.resolve(),
        phase=str(resolved.get("phase", "full")),
        hf_token=hf_token,
        require_llm=bool(resolved.get("use_llm_guidance", False)),
        ppo=resolved.get("ppo", {}),
        llm_decoding=resolved.get("llm_decoding", {}),
        reward_coefficients=resolved.get("reward_coefficients", {}),
        normalization_radius=int(resolved.get("normalization_radius", 50)),
        eval_scenarios=list(EVALUATION_FIRES),
        eval_seeds=list(resolved.get("seeds", study["defaults"]["seeds"])),
        easy_seeds=list(resolved.get("easy_seeds", study["defaults"]["easy_seeds"])),
        hard_seeds=list(resolved.get("hard_seeds", study["defaults"]["hard_seeds"])),
        training_budget_note=f"Matched to study default full budget of {resolved['total_timesteps']} timesteps",
        metadata={
            "evaluation_scenarios_source": resolved.get("evaluation_scenarios_source"),
            "evaluation_seed_note": resolved.get("evaluation_seed_note"),
        },
    )


class AuroraExperimentEnv(gym.Env):
    """Hybrid wildfire environment with ablation switches."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        config: ExperimentConfig,
        integrator: Optional[RealDataIntegrator] = None,
        scenario_spec: Optional[Dict[str, Any]] = None,
        evaluation_seed: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.config = config
        self.integrator = integrator or RealDataIntegrator(seed=config.seed)
        self.scenario_spec = scenario_spec
        self.base_seed = int(evaluation_seed if evaluation_seed is not None else config.seed)
        self.reset_count = 0
        self.grid_size = config.grid_size
        self.num_drones = config.num_drones
        self.max_steps = config.max_steps
        self.current_step = 0

        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(3, 3, 9), dtype=np.float32
        )
        self.action_space = spaces.Discrete(8)

        self.fire_sim: Optional[FireSim] = None
        self.drones: List[DroneAgent] = []
        self.current_scenario: Optional[Dict[str, Any]] = None
        self.current_strategy: Optional[Dict[str, Any]] = None
        self.episode_return = 0.0
        self.episode_water_used = 0.0
        self.episode_idle_steps = 0
        self.containment_step: Optional[int] = None
        self.last_action = 0

        self.hybrid_agent = self._build_hybrid_agent()

    def _build_hybrid_agent(self) -> Optional[HybridPPOLLMAgent]:
        if not self.config.use_llm_guidance and not self.config.use_heuristic_strategist:
            return None

        return HybridPPOLLMAgent(
            llm_model=self.config.llm_model if self.config.use_llm_guidance else "none",
            llm_guidance_frequency=self.config.guidance_interval,
            temperature=float(self.config.llm_decoding.get("temperature", 0.7)),
            hf_token=self.config.hf_token,
            llm_backend=self.config.llm_backend,
            force_heuristic=self.config.use_heuristic_strategist,
            require_model_loaded=self.config.require_llm and self.config.use_llm_guidance,
            guidance_log_path=str(self.config.guidance_log_path),
            max_new_tokens=int(self.config.llm_decoding.get("max_new_tokens", 256)),
            do_sample=bool(self.config.llm_decoding.get("do_sample", False)),
        )

    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None):
        super().reset(seed=seed)
        self.reset_count += 1
        episode_seed = int(seed if seed is not None else self.base_seed + self.reset_count - 1)
        rng = np.random.default_rng(episode_seed)

        if self.scenario_spec is not None:
            self.current_scenario = self.integrator.create_scenario_from_spec(
                self.scenario_spec,
                grid_size=self.grid_size,
                seed=episode_seed,
            )
        else:
            self.current_scenario = self.integrator.create_training_scenario(
                min_year=2010,
                min_acres=100,
                max_acres=50000,
            )

        initial_fire = self.current_scenario["initial_fire_grid"].astype(np.uint8)
        self.fire_sim = FireSim(grid_size=self.grid_size, seed=episode_seed)
        self.fire_sim.reset(initial_fire_grid=initial_fire)

        weather = self.current_scenario["weather"]
        wind_dirs = {
            "N": (0, -1),
            "NE": (1, -1),
            "E": (1, 0),
            "SE": (1, 1),
            "S": (0, 1),
            "SW": (-1, 1),
            "W": (-1, 0),
            "NW": (-1, -1),
        }
        wind_dir = wind_dirs.get(weather["wind_direction"], (0, 0))
        wind_speed = float(weather["wind_speed_mph"]) / 25.0
        self.fire_sim.set_wind(wind_dir, wind_speed)
        self.fire_sim.set_weather(
            humidity=float(weather["humidity"]) / 100.0,
            temperature=float(weather["temperature_c"]),
        )

        terrain = self.current_scenario["terrain"]
        self.fire_sim.elevation = (terrain["elevation"] / 3000.0).astype(np.float32)
        self.fire_sim.fuel_density = (0.7 + terrain["slope"] * 0.3).astype(np.float32)

        self.drones = []
        for index in range(self.num_drones):
            x = int(rng.integers(0, self.grid_size))
            y = int(rng.integers(0, self.grid_size))
            self.drones.append(DroneAgent(start_pos=(x, y), agent_id=f"drone_{index}"))

        self.current_step = 0
        self.episode_return = 0.0
        self.episode_water_used = 0.0
        self.episode_idle_steps = 0
        self.containment_step = None
        self.last_action = 0
        self.current_strategy = None

        if self.hybrid_agent is not None:
            self.hybrid_agent.reset_episode_state()
            self._update_strategy(force=True)

        return self._get_observation(0), {}

    def _update_strategy(self, force: bool = False) -> None:
        if self.hybrid_agent is None:
            self.current_strategy = None
            return

        should_query = force or self.hybrid_agent.should_request_guidance(self.current_step)
        if not should_query:
            return

        drone_positions = [tuple(drone.position) for drone in self.drones]
        drone_states = [drone.get_status() for drone in self.drones]
        self.current_strategy = self.hybrid_agent.get_strategic_guidance(
            fire_state=self.fire_sim.fire_state,
            drone_positions=drone_positions,
            drone_states=drone_states,
            weather=self.current_scenario.get("weather", {}),
            step=self.current_step,
        )

    def _get_observation(self, drone_id: int) -> np.ndarray:
        drone = self.drones[drone_id]
        x, y = drone.position
        obs = np.zeros((3, 3, 9), dtype=np.float32)

        for i in range(-1, 2):
            for j in range(-1, 2):
                nx = max(0, min(self.grid_size - 1, x + i))
                ny = max(0, min(self.grid_size - 1, y + j))

                obs[i + 1, j + 1, 0] = 1.0 if self.fire_sim.fire_state[ny, nx] == 1 else 0.0
                obs[i + 1, j + 1, 1] = self.fire_sim.terrain[ny, nx] / 3.0
                obs[i + 1, j + 1, 2] = self.fire_sim.elevation[ny, nx] / 100.0
                obs[i + 1, j + 1, 3] = self.fire_sim.fuel_density[ny, nx]
                obs[i + 1, j + 1, 4] = np.clip(
                    drone.battery / max(1e-6, drone.max_battery), 0.0, 1.0
                )
                obs[i + 1, j + 1, 5] = np.clip(
                    drone.water / max(1e-6, drone.max_water), 0.0, 1.0
                )

                if self.config.use_strategic_obs_channels and self.current_strategy:
                    priority_zones = self.current_strategy.get("priority_zones", [])
                    if priority_zones:
                        distances = [abs(ny - zone[0]) + abs(nx - zone[1]) for zone in priority_zones]
                        min_dist = min(distances)
                        obs[i + 1, j + 1, 6] = max(
                            0.0,
                            1.0 - min_dist / max(1, self.config.normalization_radius),
                        )

                    assignments = self.current_strategy.get("drone_assignments", {})
                    drone_key = f"drone_{drone_id}"
                    if drone_key in assignments and priority_zones:
                        target = priority_zones[assignments[drone_key] % len(priority_zones)]
                        dx = (target[1] - x) / max(1, self.grid_size)
                        dy = (target[0] - y) / max(1, self.grid_size)
                        obs[i + 1, j + 1, 7] = np.clip((dx + 1.0) * 0.5, 0.0, 1.0)
                        obs[i + 1, j + 1, 8] = np.clip((dy + 1.0) * 0.5, 0.0, 1.0)

        np.clip(obs, 0.0, 1.0, out=obs)
        return obs

    def _calculate_reward(self) -> float:
        burning_cells = float(np.sum(self.fire_sim.fire_state == 1))
        total_cells = float(self.grid_size * self.grid_size)
        fire_coverage = burning_cells / total_cells

        lambda_f = float(self.config.reward_coefficients.get("lambda_f", 10.0))
        lambda_s = float(self.config.reward_coefficients.get("lambda_s", 2.0))
        lambda_b = float(self.config.reward_coefficients.get("lambda_b", 1.0))
        lambda_z = float(self.config.reward_coefficients.get("lambda_z", 1.0))

        fire_reward = -fire_coverage * lambda_f
        total_suppression = sum(drone.suppression_count for drone in self.drones)
        suppression_reward = total_suppression * lambda_s
        avg_battery = sum(drone.battery for drone in self.drones) / len(self.drones)
        battery_penalty = -lambda_b if avg_battery < 0.2 else 0.0

        strategic_bonus = 0.0
        if self.config.use_strategy_reward and self.current_strategy:
            priority_zones = self.current_strategy.get("priority_zones", [])
            if priority_zones:
                for drone in self.drones:
                    distances = [
                        abs(drone.position[0] - zone[0]) + abs(drone.position[1] - zone[1])
                        for zone in priority_zones
                    ]
                    min_dist = min(distances)
                    strategic_bonus += max(
                        0.0,
                        1.0 - min_dist / max(1.0, self.config.normalization_radius / 2.0),
                    )
                strategic_bonus *= lambda_z

        return fire_reward + suppression_reward + battery_penalty + strategic_bonus

    def step(self, action: int):
        self._update_strategy(force=False)

        drone = self.drones[0]
        action = int(action)
        action_result = drone.act(action, self.fire_sim, self.drones)
        self.last_action = action
        if action == 0:
            self.episode_idle_steps += 1
        self.episode_water_used += float(action_result.get("water_used", 0.0))

        self.fire_sim.step()
        self.current_step += 1
        if not self.fire_sim.is_fire_active() and self.containment_step is None:
            self.containment_step = self.current_step

        reward = self._calculate_reward()
        self.episode_return += reward

        terminated = self.current_step >= self.max_steps or not self.fire_sim.is_fire_active()
        truncated = drone.battery <= 0
        obs = self._get_observation(0)
        info = {
            "current_step": self.current_step,
            "strategy_source": (
                self.current_strategy.get("source", "llm") if self.current_strategy else "none"
            ),
        }
        if terminated or truncated:
            info["episode_summary"] = self.get_episode_metrics()
        return obs, reward, terminated, truncated, info

    def get_episode_metrics(self) -> Dict[str, Any]:
        burning = float(np.sum(self.fire_sim.fire_state == 1))
        burned = float(np.sum(self.fire_sim.fire_state != 0))
        total_cells = float(self.grid_size * self.grid_size)
        contained = 1.0 if burning == 0 else 0.0
        contained_area = max(1.0, total_cells - burned)
        return {
            "episode_return": self.episode_return,
            "time_to_containment": self.containment_step or self.max_steps,
            "final_burned_area": burned,
            "water_used": self.episode_water_used,
            "idle_steps": self.episode_idle_steps,
            "success_flag": contained,
            "containment_percent": (1.0 - burning / total_cells) * 100.0,
            "agent_efficiency": self.episode_water_used / contained_area,
            "burning_cells_final": burning,
            "scenario_name": self.current_scenario["fire_name"],
            "scenario_year": self.current_scenario["year"],
        }


class TrainingMetricsCallback(BaseCallback):
    """Log training curves, checkpoints, and strategist statistics."""

    def __init__(self, config: ExperimentConfig, verbose: int = 1) -> None:
        super().__init__(verbose)
        self.config = config
        self.start_time = 0.0
        self.curve_rows: List[Dict[str, Any]] = []

    def _on_training_start(self) -> None:
        self.start_time = time.time()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.config.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        write_json(self.config.manifest_path, self.config.to_manifest_payload())

    def _maybe_agent_stats(self) -> Dict[str, Any]:
        try:
            agents = self.training_env.get_attr("hybrid_agent")
            agent = agents[0] if agents else None
            if agent is None:
                return {}
            return agent.get_statistics()
        except Exception:
            return {}

    def _record_curve_row(self) -> None:
        episode_rewards = [entry["r"] for entry in self.model.ep_info_buffer if "r" in entry]
        episode_lengths = [entry["l"] for entry in self.model.ep_info_buffer if "l" in entry]
        row = {
            "num_timesteps": self.num_timesteps,
            "mean_episode_reward": float(safe_mean(episode_rewards)) if episode_rewards else math.nan,
            "mean_episode_length": float(safe_mean(episode_lengths)) if episode_lengths else math.nan,
            "timestamp": now_iso(),
        }
        row.update(self._maybe_agent_stats())
        self.curve_rows.append(row)
        pd.DataFrame(self.curve_rows).to_csv(self.config.train_curve_path, index=False)

    def _on_rollout_end(self) -> None:
        self._record_curve_row()

    def _on_step(self) -> bool:
        save_freq = int(self.config.metadata.get("save_freq", 40960))
        if save_freq > 0 and self.num_timesteps > 0 and self.num_timesteps % save_freq == 0:
            checkpoint_path = self.config.checkpoints_dir / f"checkpoint_step_{self.num_timesteps}.zip"
            self.model.save(str(checkpoint_path))
        return True

    def _on_training_end(self) -> None:
        elapsed = time.time() - self.start_time
        summary = {
            "variant_name": self.config.variant_name,
            "run_name": self.config.run_name,
            "seed": self.config.seed,
            "total_timesteps": self.num_timesteps,
            "training_time_seconds": elapsed,
            "training_time_minutes": elapsed / 60.0,
            "llm_stats": self._maybe_agent_stats(),
            "curve_rows": len(self.curve_rows),
        }
        write_json(self.config.training_summary_path, summary)


def make_env(config: ExperimentConfig, scenario_spec: Optional[Dict[str, Any]] = None, evaluation_seed: Optional[int] = None):
    def _init():
        integrator = RealDataIntegrator(
            seed=config.seed if evaluation_seed is None else evaluation_seed,
            quiet=True,
        )
        env = AuroraExperimentEnv(
            config=config,
            integrator=integrator,
            scenario_spec=scenario_spec,
            evaluation_seed=evaluation_seed,
        )
        monitor_path = config.train_monitor_path if scenario_spec is None else None
        return Monitor(env, filename=str(monitor_path) if monitor_path else None)

    return _init


def build_model(config: ExperimentConfig, env: DummyVecEnv) -> PPO:
    return PPO(
        "MlpPolicy",
        env,
        learning_rate=float(config.ppo.get("learning_rate", 3e-4)),
        n_steps=int(config.ppo.get("n_steps", 2048)),
        batch_size=int(config.ppo.get("batch_size", 64)),
        n_epochs=int(config.ppo.get("n_epochs", 10)),
        gamma=float(config.ppo.get("gamma", 0.99)),
        gae_lambda=float(config.ppo.get("gae_lambda", 0.95)),
        clip_range=float(config.ppo.get("clip_range", 0.2)),
        verbose=1,
        policy_kwargs=dict(net_arch=[256, 256, 128]),
        seed=config.seed,
        tensorboard_log=None,
    )


def unpack_model_archive(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(source), extract_dir=str(destination))
    source.unlink()


def train_single_run(config: ExperimentConfig) -> Dict[str, Any]:
    set_global_seed(config.seed)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    manifest = config.to_manifest_payload()
    manifest["status"] = "running"
    write_json(config.manifest_path, manifest)

    env = DummyVecEnv([make_env(config)])
    model = build_model(config, env)
    callback = TrainingMetricsCallback(config=config, verbose=1)
    callback.config.metadata["save_freq"] = 40960

    started_at = now_iso()
    try:
        model.learn(total_timesteps=config.total_timesteps, callback=callback, progress_bar=False)
    except Exception as error:
        manifest["status"] = "failed"
        manifest["error"] = str(error)
        manifest["ended_at"] = now_iso()
        write_json(config.manifest_path, manifest)
        env.close()
        raise

    model_base = config.output_dir / config.model_label
    model.save(str(model_base))
    if config.model_zip_path.exists():
        unpack_model_archive(config.model_zip_path, config.model_dir)
        shutil.make_archive(str(model_base), "zip", root_dir=str(config.model_dir))

    eval_frame = evaluate_checkpoint(config=config, model_path=config.model_zip_path)
    eval_frame.to_csv(config.eval_csv_path, index=False)
    eval_summary = summarize_evaluation_frame(
        eval_frame,
        easy_seeds=config.easy_seeds,
        hard_seeds=config.hard_seeds,
        budget_timesteps=config.total_timesteps,
    )
    write_json(config.eval_json_path, eval_summary)

    manifest["status"] = "completed"
    manifest["started_at"] = started_at
    manifest["ended_at"] = now_iso()
    manifest["evaluation_rows"] = len(eval_frame)
    write_json(config.manifest_path, manifest)
    env.close()
    return {
        "config": config,
        "manifest": manifest,
        "evaluation": eval_summary,
    }


def load_model(model_path: Path) -> PPO:
    return PPO.load(str(model_path), device="cpu")


def evaluate_checkpoint(config: ExperimentConfig, model_path: Path) -> pd.DataFrame:
    model = load_model(model_path)
    rows: List[Dict[str, Any]] = []

    for fire in config.eval_scenarios:
        for seed in config.eval_seeds:
            env = AuroraExperimentEnv(
                config=config,
                integrator=RealDataIntegrator(seed=seed, quiet=True),
                scenario_spec=fire,
                evaluation_seed=seed,
            )
            observation, _ = env.reset(seed=seed)
            done = False
            truncated = False
            while not done and not truncated:
                action, _ = model.predict(observation, deterministic=True)
                observation, _, done, truncated, _ = env.step(int(action))

            metrics = env.get_episode_metrics()
            metrics.update(
                {
                    "variant_name": config.variant_name,
                    "run_name": config.run_name,
                    "training_seed": config.seed,
                    "seed": seed,
                    "evaluation_seed": seed,
                    "difficulty_bucket": (
                        "easy"
                        if seed in config.easy_seeds
                        else "hard" if seed in config.hard_seeds else "unassigned"
                    ),
                }
            )
            rows.append(metrics)

    return pd.DataFrame(rows)


def summarize_evaluation_frame(
    frame: pd.DataFrame,
    easy_seeds: Sequence[int],
    hard_seeds: Sequence[int],
    budget_timesteps: int,
) -> Dict[str, Any]:
    def stats_for(subset: pd.DataFrame) -> Dict[str, Any]:
        if subset.empty:
            return {}
        return {
            "mean_return": float(subset["episode_return"].mean()),
            "std_return": float(subset["episode_return"].std(ddof=0)),
            "mean_hard_scenario_return": float(subset["episode_return"].mean()),
            "std_hard_scenario_return": float(subset["episode_return"].std(ddof=0)),
            "mean_containment_rate": float(subset["success_flag"].mean()),
            "mean_burned_area": float(subset["final_burned_area"].mean()),
        }

    easy_frame = frame[frame["seed"].isin(list(easy_seeds))]
    hard_frame = frame[frame["seed"].isin(list(hard_seeds))]

    summary = {
        "mean_final_return": float(frame["episode_return"].mean()),
        "std_final_return": float(frame["episode_return"].std(ddof=0)),
        "mean_easy_scenario_return": float(easy_frame["episode_return"].mean()) if not easy_frame.empty else math.nan,
        "std_easy_scenario_return": float(easy_frame["episode_return"].std(ddof=0)) if not easy_frame.empty else math.nan,
        "mean_hard_scenario_return": float(hard_frame["episode_return"].mean()) if not hard_frame.empty else math.nan,
        "std_hard_scenario_return": float(hard_frame["episode_return"].std(ddof=0)) if not hard_frame.empty else math.nan,
        "mean_containment_rate": float(frame["success_flag"].mean()),
        "mean_burned_area": float(frame["final_burned_area"].mean()),
        "budget_timesteps": int(budget_timesteps),
        "num_eval_episodes": int(len(frame)),
    }
    return summary


def aggregate_runs(
    run_dirs: Sequence[Path],
    output_dir: Path,
    family_name: str,
) -> Dict[str, Any]:
    eval_frames = []
    training_curves = []
    manifests = []
    run_summaries = []
    for run_dir in run_dirs:
        eval_path = run_dir / "evaluation_metrics.csv"
        eval_summary_path = run_dir / "evaluation_summary.json"
        curve_path = run_dir / "training_curve.csv"
        manifest_path = run_dir / "run_manifest.json"
        if eval_path.exists():
            eval_frames.append(pd.read_csv(eval_path))
        if eval_summary_path.exists():
            summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
            summary["seed"] = int(run_dir.name.split("_")[-1])
            run_summaries.append(summary)
        if curve_path.exists():
            curve = pd.read_csv(curve_path)
            curve["seed"] = int(run_dir.name.split("_")[-1])
            training_curves.append(curve)
        if manifest_path.exists():
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))

    output_dir.mkdir(parents=True, exist_ok=True)
    aggregate_summary = {
        "family_name": family_name,
        "num_runs": len(run_dirs),
        "seeds": sorted(
            {
                int(manifest.get("seed"))
                for manifest in manifests
                if manifest.get("seed") is not None
            }
        ),
    }

    if eval_frames:
        combined_eval = pd.concat(eval_frames, ignore_index=True)
        combined_eval.to_csv(output_dir / "combined_evaluation_metrics.csv", index=False)

    if run_summaries:
        summary_frame = pd.DataFrame(run_summaries).sort_values("seed")
        summary_frame.to_csv(output_dir / "aggregate_metrics.csv", index=False)
        aggregate_summary.update(
            {
                "mean_final_return": float(summary_frame["mean_final_return"].mean()),
                "std_final_return": float(summary_frame["mean_final_return"].std(ddof=0)),
                "mean_easy_scenario_return": float(summary_frame["mean_easy_scenario_return"].mean()),
                "std_easy_scenario_return": float(summary_frame["mean_easy_scenario_return"].std(ddof=0)),
                "mean_hard_scenario_return": float(summary_frame["mean_hard_scenario_return"].mean()),
                "std_hard_scenario_return": float(summary_frame["mean_hard_scenario_return"].std(ddof=0)),
                "mean_containment_rate": float(summary_frame["mean_containment_rate"].mean()),
                "std_containment_rate": float(summary_frame["mean_containment_rate"].std(ddof=0)),
                "mean_burned_area": float(summary_frame["mean_burned_area"].mean()),
                "std_burned_area": float(summary_frame["mean_burned_area"].std(ddof=0)),
                "budget_timesteps": int(summary_frame["budget_timesteps"].iloc[0]),
                "num_eval_episodes": int(summary_frame["num_eval_episodes"].sum()),
            }
        )

    if training_curves:
        combined_curves = pd.concat(training_curves, ignore_index=True)
        combined_curves.to_csv(output_dir / "aggregate_training_curves.csv", index=False)

    write_json(output_dir / "aggregate_summary.json", aggregate_summary)
    return aggregate_summary


def aggregate_variant_summaries(variant_root: Path) -> pd.DataFrame:
    rows = []
    for variant_dir in sorted(path for path in variant_root.iterdir() if path.is_dir()):
        summary_path = variant_dir / "aggregate_summary.json"
        if not summary_path.exists():
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["variant"] = variant_dir.name
        rows.append(summary)
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "| status |\n|---|\n| no data |"

    display = frame.copy()
    for column in display.columns:
        if np.issubdtype(display[column].dtype, np.number):
            display[column] = display[column].map(
                lambda value: f"{value:.4f}" if isinstance(value, float) and not value.is_integer() else str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)
            )

    header = "| " + " | ".join(display.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(display.columns)) + " |"
    rows = ["| " + " | ".join(str(value) for value in row) + " |" for row in display.to_numpy()]
    return "\n".join([header, divider, *rows])


def create_training_curve_plot(
    variant_dirs: Dict[str, List[Path]],
    output_prefix: Path,
    title: str,
) -> None:
    plt.figure(figsize=(10, 6))

    for label, run_dirs in variant_dirs.items():
        curves = []
        for run_dir in run_dirs:
            curve_path = run_dir / "training_curve.csv"
            if curve_path.exists():
                curve = pd.read_csv(curve_path)
                if not curve.empty:
                    curves.append(curve[["num_timesteps", "mean_episode_reward"]].dropna())
        if not curves:
            continue

        min_len = min(len(curve) for curve in curves)
        aligned = np.stack(
            [curve.iloc[:min_len]["mean_episode_reward"].to_numpy(dtype=float) for curve in curves],
            axis=0,
        )
        x_values = curves[0].iloc[:min_len]["num_timesteps"].to_numpy(dtype=float)
        mean = aligned.mean(axis=0)
        std = aligned.std(axis=0)
        plt.plot(x_values, mean, label=label)
        plt.fill_between(x_values, mean - std, mean + std, alpha=0.18)

    plt.xlabel("Training Timesteps")
    plt.ylabel("Return")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_prefix.with_suffix(".png"))
    plt.savefig(output_prefix.with_suffix(".pdf"))
    plt.close()


def create_bar_plot(
    frame: pd.DataFrame,
    output_path: Path,
    title: str,
    metric_columns: Sequence[str],
) -> None:
    if frame.empty:
        return

    plt.figure(figsize=(10, 6))
    x = np.arange(len(frame))
    width = 0.22 if len(metric_columns) > 1 else 0.5

    for index, column in enumerate(metric_columns):
        offsets = x + (index - (len(metric_columns) - 1) / 2.0) * width
        std_column = column.replace("_mean", "_std")
        plt.bar(
            offsets,
            frame[column].to_numpy(dtype=float),
            width=width,
            label=column.replace("_mean", ""),
            yerr=frame[std_column].to_numpy(dtype=float) if std_column in frame.columns else None,
            capsize=4,
        )

    plt.xticks(x, frame["variant"], rotation=15)
    plt.ylabel("Return")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path.with_suffix(".png"))
    plt.savefig(output_path.with_suffix(".pdf"))
    plt.close()


def create_cadence_plot(frame: pd.DataFrame, output_path: Path) -> None:
    if frame.empty:
        return
    order = ["dense", "baseline", "sparse"]
    cadence_frame = frame.copy()
    cadence_frame["variant"] = pd.Categorical(cadence_frame["variant"], categories=order, ordered=True)
    cadence_frame = cadence_frame.sort_values("variant")

    plt.figure(figsize=(8, 5))
    plt.plot(cadence_frame["variant"].astype(str), cadence_frame["overall_mean"], marker="o")
    plt.fill_between(
        cadence_frame["variant"].astype(str),
        cadence_frame["overall_mean"] - cadence_frame["overall_std"],
        cadence_frame["overall_mean"] + cadence_frame["overall_std"],
        alpha=0.2,
    )
    plt.xlabel("Cadence")
    plt.ylabel("Return")
    plt.title("Guidance Cadence Ablation")
    plt.tight_layout()
    plt.savefig(output_path.with_suffix(".png"))
    plt.savefig(output_path.with_suffix(".pdf"))
    plt.close()


def build_mechanism_table(root: Path) -> pd.DataFrame:
    if not root.exists():
        return pd.DataFrame(columns=["variant", "easy_mean", "easy_std", "hard_mean", "hard_std", "overall_mean", "overall_std"])
    rows = []
    for variant_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        summary_path = variant_dir / "aggregate_summary.json"
        if not summary_path.exists():
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        rows.append(
            {
                "variant": variant_dir.name,
                "easy_mean": summary.get("mean_easy_scenario_return"),
                "easy_std": summary.get("std_easy_scenario_return"),
                "hard_mean": summary.get("mean_hard_scenario_return"),
                "hard_std": summary.get("std_hard_scenario_return"),
                "overall_mean": summary.get("mean_final_return"),
                "overall_std": summary.get("std_final_return"),
            }
        )
    return pd.DataFrame(rows)


def build_hyperparameter_table(study: Dict[str, Any]) -> pd.DataFrame:
    defaults = study["defaults"]
    return pd.DataFrame(
        [
            {"parameter": "N number of drones", "value": defaults["num_drones"]},
            {"parameter": "K guidance interval", "value": defaults["guidance_interval"]},
            {"parameter": "PPO clip epsilon", "value": defaults["ppo"]["clip_range"]},
            {"parameter": "gamma", "value": defaults["ppo"]["gamma"]},
            {"parameter": "GAE lambda", "value": defaults["ppo"]["gae_lambda"]},
            {"parameter": "learning rate", "value": defaults["ppo"]["learning_rate"]},
            {"parameter": "batch size", "value": defaults["ppo"]["batch_size"]},
            {"parameter": "episode length", "value": defaults["max_steps"]},
            {"parameter": "grid size", "value": defaults["grid_size"]},
            {"parameter": "reward lambda_f", "value": defaults["reward_coefficients"]["lambda_f"]},
            {"parameter": "reward lambda_s", "value": defaults["reward_coefficients"]["lambda_s"]},
            {"parameter": "reward lambda_b", "value": defaults["reward_coefficients"]["lambda_b"]},
            {"parameter": "reward lambda_z", "value": defaults["reward_coefficients"]["lambda_z"]},
            {"parameter": "normalization radius R", "value": defaults["normalization_radius"]},
            {"parameter": "LLM model", "value": defaults["llm_model"]},
            {"parameter": "LLM backend", "value": defaults["llm_backend"]},
            {"parameter": "LLM temperature", "value": defaults.get("llm_decoding", {}).get("temperature")},
            {"parameter": "LLM max_new_tokens", "value": defaults.get("llm_decoding", {}).get("max_new_tokens")},
            {"parameter": "LLM do_sample", "value": defaults.get("llm_decoding", {}).get("do_sample")},
            {"parameter": "training budget", "value": defaults["total_timesteps"]},
            {"parameter": "evaluation scenarios", "value": ", ".join(fire["name"] for fire in EVALUATION_FIRES)},
        ]
    )


def write_estrat_spec(output_path: Path) -> None:
    text = """# E_strat Specification

`E_strat` is the strategic overlay appended to the base 3x3 local observation tensor. The current tensor shape is `(3, 3, 9)`, where channels `0-5` are world/state features and channels `6-8` are strategic channels.

## Channel semantics

- Channel 6: priority-zone proximity. For each observed cell, compute Manhattan distance to the nearest strategy `priority_zone` and map it to `max(0, 1 - distance / R)` where `R = 50` by default.
- Channel 7: normalized x-direction to the assigned priority zone for the active drone, encoded as `clip((dx + 1) * 0.5, 0, 1)`.
- Channel 8: normalized y-direction to the assigned priority zone for the active drone, encoded as `clip((dy + 1) * 0.5, 0, 1)`.

## Mapping from strategy fields

- `priority_zones -> channel 6`
- `drone_assignments + priority_zones -> channels 7 and 8`

## Encoding properties

- Tensor shape: `(3, 3, 9)`
- Channel 6 is distance-based
- Channels 7-8 are assignment-based directional encodings
- All values are clipped to `[0, 1]`

## Pseudocode

```text
obs = zeros(3, 3, 9)
fill channels 0..5 from fire, terrain, elevation, fuel, battery, water
if strategy exists:
    for each visible cell:
        channel6 = max(0, 1 - manhattan(cell, nearest_priority_zone) / R)
    assigned_zone = priority_zones[drone_assignments[current_drone]]
    channel7 = clip((dx / grid_size + 1) * 0.5, 0, 1)
    channel8 = clip((dy / grid_size + 1) * 0.5, 0, 1)
```

## Concrete example

If the active drone is at `(25, 25)` and its assigned strategic target is `(20, 30)`, then:

- `dx = (30 - 25) / 50 = 0.1`
- `dy = (20 - 25) / 50 = -0.1`
- `channel7 = 0.55`
- `channel8 = 0.45`
"""
    write_text(output_path, text)


def load_guidance_events(root: Path) -> pd.DataFrame:
    rows = []
    seen_paths = set()
    patterns = ["guidance_log.jsonl", "*single_call*guidance*.jsonl"]
    for pattern in patterns:
        for path in root.rglob(pattern):
            resolved = str(path.resolve())
            if resolved in seen_paths or not path.exists():
                continue
            seen_paths.add(resolved)
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    event = json.loads(line)
                    event["guidance_log_path"] = str(path)
                    event["guidance_log_type"] = (
                        "single_call_diagnostic"
                        if path.name.startswith("single_call_guidance")
                        else "run_guidance"
                    )
                    rows.append(event)
    return pd.DataFrame(rows)


def write_fallback_analysis(root: Path) -> Dict[str, Any]:
    analysis_dir = root / "fallback_analysis"
    events = load_guidance_events(root)
    if events.empty:
        summary = {
            "llm_queries": 0,
            "valid_structured_parses": 0,
            "fallback_invocations": 0,
            "fallback_rate_percentage": None,
            "note": "No LLM guidance events were available.",
        }
        write_json(analysis_dir / "fallback_rate_summary.json", summary)
        write_text(analysis_dir / "README.md", "No LLM guidance logs were available.\n")
        return summary

    llm_attempt_mask = events["llm_query_attempted"].fillna(False)
    llm_queries = int(llm_attempt_mask.sum())
    valid_parses = int((events["valid_structured_parse"].fillna(False) & llm_attempt_mask).sum())
    fallback_invocations = int((events["fallback_invoked"].fillna(False) & llm_attempt_mask).sum())
    fallback_rate = (fallback_invocations / llm_queries * 100.0) if llm_queries else None

    summary = {
        "llm_queries": llm_queries,
        "valid_structured_parses": valid_parses,
        "fallback_invocations": fallback_invocations,
        "fallback_rate_percentage": fallback_rate,
        "guidance_log_types": sorted(events["guidance_log_type"].dropna().unique().tolist()),
    }
    write_json(analysis_dir / "fallback_rate_summary.json", summary)

    valid_rows = events[events["valid_structured_parse"].fillna(False) & llm_attempt_mask]
    if not valid_rows.empty:
        preferred_rows = valid_rows[
            valid_rows["guidance_log_path"].fillna("").str.contains("qwen3b", case=False)
        ]
        sample = (preferred_rows.iloc[0] if not preferred_rows.empty else valid_rows.iloc[0]).to_dict()
        write_text(analysis_dir / "example_prompt.txt", sample.get("prompt", ""))
        write_json(
            analysis_dir / "example_response.json",
            sample.get("parsed_guidance", {}),
        )
        explanation = f"""# Fallback Analysis

- Fields present in the structured response: {", ".join(sample.get("parsed_guidance", {}).keys())}
- Response was schema-constrained by a JSON-only prompt: yes
- Fallback happened in the sampled run: {"yes" if sample.get("fallback_invoked") else "no"}
- Sample log type: {sample.get("guidance_log_type")}
"""
        write_text(analysis_dir / "README.md", explanation)
    else:
        write_text(
            analysis_dir / "README.md",
            "# Fallback Analysis\n\nNo valid structured LLM response was captured.\n",
        )

    return summary


def cli_train(default_variant: str) -> None:
    parser = argparse.ArgumentParser(description="Train AURORA variants through the shared pipeline.")
    parser.add_argument("--phase", type=str, default="full")
    parser.add_argument("--timesteps", type=int, default=None)
    parser.add_argument("--n_envs", type=int, default=1)
    parser.add_argument("--llm_model", type=str, default=None)
    parser.add_argument("--llm_freq", type=int, default=None)
    parser.add_argument("--hf_token", type=str, default=None)
    parser.add_argument("--llm_backend", type=str, default="transformers")
    parser.add_argument("--save_freq", type=int, default=40960)
    parser.add_argument("--eval_freq", type=int, default=81920)
    parser.add_argument("--progress_freq", type=int, default=100)
    parser.add_argument("--resume", action="store_true", default=False)
    parser.add_argument("--verbose", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1001)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--use_llm_guidance", type=str2bool, default=None)
    parser.add_argument("--use_heuristic_strategist", type=str2bool, default=None)
    parser.add_argument("--use_strategic_obs_channels", type=str2bool, default=None)
    parser.add_argument("--use_strategy_reward", type=str2bool, default=None)
    parser.add_argument("--guidance_interval", type=int, default=None)
    parser.add_argument("--model_label", type=str, default=None)
    parser.add_argument("--run_name", type=str, default=None)
    parser.add_argument("--variant", type=str, default=default_variant)
    args = parser.parse_args()

    study = load_study_definition()
    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else RESULTS_ROOT / "manual_runs" / args.variant / f"seed_{args.seed}"
    )
    overrides: Dict[str, Any] = {"phase": args.phase, "n_envs": args.n_envs, "llm_backend": args.llm_backend}
    if args.timesteps is not None:
        overrides["total_timesteps"] = args.timesteps
    if args.llm_model is not None:
        overrides["llm_model"] = args.llm_model
    if args.use_llm_guidance is not None:
        overrides["use_llm_guidance"] = args.use_llm_guidance
    if args.use_heuristic_strategist is not None:
        overrides["use_heuristic_strategist"] = args.use_heuristic_strategist
    if args.use_strategic_obs_channels is not None:
        overrides["use_strategic_obs_channels"] = args.use_strategic_obs_channels
    if args.use_strategy_reward is not None:
        overrides["use_strategy_reward"] = args.use_strategy_reward
    if args.model_label is not None:
        overrides["model_label"] = args.model_label

    config = build_experiment_config(
        study=study,
        family="manual_runs",
        variant_key=args.variant,
        seed=args.seed,
        output_dir=output_dir,
        run_name=args.run_name,
        guidance_interval=args.guidance_interval or args.llm_freq,
        overrides=overrides,
    )
    if args.hf_token:
        os.environ["HF_TOKEN"] = args.hf_token
        config.hf_token = args.hf_token
    train_single_run(config)
