"""
3D Interactive Visualizer for AURORA

This module provides 3D interactive visualization capabilities for the AURORA wildfire simulation.
Features include:
- 3D terrain visualization with elevation
- Interactive fire spread visualization
- Drone movement tracking
- Real-time weather effects
- Interactive controls for exploration
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

try:
    import plotly
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: plotly not available. Install with: pip install plotly")


class AURORA3DVisualizer:
    """3D interactive visualizer for AURORA wildfire simulation."""
    
    def __init__(self, map_size: int = 50):
        """
        Initialize the 3D visualizer.
        
        Args:
            map_size: Size of the simulation map
        """
        self.map_size = map_size
        self.fig = None
        self.terrain_data = None
        self.fire_history = []
        self.drone_history = []
        self.weather_history = []
        
        # Color schemes
        self.colors = {
            'terrain': {
                'forest': '#228B22',      # Forest green
                'grass': '#90EE90',       # Light green
                'mountain': '#8B4513',    # Brown
                'water': '#4169E1',       # Blue
                'road': '#696969'         # Gray
            },
            'fire': {
                'burning': '#FF4500',     # Orange red
                'burnt': '#8B0000',       # Dark red
                'smoke': '#C0C0C0'        # Silver
            },
            'drones': {
                'active': '#00FF00',      # Green
                'recharging': '#FFFF00',  # Yellow
                'fault': '#FF0000'        # Red
            }
        }
    
    def create_3d_terrain(self, terrain: np.ndarray, elevation: np.ndarray) -> go.Figure:
        """
        Create a 3D terrain visualization.
        
        Args:
            terrain: Terrain type array
            elevation: Elevation data array
            
        Returns:
            Plotly figure with 3D terrain
        """
        if not PLOTLY_AVAILABLE:
            print("⚠️  Plotly not available - using matplotlib fallback")
            return self._create_matplotlib_3d(terrain, elevation)
        
        # Create coordinate grids
        x, y = np.meshgrid(np.arange(self.map_size), np.arange(self.map_size))
        z = elevation
        
        # Create terrain colors based on terrain type
        terrain_colors = np.zeros((self.map_size, self.map_size, 3))
        
        for i in range(self.map_size):
            for j in range(self.map_size):
                terrain_type = terrain[i, j]
                if terrain_type == 1:  # Forest
                    terrain_colors[i, j] = [0.133, 0.545, 0.133]  # Forest green
                elif terrain_type == 2:  # Road
                    terrain_colors[i, j] = [0.412, 0.412, 0.412]  # Gray
                elif terrain_type == 3:  # Water
                    terrain_colors[i, j] = [0.255, 0.412, 0.882]  # Blue
                else:  # Grass
                    terrain_colors[i, j] = [0.565, 0.933, 0.565]  # Light green
        
        # Create 3D surface plot
        fig = go.Figure(data=[
            go.Surface(
                x=x, y=y, z=z,
                surfacecolor=terrain_colors,
                colorscale='Viridis',
                showscale=False,
                name='Terrain'
            )
        ])
        
        # Update layout for better 3D experience
        fig.update_layout(
            title='AURORA 3D Terrain Visualization',
            scene=dict(
                xaxis_title='X Coordinate',
                yaxis_title='Y Coordinate',
                zaxis_title='Elevation (m)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            width=800,
            height=600
        )
        
        return fig
    
    def add_fire_layer(self, fig: go.Figure, fire_state: np.ndarray, step: int) -> go.Figure:
        """
        Add fire visualization layer to 3D plot.
        
        Args:
            fig: Existing plotly figure
            fire_state: Current fire state array
            step: Current simulation step
            
        Returns:
            Updated figure with fire layer
        """
        if not PLOTLY_AVAILABLE:
            return fig
        
        # Find fire locations
        fire_locations = np.where(fire_state > 0)
        
        if len(fire_locations[0]) > 0:
            # Create fire scatter plot
            fire_scatter = go.Scatter3d(
                x=fire_locations[1],
                y=fire_locations[0],
                z=np.zeros_like(fire_locations[0]),  # Fire at ground level
                mode='markers',
                marker=dict(
                    size=5,
                    color='red',
                    opacity=0.8
                ),
                name=f'Fire (Step {step})'
            )
            
            fig.add_trace(fire_scatter)
        
        return fig
    
    def add_drone_layer(self, fig: go.Figure, drone_positions: List[Tuple[int, int]], 
                       drone_statuses: List[Dict], step: int) -> go.Figure:
        """
        Add drone visualization layer to 3D plot.
        
        Args:
            fig: Existing plotly figure
            drone_positions: List of drone positions
            drone_statuses: List of drone status dictionaries
            step: Current simulation step
            
        Returns:
            Updated figure with drone layer
        """
        if not PLOTLY_AVAILABLE:
            return fig
        
        for i, (pos, status) in enumerate(zip(drone_positions, drone_statuses)):
            x, y = pos
            z = 10  # Drones fly above terrain
            
            # Determine drone color based on status
            if status.get("is_active", True):
                if status.get("battery_percentage", 100) < 30:
                    color = 'yellow'  # Low battery
                else:
                    color = 'green'   # Active
            else:
                color = 'red'         # Fault
            
            # Create drone scatter plot
            drone_scatter = go.Scatter3d(
                x=[x],
                y=[y],
                z=[z],
                mode='markers',
                marker=dict(
                    size=8,
                    color=color,
                    symbol='diamond',
                    opacity=0.9
                ),
                name=f'Drone {i} (Step {step})',
                text=f"Battery: {status.get('battery_percentage', 100)}%<br>Water: {status.get('water_percentage', 100)}%",
                hovertemplate='<b>%{text}</b><extra></extra>'
            )
            
            fig.add_trace(drone_scatter)
        
        return fig
    
    def create_interactive_dashboard(self, terrain: np.ndarray, elevation: np.ndarray, 
                                   fire_history: List[np.ndarray], drone_history: List[List[Tuple[int, int]]],
                                   weather_history: List[Dict]) -> go.Figure:
        """
        Create an interactive 3D dashboard with multiple views.
        
        Args:
            terrain: Terrain type array
            elevation: Elevation data array
            fire_history: History of fire states
            drone_history: History of drone positions
            weather_history: History of weather conditions
            
        Returns:
            Interactive dashboard figure
        """
        if not PLOTLY_AVAILABLE:
            print("⚠️  Plotly not available - using matplotlib fallback")
            return self._create_matplotlib_dashboard(terrain, elevation, fire_history, drone_history, weather_history)
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'surface'}, {'type': 'scatter3d'}],
                   [{'type': 'scatter'}, {'type': 'bar'}]],
            subplot_titles=('3D Terrain & Fire', 'Drone Trajectories', 'Fire Coverage Over Time', 'Weather Conditions')
        )
        
        # 1. 3D Terrain & Fire (Surface plot)
        x, y = np.meshgrid(np.arange(self.map_size), np.arange(self.map_size))
        z = elevation
        
        fig.add_trace(
            go.Surface(x=x, y=y, z=z, colorscale='Viridis', showscale=False, name='Terrain'),
            row=1, col=1
        )
        
        # Add final fire state
        if fire_history:
            final_fire = fire_history[-1]
            fire_locations = np.where(final_fire > 0)
            if len(fire_locations[0]) > 0:
                fig.add_trace(
                    go.Scatter3d(
                        x=fire_locations[1],
                        y=fire_locations[0],
                        z=np.zeros_like(fire_locations[0]),
                        mode='markers',
                        marker=dict(size=3, color='red', opacity=0.8),
                        name='Fire'
                    ),
                    row=1, col=1
                )
        
        # 2. Drone Trajectories (3D Scatter)
        for i in range(len(drone_history[0]) if drone_history else 0):
            drone_x = [pos[i][0] for pos in drone_history if i < len(pos)]
            drone_y = [pos[i][1] for pos in drone_history if i < len(pos)]
            drone_z = [10] * len(drone_x)  # Constant height
            
            fig.add_trace(
                go.Scatter3d(
                    x=drone_x, y=drone_y, z=drone_z,
                    mode='lines+markers',
                    name=f'Drone {i}',
                    line=dict(width=3),
                    marker=dict(size=4)
                ),
                row=1, col=2
            )
        
        # 3. Fire Coverage Over Time (2D Scatter)
        if fire_history:
            steps = list(range(len(fire_history)))
            coverage = [np.sum(fire > 0) / fire.size * 100 for fire in fire_history]
            
            fig.add_trace(
                go.Scatter(
                    x=steps, y=coverage,
                    mode='lines+markers',
                    name='Fire Coverage %',
                    line=dict(color='red', width=3)
                ),
                row=2, col=1
            )
        
        # 4. Weather Conditions (Bar chart)
        if weather_history:
            steps = list(range(len(weather_history)))
            temperatures = [w.get('temperature', 0) for w in weather_history]
            wind_speeds = [w.get('wind_speed', 0) for w in weather_history]
            
            fig.add_trace(
                go.Bar(x=steps, y=temperatures, name='Temperature (°F)', marker_color='orange'),
                row=2, col=2
            )
            
            fig.add_trace(
                go.Bar(x=steps, y=wind_speeds, name='Wind Speed (mph)', marker_color='blue'),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title='AURORA Interactive 3D Dashboard',
            height=800,
            showlegend=True
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Simulation Step", row=2, col=1)
        fig.update_yaxes(title_text="Fire Coverage (%)", row=2, col=1)
        fig.update_xaxes(title_text="Simulation Step", row=2, col=2)
        fig.update_yaxes(title_text="Value", row=2, col=2)
        
        return fig
    
    def create_animation_frames(self, terrain: np.ndarray, elevation: np.ndarray,
                              fire_history: List[np.ndarray], drone_history: List[List[Tuple[int, int]]],
                              weather_history: List[Dict]) -> go.Figure:
        """
        Create an animated 3D visualization.
        
        Args:
            terrain: Terrain type array
            elevation: Elevation data array
            fire_history: History of fire states
            drone_history: History of drone positions
            weather_history: History of weather conditions
            
        Returns:
            Animated figure
        """
        if not PLOTLY_AVAILABLE:
            print("⚠️  Plotly not available - animation not supported")
            return None
        
        # Create base figure
        fig = go.Figure()
        
        # Add terrain
        x, y = np.meshgrid(np.arange(self.map_size), np.arange(self.map_size))
        z = elevation
        
        fig.add_trace(
            go.Surface(
                x=x, y=y, z=z,
                colorscale='Viridis',
                showscale=False,
                name='Terrain'
            )
        )
        
        # Create frames for animation
        frames = []
        
        for step in range(len(fire_history)):
            frame_data = [
                go.Surface(x=x, y=y, z=z, colorscale='Viridis', showscale=False, name='Terrain')
            ]
            
            # Add fire for this step
            fire_state = fire_history[step]
            fire_locations = np.where(fire_state > 0)
            if len(fire_locations[0]) > 0:
                frame_data.append(
                    go.Scatter3d(
                        x=fire_locations[1],
                        y=fire_locations[0],
                        z=np.zeros_like(fire_locations[0]),
                        mode='markers',
                        marker=dict(size=5, color='red', opacity=0.8),
                        name='Fire'
                    )
                )
            
            # Add drones for this step
            if step < len(drone_history):
                drone_positions = drone_history[step]
                for i, pos in enumerate(drone_positions):
                    frame_data.append(
                        go.Scatter3d(
                            x=[pos[0]],
                            y=[pos[1]],
                            z=[10],
                            mode='markers',
                            marker=dict(size=8, color='green', symbol='diamond'),
                            name=f'Drone {i}'
                        )
                    )
            
            frames.append(go.Frame(data=frame_data, name=f'Step {step}'))
        
        fig.frames = frames
        
        # Update layout
        fig.update_layout(
            title='AURORA 3D Animation',
            scene=dict(
                xaxis_title='X Coordinate',
                yaxis_title='Y Coordinate',
                zaxis_title='Elevation (m)',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'buttons': [
                    {
                        'label': 'Play',
                        'method': 'animate',
                        'args': [None, {'frame': {'duration': 500, 'redraw': True}, 'fromcurrent': True}]
                    },
                    {
                        'label': 'Pause',
                        'method': 'animate',
                        'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate', 'transition': {'duration': 0}}]
                    }
                ]
            }],
            sliders=[{
                'steps': [{'method': 'animate', 'args': [[f'Step {i}'], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 0}}], 'label': f'Step {i}'} for i in range(len(fire_history))],
                'active': 0,
                'currentvalue': {'prefix': 'Step: '},
                'len': 0.9,
                'x': 0.1,
                'xanchor': 'left',
                'y': 0,
                'yanchor': 'top'
            }]
        )
        
        return fig
    
    def _create_matplotlib_3d(self, terrain: np.ndarray, elevation: np.ndarray):
        """Fallback matplotlib 3D visualization."""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        x, y = np.meshgrid(np.arange(self.map_size), np.arange(self.map_size))
        z = elevation
        
        # Create surface plot
        surf = ax.plot_surface(x, y, z, cmap='terrain', alpha=0.8)
        
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_zlabel('Elevation (m)')
        ax.set_title('AURORA 3D Terrain Visualization')
        
        return fig
    
    def _create_matplotlib_dashboard(self, terrain: np.ndarray, elevation: np.ndarray,
                                   fire_history: List[np.ndarray], drone_history: List[List[Tuple[int, int]]],
                                   weather_history: List[Dict]):
        """Fallback matplotlib dashboard."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 3D Terrain
        ax1_3d = fig.add_subplot(2, 2, 1, projection='3d')
        x, y = np.meshgrid(np.arange(self.map_size), np.arange(self.map_size))
        z = elevation
        ax1_3d.plot_surface(x, y, z, cmap='terrain', alpha=0.8)
        ax1_3d.set_title('3D Terrain')
        
        # 2. Drone Trajectories (2D projection)
        if drone_history:
            for i in range(len(drone_history[0])):
                drone_x = [pos[i][0] for pos in drone_history if i < len(pos)]
                drone_y = [pos[i][1] for pos in drone_history if i < len(pos)]
                ax2.plot(drone_x, drone_y, marker='o', label=f'Drone {i}')
        ax2.set_title('Drone Trajectories')
        ax2.legend()
        
        # 3. Fire Coverage
        if fire_history:
            steps = list(range(len(fire_history)))
            coverage = [np.sum(fire > 0) / fire.size * 100 for fire in fire_history]
            ax3.plot(steps, coverage, 'r-', linewidth=2)
        ax3.set_title('Fire Coverage Over Time')
        ax3.set_xlabel('Step')
        ax3.set_ylabel('Coverage (%)')
        
        # 4. Weather
        if weather_history:
            steps = list(range(len(weather_history)))
            temperatures = [w.get('temperature', 0) for w in weather_history]
            ax4.bar(steps, temperatures, color='orange', alpha=0.7)
        ax4.set_title('Temperature Over Time')
        ax4.set_xlabel('Step')
        ax4.set_ylabel('Temperature (°F)')
        
        plt.tight_layout()
        return fig
    
    def save_3d_visualization(self, fig, filename: str, format: str = 'html'):
        """
        Save 3D visualization to file.
        
        Args:
            fig: Plotly figure
            filename: Output filename
            format: Output format ('html', 'png', 'jpg')
        """
        if PLOTLY_AVAILABLE and hasattr(fig, 'write_html'):
            if format == 'html':
                fig.write_html(filename)
            else:
                fig.write_image(filename)
            print(f"✅ 3D visualization saved to {filename}")
        else:
            if hasattr(fig, 'savefig'):
                fig.savefig(filename, dpi=300, bbox_inches='tight')
                print(f"✅ 3D visualization saved to {filename}")
            else:
                print("❌ Could not save visualization")


def create_interactive_demo():
    """Create an interactive demo of the 3D visualizer."""
    print("🚀 Creating AURORA 3D Interactive Demo...")
    
    # Create sample data
    map_size = 30
    terrain = np.random.choice([1, 1, 1, 2, 3], size=(map_size, map_size), p=[0.7, 0.1, 0.1, 0.05, 0.05])
    elevation = np.random.rand(map_size, map_size) * 100
    
    # Create fire history
    fire_history = []
    fire_state = np.zeros((map_size, map_size))
    fire_state[map_size//2, map_size//2] = 1  # Start fire in center
    
    for step in range(20):
        fire_history.append(fire_state.copy())
        # Simple fire spread
        new_state = fire_state.copy()
        for i in range(map_size):
            for j in range(map_size):
                if fire_state[i, j] == 1:
                    for di in [-1, 0, 1]:
                        for dj in [-1, 0, 1]:
                            ni, nj = i + di, j + dj
                            if 0 <= ni < map_size and 0 <= nj < map_size:
                                if terrain[ni, nj] == 1 and fire_state[ni, nj] == 0:
                                    new_state[ni, nj] = 1
        fire_state = new_state
    
    # Create drone history
    drone_history = []
    drone_positions = [(5, 5), (map_size-5, 5), (map_size//2, map_size-5)]
    
    for step in range(20):
        # Simple drone movement
        new_positions = []
        for pos in drone_positions:
            x, y = pos
            # Move towards fire
            fire_center = (map_size//2, map_size//2)
            dx = 1 if fire_center[0] > x else -1 if fire_center[0] < x else 0
            dy = 1 if fire_center[1] > y else -1 if fire_center[1] < y else 0
            new_x = max(0, min(map_size-1, x + dx))
            new_y = max(0, min(map_size-1, y + dy))
            new_positions.append((new_x, new_y))
        drone_history.append(new_positions)
        drone_positions = new_positions
    
    # Create weather history
    weather_history = []
    for step in range(20):
        weather_history.append({
            'temperature': 80 + np.random.normal(0, 5),
            'wind_speed': 10 + np.random.normal(0, 3),
            'wind_direction': np.random.choice(['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW']),
            'humidity': 30 + np.random.normal(0, 10)
        })
    
    # Create visualizer
    visualizer = AURORA3DVisualizer(map_size)
    
    # Create interactive dashboard
    dashboard = visualizer.create_interactive_dashboard(
        terrain, elevation, fire_history, drone_history, weather_history
    )
    
    # Save dashboard
    visualizer.save_3d_visualization(dashboard, 'results/aurora_3d_dashboard.html', 'html')
    
    # Create animation
    animation = visualizer.create_animation_frames(
        terrain, elevation, fire_history, drone_history, weather_history
    )
    
    if animation:
        visualizer.save_3d_visualization(animation, 'results/aurora_3d_animation.html', 'html')
    
    print("✅ AURORA 3D Interactive Demo created!")
    print("📁 Files saved:")
    print("  - results/aurora_3d_dashboard.html (Interactive Dashboard)")
    print("  - results/aurora_3d_animation.html (3D Animation)")
    
    return dashboard, animation


if __name__ == "__main__":
    create_interactive_demo() 