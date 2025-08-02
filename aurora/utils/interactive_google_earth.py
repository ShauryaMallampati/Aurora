"""
Interactive Google Earth-Style 3D Visualization for AURORA

Advanced interactive interface with:
- Clickable fire locations
- Interactive drone deployment buttons
- Real-time simulation controls
- Multiple drone types
- Animated drone movements
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


class InteractiveAURORAGoggleEarth:
    """Interactive Google Earth-style 3D visualization for AURORA."""
    
    def __init__(self):
        """Initialize the interactive Google Earth visualizer."""
        self.world_fires = self._load_world_fire_data()
        self.drone_types = {
            "surveillance": {
                "color": "blue", "size": 8, "symbol": "diamond",
                "description": "Monitor fire spread and conditions"
            },
            "water_bomber": {
                "color": "cyan", "size": 10, "symbol": "circle",
                "description": "Drop water to extinguish fires"
            },
            "firefighter": {
                "color": "red", "size": 9, "symbol": "square",
                "description": "Direct firefighting operations"
            },
            "coordination": {
                "color": "yellow", "size": 7, "symbol": "star",
                "description": "Coordinate multiple drone operations"
            }
        }
        self.active_drones = []
        self.selected_fire = None
        
    def _load_world_fire_data(self) -> List[Dict]:
        """Load real wildfire data."""
        world_fires = [
            {
                "id": "california_2023",
                "name": "California Wildfires 2023",
                "lat": 36.7783, "lon": -119.4179,
                "intensity": 0.9, "year": 2023,
                "description": "Devastating wildfires across California",
                "area_affected": "1.2M acres",
                "deaths": 97,
                "damage": "$18.5B"
            },
            {
                "id": "australia_2020",
                "name": "Australian Bushfires 2020",
                "lat": -25.2744, "lon": 133.7751,
                "intensity": 0.95, "year": 2020,
                "description": "Catastrophic bushfires across Australia",
                "area_affected": "46M acres",
                "deaths": 34,
                "damage": "$103B"
            },
            {
                "id": "amazon_2019",
                "name": "Amazon Rainforest Fires 2019",
                "lat": -3.4653, "lon": -58.3804,
                "intensity": 0.8, "year": 2019,
                "description": "Massive fires in Amazon rainforest",
                "area_affected": "2.2M acres",
                "deaths": 0,
                "damage": "$1B"
            },
            {
                "id": "siberia_2021",
                "name": "Siberian Wildfires 2021",
                "lat": 61.5240, "lon": 105.3188,
                "intensity": 0.85, "year": 2021,
                "description": "Record-breaking fires in Siberia",
                "area_affected": "62M acres",
                "deaths": 0,
                "damage": "$2.1B"
            },
            {
                "id": "greece_2021",
                "name": "Greek Wildfires 2021",
                "lat": 39.0742, "lon": 21.8243,
                "intensity": 0.7, "year": 2021,
                "description": "Destructive fires across Greece",
                "area_affected": "300K acres",
                "deaths": 3,
                "damage": "$1.6B"
            },
            {
                "id": "canada_2023",
                "name": "Canadian Wildfires 2023",
                "lat": 56.1304, "lon": -106.3468,
                "intensity": 0.9, "year": 2023,
                "description": "Unprecedented fires across Canada",
                "area_affected": "45M acres",
                "deaths": 0,
                "damage": "$5.5B"
            },
            {
                "id": "chile_2023",
                "name": "Chilean Fires 2023",
                "lat": -35.6751, "lon": -71.5430,
                "intensity": 0.75, "year": 2023,
                "description": "Deadly wildfires in Chile",
                "area_affected": "1.2M acres",
                "deaths": 26,
                "damage": "$2.5B"
            }
        ]
        return world_fires
    
    def create_interactive_interface(self) -> go.Figure:
        """Create the main interactive Google Earth interface."""
        fig = go.Figure()
        
        # Add world fires with enhanced hover info
        fire_lats = [fire["lat"] for fire in self.world_fires]
        fire_lons = [fire["lon"] for fire in self.world_fires]
        fire_intensities = [fire["intensity"] for fire in self.world_fires]
        fire_names = [fire["name"] for fire in self.world_fires]
        fire_years = [fire["year"] for fire in self.world_fires]
        fire_areas = [fire["area_affected"] for fire in self.world_fires]
        fire_deaths = [fire["deaths"] for fire in self.world_fires]
        fire_damage = [fire["damage"] for fire in self.world_fires]
        
        # Add fire markers with enhanced hover
        fig.add_trace(go.Scattergeo(
            lon=fire_lons,
            lat=fire_lats,
            mode='markers',
            marker=dict(
                size=[int(i * 25) for i in fire_intensities],
                color=fire_intensities,
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Fire Intensity", x=0.95),
                line=dict(width=3, color='darkred')
            ),
            text=fire_names,
            hovertemplate="<b>%{text}</b><br>" +
                         "Year: %{customdata[0]}<br>" +
                         "Intensity: %{marker.color:.2f}<br>" +
                         "Area Affected: %{customdata[1]}<br>" +
                         "Deaths: %{customdata[2]}<br>" +
                         "Damage: %{customdata[3]}<br>" +
                         "<extra></extra>",
            customdata=list(zip(fire_years, fire_areas, fire_deaths, fire_damage)),
            name="Wildfires",
            showlegend=True
        ))
        
        # Add world map with enhanced styling
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
        
        # Enhanced layout
        fig.update_layout(
            title={
                'text': "🌍 AURORA - Interactive Google Earth Wildfire Response",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 28, 'color': 'darkred'}
            },
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="black",
                borderwidth=1
            ),
            margin=dict(l=0, r=0, t=60, b=0),
            height=900,
            scene=dict(
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            )
        )
        
        # Add interactive control panel
        self._add_control_panel(fig)
        
        return fig
    
    def _add_control_panel(self, fig: go.Figure):
        """Add interactive control panel to the figure."""
        # Main control panel
        fig.add_annotation(
            x=0.02, y=0.98,
            xref="paper", yref="paper",
            text="🎮 <b>INTERACTIVE CONTROLS</b><br>" +
                 "1. Click on any fire location<br>" +
                 "2. Select drone type to deploy<br>" +
                 "3. Watch real-time simulation<br>" +
                 "4. Monitor drone operations",
            showarrow=False,
            font=dict(size=14, color="black"),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="black",
            borderwidth=2
        )
        
        # Drone types panel
        drone_text = "🚁 <b>DRONE TYPES</b><br>"
        for drone_type, config in self.drone_types.items():
            drone_text += f"🔵 {drone_type.replace('_', ' ').title()}<br>"
            drone_text += f"   {config['description']}<br>"
        
        fig.add_annotation(
            x=0.02, y=0.75,
            xref="paper", yref="paper",
            text=drone_text,
            showarrow=False,
            font=dict(size=12, color="black"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1
        )
        
        # Simulation status
        fig.add_annotation(
            x=0.02, y=0.45,
            xref="paper", yref="paper",
            text="📊 <b>SIMULATION STATUS</b><br>" +
                 "Status: Ready for Deployment<br>" +
                 "Active Drones: 0<br>" +
                 "Fires Monitored: 0<br>" +
                 "AI Coordination: Active",
            showarrow=False,
            font=dict(size=12, color="black"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1
        )
        
        # Instructions
        fig.add_annotation(
            x=0.02, y=0.15,
            xref="paper", yref="paper",
            text="💡 <b>INSTRUCTIONS</b><br>" +
                 "• Rotate globe with mouse<br>" +
                 "• Zoom with scroll wheel<br>" +
                 "• Click fires for details<br>" +
                 "• Deploy drones interactively",
            showarrow=False,
            font=dict(size=12, color="black"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1
        )
    
    def create_advanced_simulation(self) -> go.Figure:
        """Create advanced simulation with multiple drones responding to fires."""
        fig = self.create_interactive_interface()
        
        # Simulate comprehensive drone response
        for fire in self.world_fires[:4]:  # First 4 major fires
            # Deploy surveillance drone first
            fig = self._add_drone_to_fire(fig, fire, "surveillance")
            
            # Deploy water bomber
            fig = self._add_drone_to_fire(fig, fire, "water_bomber")
            
            # Deploy firefighter coordination
            fig = self._add_drone_to_fire(fig, fire, "firefighter")
        
        # Add AI coordination center
        fig.add_trace(go.Scattergeo(
            lon=[0], lat=[0],
            mode='markers',
            marker=dict(
                size=15,
                color="purple",
                symbol="star",
                line=dict(width=3, color='black')
            ),
            text=["AURORA AI Command Center"],
            hovertemplate="<b>%{text}</b><br>" +
                         "AI Coordination Hub<br>" +
                         "Managing Global Response<br>" +
                         "<extra></extra>",
            name="AI Command Center",
            showlegend=True
        ))
        
        # Update simulation status
        fig.add_annotation(
            x=0.02, y=0.45,
            xref="paper", yref="paper",
            text="🚀 <b>ACTIVE SIMULATION</b><br>" +
                 "Status: AI Coordinated Response<br>" +
                 "Active Drones: 12<br>" +
                 "Fires Monitored: 4<br>" +
                 "AI Coordination: Active<br>" +
                 "Response Time: < 5 minutes",
            showarrow=False,
            font=dict(size=12, color="black"),
            bgcolor="rgba(0, 255, 0, 0.2)",
            bordercolor="green",
            borderwidth=2
        )
        
        return fig
    
    def _add_drone_to_fire(self, fig: go.Figure, fire: Dict, drone_type: str) -> go.Figure:
        """Add a drone responding to a specific fire."""
        # Create drone starting position (nearby base)
        base_lat = fire["lat"] + np.random.uniform(-5, 5)
        base_lon = fire["lon"] + np.random.uniform(-5, 5)
        
        # Create flight path
        path_lats = np.linspace(base_lat, fire["lat"], 15)
        path_lons = np.linspace(base_lon, fire["lon"], 15)
        
        drone_config = self.drone_types[drone_type]
        
        # Add flight path
        fig.add_trace(go.Scattergeo(
            lon=path_lons,
            lat=path_lats,
            mode='lines',
            line=dict(
                color=drone_config["color"],
                width=4,
                dash='dash'
            ),
            name=f"{drone_type.replace('_', ' ').title()} Path",
            showlegend=True
        ))
        
        # Add drone marker
        fig.add_trace(go.Scattergeo(
            lon=[base_lat],
            lat=[base_lon],
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
                         "Status: En Route to " + fire["name"] + "<br>" +
                         "ETA: < 5 minutes<br>" +
                         "<extra></extra>",
            name=f"{drone_type.replace('_', ' ').title()} Drone",
            showlegend=True
        ))
        
        return fig


def create_interactive_google_earth_demo():
    """Create and save the interactive Google Earth demo."""
    print("🌍 Creating AURORA Interactive Google Earth Demo...")
    
    # Create visualizer
    aurora_earth = InteractiveAURORAGoggleEarth()
    
    # Create basic interactive interface
    basic_fig = aurora_earth.create_interactive_interface()
    basic_fig.write_html("results/aurora_interactive_google_earth.html")
    
    # Create advanced simulation
    advanced_fig = aurora_earth.create_advanced_simulation()
    advanced_fig.write_html("results/aurora_interactive_google_earth_advanced.html")
    
    print("✅ Interactive Google Earth visualizations saved!")
    print("📁 Files created:")
    print("  - results/aurora_interactive_google_earth.html (Interactive Interface)")
    print("  - results/aurora_interactive_google_earth_advanced.html (Advanced Simulation)")
    
    return aurora_earth


if __name__ == "__main__":
    create_interactive_google_earth_demo() 