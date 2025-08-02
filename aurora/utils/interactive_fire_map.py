"""
Interactive Fire Map for AURORA

This module creates an interactive map visualization that:
- Displays real fire data from NASA FIRMS
- Shows fire locations with clickable details
- Allows running simulations from the frontend
- Visualizes drone deployment and movement
- Provides real-time fire spread simulation
"""

import os
import json
import geopandas as gpd
import folium
from folium import plugins
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import webbrowser
from pathlib import Path
import datetime
import random

class InteractiveFireMap:
    """Interactive fire map with real data and simulation capabilities."""
    
    def __init__(self, fire_data_dir: str = "../Fire_Data"):
        """
        Initialize the interactive fire map.
        
        Args:
            fire_data_dir: Directory containing fire data files
        """
        self.fire_data_dir = Path(fire_data_dir)
        self.fire_data = {}
        self.map = None
        self.simulation_data = {}
        
    def load_fire_data(self) -> Dict[str, Any]:
        """Load all fire data from the Fire_Data directory."""
        print("🔥 Loading fire data from NASA FIRMS...")
        
        fire_datasets = {}
        
        # Scan all fire data directories
        for fire_dir in self.fire_data_dir.glob("DL_FIRE_*"):
            if fire_dir.is_dir():
                dataset_name = fire_dir.name
                print(f"📁 Processing {dataset_name}...")
                
                # Look for shapefiles
                shapefiles = list(fire_dir.glob("*.shp"))
                
                for shp_file in shapefiles:
                    try:
                        # Load the shapefile
                        gdf = gpd.read_file(shp_file)
                        
                        # Extract dataset info
                        dataset_info = {
                            'name': dataset_name,
                            'file': shp_file.name,
                            'count': len(gdf),
                            'columns': list(gdf.columns),
                            'geometry_type': gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else 'Unknown',
                            'data': gdf
                        }
                        
                        fire_datasets[f"{dataset_name}_{shp_file.stem}"] = dataset_info
                        print(f"  ✅ Loaded {len(gdf)} fire points from {shp_file.name}")
                        
                    except Exception as e:
                        print(f"  ❌ Error loading {shp_file}: {e}")
        
        self.fire_data = fire_datasets
        print(f"🎯 Total datasets loaded: {len(fire_datasets)}")
        return fire_datasets
    
    def create_interactive_map(self, center_lat: float = 37.7749, center_lon: float = -122.4194) -> folium.Map:
        """Create an interactive map with fire data and simulation controls."""
        
        # Create the base map
        self.map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Add tile layers
        folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(self.map)
        folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(self.map)
        folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(self.map)
        
        # Add fire data layers
        self._add_fire_layers()
        
        # Add simulation controls
        self._add_simulation_controls()
        
        # Add layer control
        folium.LayerControl().add_to(self.map)
        
        return self.map
    
    def _add_fire_layers(self):
        """Add fire data as interactive layers."""
        
        if not self.fire_data:
            self.load_fire_data()
        
        # Color scheme for different fire types
        fire_colors = {
            'SV-C2': 'red',      # Suomi NPP VIIRS
            'M-C61': 'orange',   # MODIS
            'J1V-C2': 'yellow',  # NOAA-20 VIIRS
            'J2V-C2': 'purple',  # NOAA-21 VIIRS
            'LS': 'brown'        # Landsat
        }
        
        for dataset_key, dataset_info in self.fire_data.items():
            if len(dataset_info['data']) == 0:
                continue
                
            # Determine color based on satellite type
            color = 'red'
            for sat_type, sat_color in fire_colors.items():
                if sat_type in dataset_key:
                    color = sat_color
                    break
            
            # Create feature group for this dataset
            fg = folium.FeatureGroup(name=f"🔥 {dataset_info['name']} ({dataset_info['count']} fires)")
            
            # Add fire points
            for idx, row in dataset_info['data'].iterrows():
                try:
                    # Get coordinates
                    if hasattr(row.geometry, 'x') and hasattr(row.geometry, 'y'):
                        lon, lat = row.geometry.x, row.geometry.y
                    else:
                        # Try to get centroid
                        lon, lat = row.geometry.centroid.x, row.geometry.centroid.y
                    
                    # Create popup content
                    popup_content = self._create_fire_popup(row, dataset_info)
                    
                    # Add marker
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=3,
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.7,
                        popup=folium.Popup(popup_content, max_width=300),
                        tooltip=f"Fire {idx+1} - {dataset_info['name']}"
                    ).add_to(fg)
                    
                except Exception as e:
                    print(f"Error adding fire point {idx}: {e}")
                    continue
            
            fg.add_to(self.map)
    
    def _create_fire_popup(self, row, dataset_info: Dict) -> str:
        """Create popup content for a fire point."""
        
        popup_html = f"""
        <div style="width: 250px;">
            <h4>🔥 Fire Details</h4>
            <p><strong>Dataset:</strong> {dataset_info['name']}</p>
            <p><strong>Satellite:</strong> {dataset_info['name'].split('_')[2]}</p>
        """
        
        # Add available attributes
        for col in dataset_info['columns']:
            if col != 'geometry':
                try:
                    value = row[col]
                    if pd.notna(value):
                        # Format the value nicely
                        if isinstance(value, (int, float)):
                            if col.lower() in ['confidence', 'frp']:
                                popup_html += f"<p><strong>{col}:</strong> {value:.2f}</p>"
                            else:
                                popup_html += f"<p><strong>{col}:</strong> {value}</p>"
                        else:
                            popup_html += f"<p><strong>{col}:</strong> {value}</p>"
                except:
                    continue
        
        popup_html += """
            <hr>
            <button onclick="runSimulation(this)" 
                    style="background: #ff4444; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
                🚁 Run Simulation
            </button>
        </div>
        """
        
        return popup_html
    
    def _add_simulation_controls(self):
        """Add simulation controls to the map."""
        
        # Add simulation panel
        simulation_html = """
        <div id="simulation-panel" style="position: fixed; top: 10px; right: 10px; width: 300px; 
             background: white; border: 2px solid #ccc; border-radius: 5px; padding: 10px; z-index: 1000;">
            <h3>🚁 AURORA Simulation</h3>
            <div>
                <label>Number of Drones:</label>
                <input type="number" id="num-drones" value="3" min="1" max="10" style="width: 60px;">
            </div>
            <div style="margin-top: 10px;">
                <label>Simulation Steps:</label>
                <input type="number" id="sim-steps" value="50" min="10" max="200" style="width: 60px;">
            </div>
            <div style="margin-top: 10px;">
                <label>Wind Speed (mph):</label>
                <input type="number" id="wind-speed" value="15" min="0" max="50" style="width: 60px;">
            </div>
            <div style="margin-top: 10px;">
                <label>Wind Direction:</label>
                <select id="wind-direction" style="width: 100px;">
                    <option value="N">North</option>
                    <option value="NE">Northeast</option>
                    <option value="E">East</option>
                    <option value="SE">Southeast</option>
                    <option value="S">South</option>
                    <option value="SW">Southwest</option>
                    <option value="W">West</option>
                    <option value="NW">Northwest</option>
                </select>
            </div>
            <button onclick="startSimulation()" 
                    style="background: #28a745; color: white; border: none; padding: 8px 15px; 
                           border-radius: 3px; cursor: pointer; margin-top: 10px; width: 100%;">
                🚀 Start Simulation
            </button>
            <div id="simulation-status" style="margin-top: 10px; font-size: 12px; color: #666;">
                Ready to simulate
            </div>
        </div>
        """
        
        # Add JavaScript for simulation
        simulation_js = """
        <script>
        function startSimulation() {
            const numDrones = document.getElementById('num-drones').value;
            const simSteps = document.getElementById('sim-steps').value;
            const windSpeed = document.getElementById('wind-speed').value;
            const windDirection = document.getElementById('wind-direction').value;
            
            document.getElementById('simulation-status').innerHTML = '🚁 Starting simulation...';
            
            // Send simulation request to backend
            fetch('/api/run-simulation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    num_drones: parseInt(numDrones),
                    steps: parseInt(simSteps),
                    wind_speed: parseFloat(windSpeed),
                    wind_direction: windDirection,
                    fire_data: 'all'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('simulation-status').innerHTML = 
                        '✅ Simulation completed! Check results below.';
                    displaySimulationResults(data.results);
                } else {
                    document.getElementById('simulation-status').innerHTML = 
                        '❌ Simulation failed: ' + data.error;
                }
            })
            .catch(error => {
                document.getElementById('simulation-status').innerHTML = 
                    '❌ Error: ' + error.message;
            });
        }
        
        function displaySimulationResults(results) {
            // Create results display
            const resultsDiv = document.createElement('div');
            resultsDiv.id = 'simulation-results';
            resultsDiv.style.cssText = 'position: fixed; bottom: 10px; left: 10px; width: 400px; ' +
                                      'background: white; border: 2px solid #28a745; border-radius: 5px; ' +
                                      'padding: 10px; z-index: 1000; max-height: 300px; overflow-y: auto;';
            
            resultsDiv.innerHTML = `
                <h4>📊 Simulation Results</h4>
                <p><strong>Fire Coverage:</strong> ${results.fire_coverage}%</p>
                <p><strong>Suppressions:</strong> ${results.suppressions}</p>
                <p><strong>Duration:</strong> ${results.duration}s</p>
                <p><strong>Efficiency:</strong> ${results.efficiency}%</p>
                <button onclick="this.parentElement.remove()" 
                        style="background: #dc3545; color: white; border: none; padding: 5px 10px; 
                               border-radius: 3px; cursor: pointer;">
                    Close
                </button>
            `;
            
            document.body.appendChild(resultsDiv);
        }
        
        function runSimulation(button) {
            // Get fire location from popup
            const popup = button.closest('.leaflet-popup');
            const lat = popup._latlng.lat;
            const lng = popup._latlng.lng;
            
            // Set simulation parameters for this specific fire
            document.getElementById('num-drones').value = 2;
            document.getElementById('sim-steps').value = 30;
            
            // Start simulation focused on this fire
            startSimulation();
        }
        </script>
        """
        
        # Add to map
        self.map.get_root().html.add_child(folium.Element(simulation_html + simulation_js))
    
    def add_drone_trajectories(self, drone_data: List[Dict]):
        """Add drone trajectories to the map."""
        
        # Create drone layer
        drone_fg = folium.FeatureGroup(name="🚁 Drone Trajectories")
        
        colors = ['red', 'blue', 'green', 'purple', 'orange']
        
        for i, drone in enumerate(drone_data):
            color = colors[i % len(colors)]
            
            # Create trajectory line
            if len(drone['trajectory']) > 1:
                folium.PolyLine(
                    locations=drone['trajectory'],
                    color=color,
                    weight=3,
                    opacity=0.8,
                    popup=f"Drone {i+1} Trajectory"
                ).add_to(drone_fg)
            
            # Add start and end markers
            if drone['trajectory']:
                # Start marker
                folium.CircleMarker(
                    location=drone['trajectory'][0],
                    radius=8,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.8,
                    popup=f"Drone {i+1} Start"
                ).add_to(drone_fg)
                
                # End marker
                folium.CircleMarker(
                    location=drone['trajectory'][-1],
                    radius=8,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.8,
                    popup=f"Drone {i+1} End"
                ).add_to(drone_fg)
        
        drone_fg.add_to(self.map)
    
    def save_map(self, filename: str = "aurora_interactive_fire_map.html") -> str:
        """Save the interactive map to HTML file."""
        
        output_path = Path("results") / filename
        output_path.parent.mkdir(exist_ok=True)
        
        self.map.save(str(output_path))
        print(f"🗺️ Interactive map saved to: {output_path}")
        
        return str(output_path)
    
    def open_map(self, filename: str = "aurora_interactive_fire_map.html"):
        """Open the interactive map in browser."""
        
        output_path = Path("results") / filename
        if output_path.exists():
            webbrowser.open(f"file://{output_path.absolute()}")
        else:
            print(f"Map file not found: {output_path}")


def create_interactive_fire_map():
    """Create and display the interactive fire map."""
    
    print("🔥 Creating AURORA Interactive Fire Map...")
    
    # Create the map
    fire_map = InteractiveFireMap()
    
    # Load fire data
    fire_map.load_fire_data()
    
    # Create interactive map
    map_obj = fire_map.create_interactive_map()
    
    # Save and open
    output_path = fire_map.save_map()
    fire_map.open_map()
    
    print("✅ Interactive fire map created and opened!")
    print(f"🌐 Map URL: file://{Path(output_path).absolute()}")
    
    return fire_map


if __name__ == "__main__":
    create_interactive_fire_map() 