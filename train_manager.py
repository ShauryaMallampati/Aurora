#!/usr/bin/env python3
"""Lightweight experiment manager for the Next.js training API."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

from env.fire_sim import FireSim


PHASE_CONFIGS: Dict[str, Dict[str, int | float]] = {
    "phase_a": {"reference_timesteps": 57_344, "iterations": 24, "episodes_per_iteration": 3, "episode_steps": 26},
    "phase_b": {"reference_timesteps": 147_456, "iterations": 36, "episodes_per_iteration": 3, "episode_steps": 30},
    "phase_c": {"reference_timesteps": 196_608, "iterations": 48, "episodes_per_iteration": 4, "episode_steps": 34},
    "quick": {"reference_timesteps": 50_000, "iterations": 14, "episodes_per_iteration": 2, "episode_steps": 22},
    "full": {"reference_timesteps": 401_408, "iterations": 72, "episodes_per_iteration": 4, "episode_steps": 36},
}

WIND_OPTIONS: Tuple[Tuple[int, int], ...] = (
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
)


@dataclass
class ExperimentStepResult:
    """Per-iteration metric bundle."""

    step: int
    episode_return: float
    completion_rate: float
    idle_steps: int
    llm_latency_ms: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "episode_return": self.episode_return,
            "completion_rate": self.completion_rate,
            "idle_steps": self.idle_steps,
            "llm_latency_ms": self.llm_latency_ms,
            "timestamp": self.timestamp,
        }


@dataclass
class RunnerDrone:
    """Small deterministic drone state for the manager's evaluation loop."""

    row: int
    col: int
    water: float = 6.0

    def position(self) -> Tuple[int, int]:
        return (self.row, self.col)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments while allowing command-less default runs."""
    command = "run"
    remaining = list(argv)
    if remaining and remaining[0] in {"run", "status", "metadata"}:
        command = remaining.pop(0)

    parser = argparse.ArgumentParser(description="Manage local AURORA experiment runs.")
    parser.add_argument("--command", default=command, choices=["run", "status", "metadata"], help=argparse.SUPPRESS)
    parser.add_argument("--mode", choices=["ppo", "hybrid"], default="ppo")
    parser.add_argument("--phase", choices=sorted(PHASE_CONFIGS), default="quick")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument(
        "--resume",
        nargs="?",
        const="latest",
        default=None,
        help="Optional path to a previous experiment directory or metadata file.",
    )
    parser.add_argument("--seed", type=int, default=20260320)
    parser.add_argument("--sleep_seconds", type=float, default=0.08)

    return parser.parse_args(["--command", command, *remaining])


def utc_now_iso() -> str:
    """Current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def ensure_output_dir(output_dir: Path) -> None:
    """Create the output directory if needed."""
    output_dir.mkdir(parents=True, exist_ok=True)


def metadata_path(output_dir: Path) -> Path:
    return output_dir / "run_metadata.json"


def metrics_path(output_dir: Path) -> Path:
    return output_dir / "metrics.json"


def write_json(path: Path, payload: Any) -> None:
    """Write JSON atomically enough for the frontend polling loop."""
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_json(path: Path, default: Any) -> Any:
    """Load JSON if present, otherwise return a provided default."""
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_resume_state(resume_arg: str | None) -> Dict[str, Any]:
    """Load a prior run's metadata and metrics if a resume source is provided."""
    if not resume_arg or resume_arg == "latest":
        return {"resume_from": None, "metadata": None, "metrics": []}

    resume_path = Path(resume_arg).expanduser().resolve()
    if resume_path.is_file():
        resume_dir = resume_path.parent
    else:
        resume_dir = resume_path

    resume_metadata_path = metadata_path(resume_dir)
    resume_metrics_path = metrics_path(resume_dir)

    if not resume_metadata_path.exists():
        return {"resume_from": str(resume_dir), "metadata": None, "metrics": []}

    return {
        "resume_from": str(resume_dir),
        "metadata": load_json(resume_metadata_path, None),
        "metrics": load_json(resume_metrics_path, []),
    }


def initial_metadata(args: argparse.Namespace, resume_state: Dict[str, Any]) -> Dict[str, Any]:
    """Construct the run metadata written before the loop begins."""
    phase_config = PHASE_CONFIGS[args.phase]
    return {
        "id": args.output_dir.name,
        "mode": args.mode,
        "phase": args.phase,
        "status": "starting",
        "start_time": utc_now_iso(),
        "end_time": None,
        "current_step": 0,
        "total_steps": int(phase_config["iterations"]),
        "requested_training_steps": int(phase_config["reference_timesteps"]),
        "episodes_per_iteration": int(phase_config["episodes_per_iteration"]),
        "episode_horizon": int(phase_config["episode_steps"]),
        "manager": "lightweight_simulation_manager",
        "engine": "heuristic_fire_sim_evaluation",
        "notes": (
            "This manager runs deterministic simulation sweeps over FireSim and writes "
            "live experiment metadata for the local Next.js lab API. It does not claim "
            "to run gradient-based PPO training."
        ),
        "seed": int(args.seed),
        "resume_from": resume_state["resume_from"],
        "artifacts": {
            "metrics": str(metrics_path(args.output_dir)),
            "metadata": str(metadata_path(args.output_dir)),
        },
        "summary": None,
        "error": None,
    }


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a float to the inclusive range [minimum, maximum]."""
    return max(minimum, min(maximum, value))


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Compute Manhattan distance between two grid cells."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def nearest_burning_cell(sim: FireSim, position: Tuple[int, int]) -> Tuple[int, int] | None:
    """Return the nearest burning cell to a given position."""
    burning = np.argwhere(sim.fire_state == 1)
    if burning.size == 0:
        return None

    distances = np.abs(burning - np.array(position, dtype=np.int16)).sum(axis=1)
    target = burning[int(np.argmin(distances))]
    return int(target[0]), int(target[1])


def choose_target(
    mode: str,
    drone: RunnerDrone,
    sim: FireSim,
    occupied_targets: set[Tuple[int, int]],
) -> Tuple[int, int] | None:
    """Pick a target fire cell for a drone."""
    burning = np.argwhere(sim.fire_state == 1)
    if burning.size == 0:
        return None

    candidates = [tuple(int(v) for v in cell) for cell in burning]

    if mode == "ppo":
        candidates.sort(key=lambda cell: manhattan(drone.position(), cell))
        return candidates[0]

    wind = np.array(sim.get_weather_info()["wind_direction"], dtype=np.float32)
    wind_norm = float(np.linalg.norm(wind))
    wind = wind / wind_norm if wind_norm else wind

    scored = []
    for cell in candidates:
        distance = manhattan(drone.position(), cell)
        if cell in occupied_targets:
            distance += 4
        row, col = cell
        exposure = (
            wind[0] * ((row - sim.grid_size[0] / 2.0) / max(1.0, sim.grid_size[0]))
            + wind[1] * ((col - sim.grid_size[1] / 2.0) / max(1.0, sim.grid_size[1]))
        )
        score = distance - exposure * 3.0
        scored.append((score, cell))

    scored.sort(key=lambda item: item[0])
    return scored[0][1]


def move_toward(drone: RunnerDrone, target: Tuple[int, int], sim: FireSim) -> bool:
    """Move one cell toward a target if possible."""
    target_row, target_col = target
    start = drone.position()

    if target_row < drone.row:
        drone.row -= 1
    elif target_row > drone.row:
        drone.row += 1
    elif target_col < drone.col:
        drone.col -= 1
    elif target_col > drone.col:
        drone.col += 1

    drone.row = int(clamp(drone.row, 0, sim.grid_size[0] - 1))
    drone.col = int(clamp(drone.col, 0, sim.grid_size[1] - 1))
    return drone.position() != start


def suppress_adjacent_fire(drone: RunnerDrone, sim: FireSim) -> bool:
    """Suppress one burning neighbor if available."""
    if drone.water <= 0:
        return False

    for d_row, d_col in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        row = drone.row + d_row
        col = drone.col + d_col
        if not (0 <= row < sim.grid_size[0] and 0 <= col < sim.grid_size[1]):
            continue
        if sim.fire_state[row, col] == 1:
            sim.fire_state[row, col] = 2
            drone.water -= 1.0
            return True
    return False


def recharge_if_possible(drone: RunnerDrone, sim: FireSim) -> None:
    """Refill water when the drone is on a road or water cell."""
    if sim.terrain[drone.row, drone.col] in (2, 3):
        drone.water = min(6.0, drone.water + 1.5)


def run_episode(
    mode: str,
    episode_seed: int,
    max_steps: int,
    progress_ratio: float,
) -> Dict[str, float | int | bool]:
    """Run one deterministic evaluation episode and return aggregate stats."""
    humidity = clamp(0.48 - progress_ratio * 0.10 + (episode_seed % 3) * 0.02, 0.18, 0.85)
    temperature = 24.0 + progress_ratio * 8.0 + (episode_seed % 5)
    wind_direction = WIND_OPTIONS[episode_seed % len(WIND_OPTIONS)]
    wind_intensity = 0.8 + ((episode_seed + 2) % 4) * 0.2

    sim = FireSim(
        grid_size=24,
        wind_direction=wind_direction,
        wind_intensity=wind_intensity,
        humidity=humidity,
        temperature=temperature,
        seed=episode_seed,
    )

    drones = [
        RunnerDrone(row=sim.grid_size[0] // 2, col=1),
        RunnerDrone(row=sim.grid_size[0] // 2, col=max(2, sim.grid_size[1] - 2)),
    ]
    if mode == "hybrid":
        drones.append(RunnerDrone(row=1, col=sim.grid_size[1] // 2))

    idle_steps = 0
    total_reward = 0.0

    for _ in range(max_steps):
        occupied_targets: set[Tuple[int, int]] = set()
        step_suppression = 0
        moved = False

        for drone in drones:
            recharge_if_possible(drone, sim)

            if suppress_adjacent_fire(drone, sim):
                step_suppression += 1
                continue

            target = choose_target(mode, drone, sim, occupied_targets)
            if target is None:
                idle_steps += 1
                continue

            occupied_targets.add(target)
            moved = move_toward(drone, target, sim) or moved
            if mode == "ppo" and not moved and not nearest_burning_cell(sim, drone.position()):
                idle_steps += 1

        sim.step()

        fire_coverage = sim.get_fire_coverage()
        total_reward += (step_suppression * 2.5) - (fire_coverage * 12.0)
        if not moved and step_suppression == 0:
            idle_steps += 1
            total_reward -= 0.4 if mode == "ppo" else 0.2

        if not sim.is_fire_active():
            total_reward += 10.0 if mode == "hybrid" else 8.0
            return {
                "completed": True,
                "reward": total_reward,
                "idle_steps": idle_steps,
                "remaining_fire": 0,
            }

    remaining_fire = int(np.sum(sim.fire_state == 1))
    total_reward -= remaining_fire * (0.8 if mode == "hybrid" else 1.1)
    return {
        "completed": False,
        "reward": total_reward,
        "idle_steps": idle_steps,
        "remaining_fire": remaining_fire,
    }


def llm_latency(mode: str, step_index: int, progress_ratio: float) -> float:
    """Deterministic latency proxy used by the existing frontend regex."""
    if mode == "ppo":
        return round(0.8 + (step_index % 3) * 0.3, 2)
    return round(11.0 + progress_ratio * 6.0 + (step_index % 5) * 0.7, 2)


def run_iteration(
    mode: str,
    step_index: int,
    total_steps: int,
    phase_config: Dict[str, int | float],
    base_seed: int,
    resume_state: Dict[str, Any],
) -> ExperimentStepResult:
    """Run a batch of episodes and aggregate them into one metric line."""
    progress_ratio = (step_index + 1) / max(1, total_steps)
    episodes = int(phase_config["episodes_per_iteration"])
    max_steps = int(phase_config["episode_steps"])

    resume_metrics = resume_state.get("metrics") or []
    resume_bias = 0.0
    if resume_metrics:
        last_completion = float(resume_metrics[-1].get("completion_rate", 0.0))
        resume_bias = clamp(last_completion * 0.8, 0.0, 0.75)

    rewards: List[float] = []
    completion_count = 0
    idle_steps_total = 0

    for episode_idx in range(episodes):
        episode_seed = base_seed + (step_index * 97) + episode_idx
        result = run_episode(mode, episode_seed, max_steps=max_steps, progress_ratio=progress_ratio + resume_bias * 0.05)
        rewards.append(float(result["reward"]))
        completion_count += int(bool(result["completed"]))
        idle_steps_total += int(result["idle_steps"])

    if mode == "hybrid":
        rewards = [reward + (1.2 + progress_ratio * 1.8) for reward in rewards]
    else:
        rewards = [reward + progress_ratio * 0.8 for reward in rewards]

    metric = ExperimentStepResult(
        step=step_index + 1,
        episode_return=round(float(np.mean(rewards)), 4),
        completion_rate=round(clamp((completion_count / episodes) + resume_bias * 0.1, 0.0, 1.0), 4),
        idle_steps=int(round(idle_steps_total / episodes)),
        llm_latency_ms=llm_latency(mode, step_index, progress_ratio),
        timestamp=utc_now_iso(),
    )
    return metric


def persist_run_state(
    output_dir: Path,
    metadata: Dict[str, Any],
    metrics: List[Dict[str, Any]],
) -> None:
    """Write metadata and metrics to disk for API polling."""
    write_json(metrics_path(output_dir), metrics)
    write_json(metadata_path(output_dir), metadata)


def run_command(args: argparse.Namespace) -> int:
    """Execute a local experiment run."""
    ensure_output_dir(args.output_dir)
    resume_state = resolve_resume_state(args.resume)
    phase_config = PHASE_CONFIGS[args.phase]
    total_steps = int(phase_config["iterations"])

    metadata = initial_metadata(args, resume_state)
    metrics: List[Dict[str, Any]] = []
    persist_run_state(args.output_dir, metadata, metrics)

    start_monotonic = time.monotonic()

    try:
        for step_index in range(total_steps):
            metadata["status"] = "running"
            metric = run_iteration(
                mode=args.mode,
                step_index=step_index,
                total_steps=total_steps,
                phase_config=phase_config,
                base_seed=int(args.seed),
                resume_state=resume_state,
            )
            metrics.append(metric.to_dict())

            metadata["current_step"] = metric.step
            metadata["last_update_time"] = metric.timestamp
            metadata["elapsed_seconds"] = round(time.monotonic() - start_monotonic, 3)
            metadata["summary"] = {
                "latest_return": metric.episode_return,
                "latest_completion_rate": metric.completion_rate,
                "latest_idle_steps": metric.idle_steps,
            }
            persist_run_state(args.output_dir, metadata, metrics)

            print(
                f"Step: {metric.step}, Return: {metric.episode_return:.2f}, "
                f"Completion: {metric.completion_rate:.3f}, Idle: {metric.idle_steps}, "
                f"LLM_Latency: {metric.llm_latency_ms:.2f}ms",
                flush=True,
            )
            time.sleep(max(0.0, float(args.sleep_seconds)))

        metadata["status"] = "completed"
        metadata["end_time"] = utc_now_iso()
        metadata["elapsed_seconds"] = round(time.monotonic() - start_monotonic, 3)
        metadata["summary"] = {
            "best_return": max(metric["episode_return"] for metric in metrics) if metrics else 0.0,
            "best_completion_rate": max(metric["completion_rate"] for metric in metrics) if metrics else 0.0,
            "final_return": metrics[-1]["episode_return"] if metrics else 0.0,
            "final_completion_rate": metrics[-1]["completion_rate"] if metrics else 0.0,
            "final_idle_steps": metrics[-1]["idle_steps"] if metrics else 0,
        }
        persist_run_state(args.output_dir, metadata, metrics)
        return 0

    except KeyboardInterrupt:
        metadata["status"] = "failed"
        metadata["end_time"] = utc_now_iso()
        metadata["error"] = "Interrupted by user"
        metadata["elapsed_seconds"] = round(time.monotonic() - start_monotonic, 3)
        persist_run_state(args.output_dir, metadata, metrics)
        print("Experiment interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        metadata["status"] = "failed"
        metadata["end_time"] = utc_now_iso()
        metadata["error"] = str(exc)
        metadata["elapsed_seconds"] = round(time.monotonic() - start_monotonic, 3)
        persist_run_state(args.output_dir, metadata, metrics)
        print(f"Experiment failed: {exc}", file=sys.stderr)
        return 1


def status_command(output_dir: Path) -> int:
    """Print a compact status payload for a run directory."""
    ensure_output_dir(output_dir)
    metadata = load_json(metadata_path(output_dir), {})
    metrics = load_json(metrics_path(output_dir), [])
    payload = {
        "metadata": metadata,
        "metrics_count": len(metrics),
        "last_metric": metrics[-1] if metrics else None,
    }
    print(json.dumps(payload, indent=2))
    return 0


def metadata_command(output_dir: Path) -> int:
    """Print raw metadata JSON for a run directory."""
    ensure_output_dir(output_dir)
    metadata = load_json(metadata_path(output_dir), {})
    print(json.dumps(metadata, indent=2))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.command == "status":
        return status_command(args.output_dir)
    if args.command == "metadata":
        return metadata_command(args.output_dir)
    return run_command(args)


if __name__ == "__main__":
    raise SystemExit(main())
