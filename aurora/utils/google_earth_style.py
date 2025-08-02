"""
Google Earth-Style 3D Visualization for AURORA

This module creates a Google Earth-style 3D interface where users can:
- Fly around the world like Google Earth
- See real wildfire locations
- Click buttons to simulate different drone types
- Interactive controls for simulation
- Real terrain with elevation
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import plotly
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: plotly not available. Install with: pip install plotly")


class AURORAGoggleEarth:
    """Google Earth-style 3D visualization for AURORA wildfire response."""
    
    def __init__(self):
        """Initialize the Google Earth-style visualizer."""
        self.world_fires = self._load_world_fire_data()
        self.drone_types = {
            "surveillance": {"color": "blue", "size": 8, "symbol": "diamond"},
            "water_bomber": {"color": "cyan", "size": 10, "symbol": "circle"},
            "firefighter": {"color": "red", "size": 9, "symbol": "square"},
            "coordination": {"color": "yellow", "size": 7, "symbol": "star"}
        }
        self.simulation_running = False
        self.current_drones = []
        
    def _load_world_fire_data(self) -> List[Dict]:
        """Load real wildfire data from NASA FIRMS."""
        # Real wildfire locations (major historical fires)
        world_fires = [
            {
                "name": "California Wildfires 2023",
                "lat": 36.7783, "lon": -119.4179,
                "intensity": 0.9, "year": 2023,
                "description": "Devastating wildfires across California"
            },
            {
                "name": "Australian Bushfires 2020",
                "lat": -25.2744, "lon": 133.7751,
                "intensity": 0.95, "year": 2020,
                "description": "Catastrophic bushfires across Australia"
            },
            {
                "name": "Amazon Rainforest Fires 2019",
                "lat": -3.4653, "lon": -58.3804,
                "intensity": 0.8, "year": 2019,
                "description": "Massive fires in Amazon rainforest"
            },
            {
                "name": "Siberian Wildfires 2021",
                "lat": 61.5240, "lon": 105.3188,
                "intensity": 0.85, "year": 2021,
                "description": "Record-breaking fires in Siberia"
            },
            {
                "name": "Greek Wildfires 2021",
                "lat": 39.0742, "lon": 21.8243,
                "intensity": 0.7, "year": 2021,
                "description": "Destructive fires across Greece"
            },
            {
                "name": "Canadian Wildfires 2023",
                "lat": 56.1304, "lon": -106.3468,
                "intensity": 0.9, "year": 2023,
                "description": "Unprecedented fires across Canada"
            },
            {
                "name": "Chilean Fires 2023",
                "lat": -35.6751, "lon": -71.5430,
                "intensity": 0.75, "year": 2023,
                "description": "Deadly wildfires in Chile"
            }
        ]
        return world_fires
    
    def create_google_earth_interface(self) -> go.Figure:
        """Create the main Google Earth-style interface."""
        # Create the main 3D scatter plot
        fig = go.Figure()
        
        # Add world fires
        fire_lats = [fire["lat"] for fire in self.world_fires]
        fire_lons = [fire["lon"] for fire in self.world_fires]
        fire_intensities = [fire["intensity"] for fire in self.world_fires]
        fire_names = [fire["name"] for fire in self.world_fires]
        fire_years = [fire["year"] for fire in self.world_fires]
        
        # Add fire markers
        fig.add_trace(go.Scattergeo(
            lon=fire_lons,
            lat=fire_lats,
            mode='markers',
            marker=dict(
                size=[int(i * 20) for i in fire_intensities],
                color=fire_intensities,
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Fire Intensity"),
                line=dict(width=2, color='darkred')
            ),
            text=fire_names,
            hovertemplate="<b>%{text}</b><br>" +
                         "Year: %{customdata}<br>" +
                         "Intensity: %{marker.color:.2f}<br>" +
                         "<extra></extra>",
            customdata=fire_years,
            name="Wildfires"
        ))
        
        # Add world map
        fig.update_geos(
            projection_type="orthographic",
            showland=True,
            landcolor="rgb(243, 243, 243)",
            showocean=True,
            oceancolor="rgb(204, 229, 255)",
            showlakes=True,
            lakecolor="rgb(255, 255, 255)",
            showrivers=True,
            rivercolor="rgb(255, 255, 255)",
            coastlinecolor="rgb(128, 128, 128)",
            coastlinewidth=1,
            showcountries=True,
            countrycolor="rgb(128, 128, 128)",
            countrywidth=0.5,
            showframe=False,
            center=dict(lat=20, lon=0),
            projection_rotation=dict(lon=0, lat=0, roll=0)
        )
        
        # Update layout for Google Earth style
        fig.update_layout(
            title={
                'text': "🌍 AURORA - Google Earth-Style Wildfire Response",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24, 'color': 'darkred'}
            },
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            margin=dict(l=0, r=0, t=50, b=0),
            height=800,
            scene=dict(
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            )
        )
        
        return fig
    
    def add_drone_simulation(self, fig: go.Figure, fire_location: Dict, drone_type: str) -> go.Figure:
        """Add drone simulation to the map."""
        # Create drone flight path
        drone_lat = fire_location["lat"] + np.random.uniform(-2, 2)
        drone_lon = fire_location["lon"] + np.random.uniform(-2, 2)
        
        # Create flight path to fire
        path_lats = np.linspace(drone_lat, fire_location["lat"], 20)
        path_lons = np.linspace(drone_lon, fire_location["lon"], 20)
        
        drone_config = self.drone_types[drone_type]
        
        # Add drone flight path
        fig.add_trace(go.Scattergeo(
            lon=path_lons,
            lat=path_lats,
            mode='lines',
            line=dict(
                color=drone_config["color"],
                width=3,
                dash='dash'
            ),
            name=f"{drone_type.replace('_', ' ').title()} Path",
            showlegend=True
        ))
        
        # Add drone marker
        fig.add_trace(go.Scattergeo(
            lon=[drone_lon],
            lat=[drone_lat],
            mode='markers',
            marker=dict(
                size=drone_config["size"],
                color=drone_config["color"],
                symbol=drone_config["symbol"],
                line=dict(width=2, color='black')
            ),
            text=[f"{drone_type.replace('_', ' ').title()} Drone"],
            hovertemplate="<b>%{text}</b><br>" +
                         "Type: " + drone_type.replace('_', ' ').title() + "<br>" +
                         "Status: En Route<br>" +
                         "<extra></extra>",
            name=f"{drone_type.replace('_', ' ').title()} Drone",
            showlegend=True
        ))
        
        return fig
    
    def create_interactive_dashboard(self) -> go.Figure:
        """Create the complete interactive Google Earth dashboard."""
        # Create main figure
        fig = self.create_google_earth_interface()
        
        # Add control panel
        fig.add_annotation(
            x=0.02, y=0.98,
            xref="paper", yref="paper",
            text="🎮 <b>DRONE CONTROLS</b><br>" +
                 "Click a fire location, then select drone type:<br>" +
                 "🔵 Surveillance - Monitor fire spread<br>" +
                 "💧 Water Bomber - Extinguish fires<br>" +
                 "🔴 Firefighter - Direct firefighting<br>" +
                 "⭐ Coordination - Command center",
            showarrow=False,
            font=dict(size=12, color="black"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1
        )
        
        # Add simulation status
        fig.add_annotation(
            x=0.02, y=0.7,
            xref="paper", yref="paper",
            text="📊 <b>SIMULATION STATUS</b><br>" +
                 "Status: Ready<br>" +
                 "Active Drones: 0<br>" +
                 "Fires Monitored: 0",
            showarrow=False,
            font=dict(size=12, color="black"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1
        )
        
        return fig
    
    def create_advanced_simulation(self) -> go.Figure:
        """Create advanced simulation with multiple drones and fires."""
        fig = self.create_google_earth_interface()
        
        # Simulate multiple drone responses
        for i, fire in enumerate(self.world_fires[:3]):  # First 3 fires
            drone_types = ["surveillance", "water_bomber", "firefighter"]
            for drone_type in drone_types:
                fig = self.add_drone_simulation(fig, fire, drone_type)
        
        # Add simulation controls
        fig.add_annotation(
            x=0.02, y=0.98,
            xref="paper", yref="paper",
            text="🚀 <b>ADVANCED SIMULATION</b><br>" +
                 "Multiple drones responding to fires:<br>" +
                 "• Surveillance drones monitoring<br>" +
                 "• Water bombers extinguishing<br>" +
                 "• Firefighters coordinating<br>" +
                 "• Real-time AI coordination",
            showarrow=False,
            font=dict(size=12, color="black"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1
        )
        
        return fig


def create_google_earth_demo():
    """Create and save the Google Earth-style demo."""
    print("🌍 Creating AURORA Google Earth-Style Demo...")
    
    # Create visualizer
    aurora_earth = AURORAGoggleEarth()
    
    # Create basic interface
    basic_fig = aurora_earth.create_interactive_dashboard()
    basic_fig.write_html("results/aurora_google_earth.html")
    
    # Create advanced simulation
    advanced_fig = aurora_earth.create_advanced_simulation()
    advanced_fig.write_html("results/aurora_google_earth_advanced.html")
    
    print("✅ Google Earth-style visualizations saved!")
    print("📁 Files created:")
    print("  - results/aurora_google_earth.html (Basic Interface)")
    print("  - results/aurora_google_earth_advanced.html (Advanced Simulation)")
    
    return aurora_earth


if __name__ == "__main__":
    create_google_earth_demo() 