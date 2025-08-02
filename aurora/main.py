"""
Entry point for running the AURORA wildfire simulation.

This script stitches together the terrain generator, fire simulator,
drone agents and visualiser to produce a simple step‑by‑step
simulation.  A number of drones are initialised at random positions
and controlled by a basic heuristic: each drone moves toward the
nearest burning cell and attempts to suppress fires when adjacent.

At each timestep the script prints the percentage of forest area
affected by fire and the number of drones that are able to act (i.e.
whose suppression cooldown is zero).  The visualiser is called to
produce a plot of the current state; these frames can be combined to
create an animation if desired.
"""

from __future__ import annotations

import os
import numpy as np
from typing import List, Tuple

try:
    from .env.fire_sim import FireSim
    from .agents.drone_agent import DroneAgent
    from .utils.visualizer import render
except ImportError:
    from env.fire_sim import FireSim
    from agents.drone_agent import DroneAgent
    from utils.visualizer import render


def nearest_burning_target(drone: DroneAgent, sim: FireSim) -> Tuple[int, int] | None:
    """Find the location of the nearest burning cell to the drone.

    Uses Manhattan distance to locate the closest burning cell in the
    environment.  Returns ``None`` if there are no burning cells.
    """
    burning_coords = np.argwhere(sim.fire_state == 1)
    if burning_coords.size == 0:
        return None
    pos = np.array(drone.position)
    distances = np.sum(np.abs(burning_coords - pos), axis=1)
    idx = int(np.argmin(distances))
    return tuple(int(x) for x in burning_coords[idx])


def heuristic_action(drone: DroneAgent, sim: FireSim) -> int:
    """Compute a simple heuristic action for the drone.

    If an adjacent burning cell exists and the drone is off cooldown,
    choose the suppress action.  Otherwise move one step toward the
    nearest burning cell using Manhattan distance.  If there are no
    burning cells the drone stays in place.
    """
    # If adjacent burning cell and can suppress
    if drone.cooldown == 0:
        r, c = drone.position
        for dr, dc, action in [(-1, 0, 1), (1, 0, 2), (0, -1, 3), (0, 1, 4)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < sim.grid_size[0] and 0 <= nc < sim.grid_size[1]:
                if sim.fire_state[nr, nc] == 1:
                    return 5  # suppress
    # Move towards nearest burning cell
    target = nearest_burning_target(drone, sim)
    if target is None:
        return 0  # no fire, stay
    tr, tc = target
    r, c = drone.position
    # Determine direction: prefer row movement then column
    if tr < r and r > 0:
        return 1  # up
    if tr > r and r < sim.grid_size[0] - 1:
        return 2  # down
    if tc < c and c > 0:
        return 3  # left
    if tc > c and c < sim.grid_size[1] - 1:
        return 4  # right
    return 0


def run_simulation(num_drones: int = 3, steps: int = 30, render_every: int = 1) -> None:
    """Run a wildfire simulation with a given number of drones.

    Args:
        num_drones: number of drone agents to deploy
        steps: number of time steps to simulate
        render_every: frequency (in steps) at which to render the state
    """
    # Ensure a terrain map exists
    terrain_path = os.path.join(os.path.dirname(__file__), 'data', 'terrain_map.npy')
    if not os.path.exists(terrain_path):
        try:
            from .data.generate_map import main as gen_map_main
        except ImportError:
            from data.generate_map import main as gen_map_main
        gen_map_main()
    sim = FireSim()
    # Create drones at random navigable positions
    drones: List[DroneAgent] = []
    navigable = np.where(sim.terrain != 3)
    available_positions = list(zip(navigable[0], navigable[1]))
    np.random.shuffle(available_positions)
    for i in range(num_drones):
        pos = available_positions[i % len(available_positions)]
        drones.append(DroneAgent(pos))
    # Track fire coverage over time
    coverage_history: List[float] = []
    for step_idx in range(steps):
        # Decide actions for each drone
        for drone in drones:
            act = heuristic_action(drone, sim)
            drone.act(act, sim)
        # Record metrics before advancing fire (so that suppression is counted)
        coverage = sim.get_fire_coverage() * 100.0
        active_drones = sum(1 for d in drones if d.cooldown == 0)
        print(f"Step {step_idx:2d}: fire coverage {coverage:.1f}% – active drones {active_drones}/{num_drones}")
        coverage_history.append(coverage)
        # Advance fire
        sim.step()
        # Render state if required
        if render_every > 0 and (step_idx % render_every == 0 or step_idx == steps - 1):
            # Save each frame into results folder
            output_dir = os.path.join(os.path.dirname(__file__), 'results')
            os.makedirs(output_dir, exist_ok=True)
            frame_path = os.path.join(output_dir, f'frame_{step_idx:03d}.png')
            render(sim, drones, step=step_idx, save_path=frame_path)
        if not sim.is_fire_active():
            # Early exit if all fires have been extinguished
            break
    # Save summary plot of fire coverage over time
    import matplotlib.pyplot as plt
    output_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots()
    ax.plot(coverage_history, marker='o')
    ax.set_xlabel('Step')
    ax.set_ylabel('Fire coverage (%)')
    ax.set_title('Fire coverage over time')
    fig.tight_layout()
    stats_path = os.path.join(output_dir, 'fire_stats.png')
    fig.savefig(stats_path)
    plt.close(fig)
    print(f"Saved fire coverage plot to {stats_path}")


def main() -> None:
    run_simulation()


if __name__ == '__main__':
    main()