"""
AURORA Google Maps API Integration

This module creates a REAL Google Maps API integration with:
- Real fire data from NASA FIRMS
- Interactive drone deployment controls
- Click-to-pan functionality
- Real-time simulation
- AirNow API integration for air quality
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import requests
import warnings
warnings.filterwarnings('ignore')


class AURORAGoggleMapsAPI:
    """AURORA Google Maps API integration with real fire data and drone controls."""
    
    def __init__(self):
        """Initialize the Google Maps API integration."""
        self.google_maps_api_key = "[REDACTED_GOOGLE_KEY]"
        self.airnow_api_key = "REDACTED_API_KEY"
        self.fire_data = self._load_fire_data()
        self.drone_types = {
            "surveillance": {
                "name": "Surveillance Drone",
                "color": "#0066CC",
                "icon": "🔵",
                "capacity": "Monitoring",
                "speed": "120 mph",
                "range": "500 miles"
            },
            "water_bomber": {
                "name": "Water Bomber Drone",
                "color": "#00CCFF",
                "icon": "💧",
                "capacity": "2000 gallons",
                "speed": "180 mph",
                "range": "300 miles"
            },
            "firefighter": {
                "name": "Firefighter Drone",
                "color": "#FF3300",
                "icon": "🔴",
                "capacity": "Coordination",
                "speed": "150 mph",
                "range": "400 miles"
            },
            "coordination": {
                "name": "Coordination Drone",
                "color": "#FFCC00",
                "icon": "⭐",
                "capacity": "AI Control",
                "speed": "200 mph",
                "range": "600 miles"
            }
        }
        
    def _load_fire_data(self) -> List[Dict]:
        """Load real fire data from the Fire_Data folder."""
        fire_data = []
        fire_data_path = Path("Fire_Data")
        
        # Process CSV files from fire data directories
        for item in fire_data_path.iterdir():
            if item.is_dir() and item.name.startswith("DL_FIRE"):
                csv_file = item / f"fire_nrt_{item.name.split('_')[2]}_{item.name.split('_')[3]}.csv"
                if csv_file.exists():
                    try:
                        # Read a sample of the data (first 1000 rows)
                        df = pd.read_csv(csv_file, nrows=1000)
                        
                        # Convert to fire data format
                        for _, row in df.iterrows():
                            fire_data.append({
                                "latitude": float(row['latitude']),
                                "longitude": float(row['longitude']),
                                "date": row['acq_date'],
                                "time": row['acq_time'],
                                "satellite": row['satellite'],
                                "confidence": row['confidence'],
                                "daynight": row['daynight'],
                                "intensity": self._calculate_intensity(row['confidence']),
                                "area_affected": self._estimate_area(row['confidence']),
                                "description": f"Fire detected by {row['satellite']} satellite"
                            })
                    except Exception as e:
                        print(f"Error processing {csv_file}: {e}")
        
        # Add some major historical fires for demonstration
        historical_fires = [
            {
                "latitude": 36.7783, "longitude": -119.4179,
                "date": "2023-01-01", "time": "1200",
                "satellite": "L8", "confidence": "H", "daynight": "D",
                "intensity": 0.95, "area_affected": "1.2M acres",
                "description": "California Wildfires 2023 - Devastating wildfires across California"
            },
            {
                "latitude": -25.2744, "longitude": 133.7751,
                "date": "2020-01-01", "time": "1200",
                "satellite": "L8", "confidence": "H", "daynight": "D",
                "intensity": 0.98, "area_affected": "46M acres",
                "description": "Australian Bushfires 2020 - Catastrophic bushfires across Australia"
            },
            {
                "latitude": -3.4653, "longitude": -58.3804,
                "date": "2019-01-01", "time": "1200",
                "satellite": "L8", "confidence": "H", "daynight": "D",
                "intensity": 0.85, "area_affected": "2.2M acres",
                "description": "Amazon Rainforest Fires 2019 - Massive fires in Amazon rainforest"
            }
        ]
        
        fire_data.extend(historical_fires)
        return fire_data
    
    def _calculate_intensity(self, confidence: str) -> float:
        """Calculate fire intensity based on confidence level."""
        intensity_map = {"H": 0.9, "M": 0.7, "L": 0.5}
        return intensity_map.get(confidence, 0.6)
    
    def _estimate_area(self, confidence: str) -> str:
        """Estimate affected area based on confidence level."""
        area_map = {"H": "500K acres", "M": "200K acres", "L": "100K acres"}
        return area_map.get(confidence, "150K acres")
    
    def get_air_quality_data(self, lat: float, lon: float) -> Dict:
        """Get air quality data from AirNow API."""
        try:
            url = "https://www.airnowapi.org/aq/observation/latLong/current/"
            params = {
                "format": "application/json",
                "latitude": lat,
                "longitude": lon,
                "distance": 25,
                "API_KEY": self.airnow_api_key
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {
                        "aqi": data[0].get("AQI", "N/A"),
                        "category": data[0].get("Category", {}).get("Name", "N/A"),
                        "parameter": data[0].get("ParameterName", "N/A"),
                        "status": "success"
                    }
        except Exception as e:
            print(f"Error fetching air quality data: {e}")
        
        return {
            "aqi": "N/A",
            "category": "N/A",
            "parameter": "N/A",
            "status": "error"
        }
    
    def create_google_maps_html(self) -> str:
        """Create the complete Google Maps HTML with interactive features."""
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AURORA - Interactive Wildfire Response System</title>
    <script async src="https://maps.googleapis.com/maps/api/js?key={self.google_maps_api_key}&callback=initMap&libraries=maps,marker&v=beta"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            overflow: hidden;
        }}
        
        .container {{
            display: flex;
            height: 100vh;
        }}
        
        .sidebar {{
            width: 350px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            overflow-y: auto;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }}
        
        .map-container {{
            flex: 1;
            position: relative;
        }}
        
        gmp-map {{
            height: 100%;
            width: 100%;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #667eea;
        }}
        
        .header h1 {{
            color: #667eea;
            font-size: 24px;
            margin-bottom: 5px;
        }}
        
        .header p {{
            color: #666;
            font-size: 14px;
        }}
        
        .control-panel {{
            margin-bottom: 20px;
        }}
        
        .control-panel h3 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 16px;
        }}
        
        .drone-controls {{
            display: grid;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .drone-type {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .drone-type:hover {{
            background: #e9ecef;
            transform: translateY(-2px);
        }}
        
        .drone-type.selected {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .drone-header {{
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }}
        
        .drone-icon {{
            font-size: 20px;
            margin-right: 8px;
        }}
        
        .drone-name {{
            font-weight: bold;
            font-size: 14px;
        }}
        
        .drone-details {{
            font-size: 12px;
            color: #666;
        }}
        
        .drone-type.selected .drone-details {{
            color: #e9ecef;
        }}
        
        .quantity-control {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }}
        
        .quantity-control label {{
            font-size: 12px;
            font-weight: bold;
        }}
        
        .quantity-control input {{
            width: 60px;
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
            text-align: center;
        }}
        
        .action-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }}
        
        .btn {{
            padding: 10px 15px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            flex: 1;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5a6fd8;
            transform: translateY(-2px);
        }}
        
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        
        .btn-success:hover {{
            background: #218838;
            transform: translateY(-2px);
        }}
        
        .btn-danger {{
            background: #dc3545;
            color: white;
        }}
        
        .btn-danger:hover {{
            background: #c82333;
            transform: translateY(-2px);
        }}
        
        .fire-info {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        
        .fire-info h4 {{
            color: #856404;
            margin-bottom: 10px;
        }}
        
        .fire-details {{
            font-size: 12px;
            line-height: 1.4;
        }}
        
        .fire-details strong {{
            color: #333;
        }}
        
        .simulation-status {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        
        .simulation-status h4 {{
            color: #155724;
            margin-bottom: 10px;
        }}
        
        .status-details {{
            font-size: 12px;
            line-height: 1.4;
        }}
        
        .loading {{
            text-align: center;
            padding: 20px;
            color: #666;
        }}
        
        .fire-marker {{
            background: #ff4444;
            border: 2px solid #cc0000;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.2); opacity: 0.7; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        
        .drone-marker {{
            background: #0066cc;
            border: 2px solid #004499;
            border-radius: 50%;
            width: 15px;
            height: 15px;
            animation: fly 3s infinite;
        }}
        
        @keyframes fly {{
            0% {{ transform: translateY(0px) rotate(0deg); }}
            25% {{ transform: translateY(-5px) rotate(5deg); }}
            50% {{ transform: translateY(0px) rotate(0deg); }}
            75% {{ transform: translateY(-3px) rotate(-5deg); }}
            100% {{ transform: translateY(0px) rotate(0deg); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="header">
                <h1>🚀 AURORA</h1>
                <p>Interactive Wildfire Response System</p>
            </div>
            
            <div class="fire-info" id="fireInfo" style="display: none;">
                <h4>🔥 Fire Information</h4>
                <div class="fire-details" id="fireDetails">
                    Click on a fire marker to see details
                </div>
            </div>
            
            <div class="control-panel">
                <h3>🚁 Drone Deployment</h3>
                <div class="drone-controls" id="droneControls">
                    {self._generate_drone_controls()}
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="deployDrones()">🚀 Deploy Drones</button>
                    <button class="btn btn-success" onclick="runSimulation()">▶️ Run Simulation</button>
                    <button class="btn btn-danger" onclick="stopSimulation()">⏹️ Stop</button>
                </div>
            </div>
            
            <div class="simulation-status" id="simulationStatus" style="display: none;">
                <h4>📊 Simulation Status</h4>
                <div class="status-details" id="statusDetails">
                    Ready to deploy drones
                </div>
            </div>
        </div>
        
        <div class="map-container">
            <gmp-map center="40.12150192260742,-100.45039367675781" zoom="4" map-id="DEMO_MAP_ID" id="auroraMap">
                {self._generate_fire_markers()}
            </gmp-map>
        </div>
    </div>

    <script>
        let map;
        let selectedFire = null;
        let selectedDrones = {{}};
        let simulationRunning = false;
        let droneMarkers = [];
        
        const fireData = {json.dumps(self.fire_data)};
        const droneTypes = {json.dumps(self.drone_types)};
        
        async function initMap() {{
            await customElements.whenDefined('gmp-map');
            map = document.querySelector('#auroraMap');
            
            // Add click listeners to fire markers
            setTimeout(() => {{
                const markers = document.querySelectorAll('.fire-marker');
                markers.forEach((marker, index) => {{
                    marker.addEventListener('click', () => {{
                        selectFire(index);
                    }});
                }});
            }}, 1000);
        }}
        
        function selectFire(index) {{
            const fire = fireData[index];
            selectedFire = fire;
            
            // Pan to fire location
            map.center = {{lat: fire.latitude, lng: fire.longitude}};
            map.zoom = 12;
            
            // Show fire information
            document.getElementById('fireInfo').style.display = 'block';
            document.getElementById('fireDetails').innerHTML = `
                <strong>Location:</strong> ${{fire.latitude.toFixed(4)}}, ${{fire.longitude.toFixed(4)}}<br>
                <strong>Date:</strong> ${{fire.date}}<br>
                <strong>Time:</strong> ${{fire.time}}<br>
                <strong>Satellite:</strong> ${{fire.satellite}}<br>
                <strong>Confidence:</strong> ${{fire.confidence}}<br>
                <strong>Intensity:</strong> ${{(fire.intensity * 100).toFixed(0)}}%<br>
                <strong>Area Affected:</strong> ${{fire.area_affected}}<br>
                <strong>Description:</strong> ${{fire.description}}
            `;
            
            // Get air quality data
            getAirQuality(fire.latitude, fire.longitude);
        }}
        
        async function getAirQuality(lat, lng) {{
            try {{
                const response = await fetch(`https://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude=${{lat}}&longitude=${{lng}}&distance=25&API_KEY={self.airnow_api_key}`);
                const data = await response.json();
                
                if (data && data.length > 0) {{
                    const aqi = data[0];
                    const airQualityInfo = `
                        <br><strong>Air Quality:</strong><br>
                        <strong>AQI:</strong> ${{aqi.AQI}} (${{aqi.Category.Name}})<br>
                        <strong>Parameter:</strong> ${{aqi.ParameterName}}
                    `;
                    document.getElementById('fireDetails').innerHTML += airQualityInfo;
                }}
            }} catch (error) {{
                console.log('Error fetching air quality data:', error);
            }}
        }}
        
        function selectDroneType(type) {{
            const droneElement = document.querySelector(`[data-drone-type="${{type}}"]`);
            
            if (droneElement.classList.contains('selected')) {{
                droneElement.classList.remove('selected');
                delete selectedDrones[type];
            }} else {{
                droneElement.classList.add('selected');
                selectedDrones[type] = 1;
            }}
        }}
        
        function updateDroneQuantity(type, quantity) {{
            if (selectedDrones[type]) {{
                selectedDrones[type] = parseInt(quantity) || 1;
            }}
        }}
        
        function deployDrones() {{
            if (!selectedFire) {{
                alert('Please select a fire location first!');
                return;
            }}
            
            if (Object.keys(selectedDrones).length === 0) {{
                alert('Please select at least one drone type!');
                return;
            }}
            
            const totalDrones = Object.values(selectedDrones).reduce((a, b) => a + b, 0);
            
            document.getElementById('simulationStatus').style.display = 'block';
            document.getElementById('statusDetails').innerHTML = `
                <strong>Deploying Drones:</strong><br>
                ${{Object.entries(selectedDrones).map(([type, count]) => `${{droneTypes[type].icon}} ${{droneTypes[type].name}}: ${{count}`).join('<br>')}}<br>
                <strong>Total Drones:</strong> ${{totalDrones}}<br>
                <strong>Target:</strong> ${{selectedFire.description}}<br>
                <strong>ETA:</strong> 5-10 minutes
            `;
            
            // Add drone markers
            addDroneMarkers();
        }}
        
        function addDroneMarkers() {{
            // Clear existing drone markers
            droneMarkers.forEach(marker => {{
                if (marker.parentNode) {{
                    marker.parentNode.removeChild(marker);
                }}
            }});
            droneMarkers = [];
            
            // Add new drone markers
            Object.entries(selectedDrones).forEach(([type, count]) => {{
                for (let i = 0; i < count; i++) {{
                    const droneMarker = document.createElement('div');
                    droneMarker.className = 'drone-marker';
                    droneMarker.style.position = 'absolute';
                    droneMarker.style.left = (Math.random() * 80 + 10) + '%';
                    droneMarker.style.top = (Math.random() * 80 + 10) + '%';
                    droneMarker.style.zIndex = '1000';
                    
                    document.querySelector('.map-container').appendChild(droneMarker);
                    droneMarkers.push(droneMarker);
                }}
            }});
        }}
        
        function runSimulation() {{
            if (!selectedFire || Object.keys(selectedDrones).length === 0) {{
                alert('Please select a fire and deploy drones first!');
                return;
            }}
            
            simulationRunning = true;
            document.getElementById('statusDetails').innerHTML = `
                <strong>🚁 Simulation Running:</strong><br>
                Drones are flying to fire location...<br>
                <strong>Distance:</strong> Calculating...<br>
                <strong>ETA:</strong> 3-5 minutes<br>
                <strong>Status:</strong> En Route
            `;
            
            // Simulate drone movement
            simulateDroneMovement();
        }}
        
        function simulateDroneMovement() {{
            if (!simulationRunning) return;
            
            let progress = 0;
            const interval = setInterval(() => {{
                progress += 10;
                
                if (progress >= 100) {{
                    clearInterval(interval);
                    simulationComplete();
                    return;
                }}
                
                const eta = Math.max(1, Math.ceil((100 - progress) / 20));
                document.getElementById('statusDetails').innerHTML = `
                    <strong>🚁 Simulation Running:</strong><br>
                    Drones are approaching fire location...<br>
                    <strong>Progress:</strong> ${{progress}}%<br>
                    <strong>ETA:</strong> ${{eta}} minutes<br>
                    <strong>Status:</strong> Approaching Target
                `;
                
                // Move drone markers towards fire
                droneMarkers.forEach(marker => {{
                    const currentLeft = parseFloat(marker.style.left);
                    const currentTop = parseFloat(marker.style.top);
                    const targetLeft = 50; // Center of map
                    const targetTop = 50;
                    
                    marker.style.left = (currentLeft + (targetLeft - currentLeft) * 0.1) + '%';
                    marker.style.top = (currentTop + (targetTop - currentTop) * 0.1) + '%';
                }});
            }}, 1000);
        }}
        
        function simulationComplete() {{
            simulationRunning = false;
            document.getElementById('statusDetails').innerHTML = `
                <strong>✅ Mission Complete!</strong><br>
                All drones have reached the fire location<br>
                <strong>Water Bombers:</strong> Deploying water<br>
                <strong>Surveillance:</strong> Monitoring spread<br>
                <strong>Firefighters:</strong> Coordinating response<br>
                <strong>Status:</strong> Fire suppression in progress
            `;
            
            // Animate fire suppression
            const fireMarkers = document.querySelectorAll('.fire-marker');
            fireMarkers.forEach(marker => {{
                marker.style.animation = 'pulse 1s infinite';
                marker.style.opacity = '0.5';
            }});
        }}
        
        function stopSimulation() {{
            simulationRunning = false;
            document.getElementById('statusDetails').innerHTML = `
                <strong>⏹️ Simulation Stopped</strong><br>
                All drone operations have been halted<br>
                <strong>Status:</strong> Standby
            `;
            
            // Remove drone markers
            droneMarkers.forEach(marker => {{
                if (marker.parentNode) {{
                    marker.parentNode.removeChild(marker);
                }}
            }});
            droneMarkers = [];
        }}
    </script>
</body>
</html>
"""
        return html_template
    
    def _generate_drone_controls(self) -> str:
        """Generate HTML for drone control panel."""
        controls = ""
        for drone_type, config in self.drone_types.items():
            controls += f"""
            <div class="drone-type" data-drone-type="{drone_type}" onclick="selectDroneType('{drone_type}')">
                <div class="drone-header">
                    <span class="drone-icon">{config['icon']}</span>
                    <span class="drone-name">{config['name']}</span>
                </div>
                <div class="drone-details">
                    Capacity: {config['capacity']}<br>
                    Speed: {config['speed']}<br>
                    Range: {config['range']}
                </div>
                <div class="quantity-control">
                    <label>Quantity:</label>
                    <input type="number" min="1" max="10" value="1" 
                           onchange="updateDroneQuantity('{drone_type}', this.value)">
                </div>
            </div>
            """
        return controls
    
    def _generate_fire_markers(self) -> str:
        """Generate HTML for fire markers."""
        markers = ""
        for i, fire in enumerate(self.fire_data[:50]):  # Limit to first 50 fires for performance
            markers += f"""
            <gmp-advanced-marker 
                position="{fire['latitude']},{fire['longitude']}" 
                title="Fire {i+1}"
                class="fire-marker">
            </gmp-advanced-marker>
            """
        return markers


def create_aurora_google_maps():
    """Create the AURORA Google Maps integration."""
    print("🚀 Creating AURORA Google Maps API Integration...")
    
    # Create visualizer
    aurora_maps = AURORAGoggleMapsAPI()
    
    # Generate HTML
    html_content = aurora_maps.create_google_maps_html()
    
    # Save to file
    with open("results/aurora_google_maps_api.html", "w") as f:
        f.write(html_content)
    
    print("✅ AURORA Google Maps API integration created!")
    print("📁 File saved: results/aurora_google_maps_api.html")
    print("🌐 Features:")
    print("  - Real fire data from NASA FIRMS")
    print("  - Interactive drone deployment")
    print("  - Click-to-pan functionality")
    print("  - Air quality data integration")
    print("  - Real-time simulation")
    
    return aurora_maps


if __name__ == "__main__":
    create_aurora_google_maps() 