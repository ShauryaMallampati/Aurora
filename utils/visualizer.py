"""
Visualization stuff.
Draws the fire, drones, and stats.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from typing import Iterable, Optional, List
import matplotlib.patches as patches

try:
    from ..env.fire_sim import FireSim
    from ..agents.drone_agent import DroneAgent
except ImportError:
    from env.fire_sim import FireSim
    from agents.drone_agent import DroneAgent


def render(sim: FireSim, drones: Iterable[DroneAgent] = (), step: Optional[int] = None,
           save_path: Optional[str] = None, show_weather: bool = True) -> None:
    """
    Draws the map state.
    Red fuel, Green trees, Blue water, you get it.
    """
    terrain = sim.terrain
    fire = sim.fire_state
    
    # Build an enhanced image array where each cell is an RGB triple
    img = np.zeros((terrain.shape[0], terrain.shape[1], 3), dtype=np.float32)
    
    # Base terrain colours with enhanced contrast
    # white for empty (0)
    img[terrain == 0] = np.array([0.95, 0.95, 0.95])
    # forest (1) initially green
    img[terrain == 1] = np.array([0.0, 0.7, 0.0])
    # road (2) grey
    img[terrain == 2] = np.array([0.4, 0.4, 0.4])
    # water (3) blue
    img[terrain == 3] = np.array([0.2, 0.4, 0.8])
    
    # Overlay fire states with enhanced colors
    # burning cells become bright red
    burning = fire == 1
    img[burning] = np.array([1.0, 0.1, 0.1])
    # burnt cells become dark gray
    burnt = fire == 2
    img[burnt] = np.array([0.2, 0.2, 0.2])
    
    # Create the figure with enhanced size
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(img, interpolation='none', origin='lower')
    
    # Plot drones with enhanced information
    drone_colors = ['yellow', 'orange', 'cyan', 'magenta', 'lime']
    for i, drone in enumerate(drones):
        r, c = drone.position
        
        # Choose color based on agent status
        if not drone.is_active:
            color = 'red'
        else:
            color = drone_colors[i % len(drone_colors)]
        
        # Plot drone position
        ax.scatter(c, r, color=color, marker='o', s=100, edgecolors='k', linewidths=2, zorder=10)
        
        # Add agent ID
        ax.text(c + 0.3, r + 0.3, drone.agent_id, fontsize=8, color='black', 
               weight='bold', bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        
        # Add battery indicator
        battery_color = get_battery_color(drone.battery_percentage)
        battery_x = c - 0.4
        battery_y = r - 0.4
        battery_rect = patches.Rectangle((battery_x, battery_y), 0.8, 0.1, 
                                       linewidth=1, edgecolor='black', 
                                       facecolor=battery_color, alpha=0.8)
        ax.add_patch(battery_rect)
        
        # Add water indicator
        water_color = get_water_color(drone.water_percentage)
        water_x = c - 0.4
        water_y = r - 0.6
        water_rect = patches.Rectangle((water_x, water_y), 0.8, 0.1, 
                                     linewidth=1, edgecolor='black', 
                                     facecolor=water_color, alpha=0.8)
        ax.add_patch(water_rect)
        
        # Add fault indicators
        if drone.faults:
            fault_x = c + 0.4
            fault_y = r - 0.4
            ax.text(fault_x, fault_y, '⚠', fontsize=12, color='red', weight='bold')
    
    # Draw communication links between agents
    draw_communication_links(ax, drones, sim)
    
    # Configure axes
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Enhanced title with weather information
    title = f"AURORA Enhanced Simulation – Step {step}" if step is not None else "AURORA Enhanced Simulation"
    if show_weather:
        weather_info = sim.get_weather_info()
        title += f"\nWind: {weather_info['wind_direction']} (intensity: {weather_info['wind_intensity']:.1f}) | "
        title += f"Temp: {weather_info['temperature']:.1f}°C | Humidity: {weather_info['humidity']*100:.0f}%"
    
    ax.set_title(title, fontsize=12, pad=20)
    
    # Add legend
    add_legend(ax)
    
    # Save or show figure
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()


def get_battery_color(battery_percentage: float) -> str:
    """Get color for battery level indicator."""
    if battery_percentage > 70:
        return 'green'
    elif battery_percentage > 30:
        return 'yellow'
    else:
        return 'red'


def get_water_color(water_percentage: float) -> str:
    """Get color for water level indicator."""
    if water_percentage > 70:
        return 'blue'
    elif water_percentage > 30:
        return 'cyan'
    else:
        return 'orange'


def draw_communication_links(ax, drones: Iterable[DroneAgent], sim: FireSim) -> None:
    """Draw communication links between agents within range."""
    drone_list = list(drones)
    
    for i, drone1 in enumerate(drone_list):
        for j, drone2 in enumerate(drone_list[i+1:], i+1):
            # Calculate distance
            r1, c1 = drone1.position
            r2, c2 = drone2.position
            distance = abs(r1 - r2) + abs(c1 - c2)  # Manhattan distance
            
            # Draw link if within communication range
            if distance <= drone1.communication_range:
                # Use different line styles for different ranges
                if distance <= 3:
                    linestyle = '-'
                    linewidth = 2
                    alpha = 0.8
                elif distance <= 6:
                    linestyle = '--'
                    linewidth = 1.5
                    alpha = 0.6
                else:
                    linestyle = ':'
                    linewidth = 1
                    alpha = 0.4
                
                ax.plot([c1, c2], [r1, r2], color='blue', linestyle=linestyle, 
                       linewidth=linewidth, alpha=alpha, zorder=5)


def add_legend(ax) -> None:
    """Add a legend showing what the colors mean."""
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', 
                  markersize=10, label='Forest'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                  markersize=10, label='Burning'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                  markersize=10, label='Burnt'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
                  markersize=10, label='Water'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='darkgray', 
                  markersize=10, label='Road'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow', 
                  markersize=10, label='Drone (Active)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                  markersize=10, label='Drone (Inactive)'),
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))


def create_animation_frames(sim: FireSim, drones: List[DroneAgent], 
                          steps: int, output_dir: str = "results") -> None:
    """Create a sequence of frames for animation."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    for step in range(steps):
        frame_path = os.path.join(output_dir, f'animation_frame_{step:04d}.png')
        render(sim, drones, step=step, save_path=frame_path)
        
        # Advance simulation
        for drone in drones:
            # Simple heuristic action for animation
            action = 0  # stay
            if step % 3 == 0:  # Move every 3 steps
                action = np.random.randint(1, 5)  # Random movement
            drone.act(action, sim, drones)
        
        sim.step()
        
        if not sim.is_fire_active():
            break


def render_3d_elevation(sim: FireSim, drones: Iterable[DroneAgent] = (), 
                       step: Optional[int] = None, save_path: Optional[str] = None) -> None:
    """Render a 3D elevation view of the terrain and fire."""
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Create coordinate grids
    x, y = np.meshgrid(range(sim.grid_size[1]), range(sim.grid_size[0]))
    z = sim.elevation
    
    # Create color map based on terrain and fire
    colors = np.zeros((sim.grid_size[0], sim.grid_size[1], 4))
    
    for i in range(sim.grid_size[0]):
        for j in range(sim.grid_size[1]):
            if sim.terrain[i, j] == 1:  # Forest
                if sim.fire_state[i, j] == 1:  # Burning
                    colors[i, j] = [1, 0, 0, 0.8]  # Red
                elif sim.fire_state[i, j] == 2:  # Burnt
                    colors[i, j] = [0.2, 0.2, 0.2, 0.8]  # Dark gray
                else:
                    colors[i, j] = [0, 0.7, 0, 0.8]  # Green
            elif sim.terrain[i, j] == 2:  # Road
                colors[i, j] = [0.4, 0.4, 0.4, 0.8]  # Gray
            elif sim.terrain[i, j] == 3:  # Water
                colors[i, j] = [0.2, 0.4, 0.8, 0.8]  # Blue
            else:  # Empty
                colors[i, j] = [0.95, 0.95, 0.95, 0.8]  # Light gray
    
    # Plot 3D surface
    surf = ax.plot_surface(x, y, z, facecolors=colors, alpha=0.8)
    
    # Plot drones
    for i, drone in enumerate(drones):
        r, c = drone.position
        ax.scatter(c, r, sim.elevation[r, c] + 5, 
                  color='yellow', s=100, edgecolors='black', linewidth=2)
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Elevation (m)')
    ax.set_title(f'AURORA 3D Elevation View - Step {step}' if step is not None else 'AURORA 3D Elevation View')
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()