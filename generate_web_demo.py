"""
AURORA Interactive Web Demo Generator

Generates an interactive HTML dashboard for ISEF judges showing:
- Real-time drone movements on map with strategic LLM guidance overlay
- Fire spread animation
- Performance metrics and telemetry
- LLM strategic reasoning display

Author: Shaurya Mallampati
Date: October 13, 2025
ISEF 2025 Competition
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AURORA - AI Wildfire Response Demo | ISEF 2025</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.95;
        }}
        
        .info-panel {{
            background: #f8f9fa;
            padding: 20px 30px;
            border-bottom: 3px solid #e9ecef;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}
        
        .info-card {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .info-card h3 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .info-card p {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }}
        
        .main-content {{
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 20px;
            padding: 30px;
        }}
        
        .visualization-panel {{
            background: white;
        }}
        
        .side-panel {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            max-height: 800px;
            overflow-y: auto;
        }}
        
        #fireCanvas {{
            border: 3px solid #e9ecef;
            border-radius: 10px;
            width: 100%;
            height: auto;
            image-rendering: pixelated;
        }}
        
        .controls {{
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.1em;
            border-radius: 50px;
            cursor: pointer;
            margin: 5px;
            transition: transform 0.2s, box-shadow 0.2s;
            font-weight: bold;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .btn:active {{
            transform: translateY(0);
        }}
        
        .slider-container {{
            margin: 15px 0;
        }}
        
        .slider {{
            width: 100%;
            margin: 10px 0;
        }}
        
        .metrics-display {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .metric-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .metric-row:last-child {{
            border-bottom: none;
        }}
        
        .metric-label {{
            font-weight: bold;
            color: #667eea;
        }}
        
        .metric-value {{
            color: #333;
            font-weight: bold;
        }}
        
        .strategy-panel {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .strategy-panel h3 {{
            color: #f5576c;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }}
        
        .strategy-panel h3:before {{
            content: "🧠";
            margin-right: 10px;
        }}
        
        .strategy-content {{
            font-size: 0.9em;
            line-height: 1.6;
            color: #555;
        }}
        
        .drone-list {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .drone-item {{
            padding: 10px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        
        .drone-item.inactive {{
            opacity: 0.5;
            border-left-color: #dc3545;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 5px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
        }}
        
        .progress-fill.battery {{
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        }}
        
        .progress-fill.water {{
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .burning {{
            animation: pulse 1s infinite;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 AURORA 🚁</h1>
            <p>AI-Powered Wildfire Response System with Hybrid PPO + LLM Strategy</p>
            <p style="font-size: 0.9em; margin-top: 10px;">ISEF 2025 | Shaurya Mallampati</p>
        </div>
        
        <div class="info-panel">
            <div class="info-grid">
                <div class="info-card">
                    <h3>Fire Scenario</h3>
                    <p id="fireName">{fire_name}</p>
                </div>
                <div class="info-card">
                    <h3>Fire Size</h3>
                    <p id="fireSize">{fire_size} acres</p>
                </div>
                <div class="info-card">
                    <h3>Weather</h3>
                    <p id="weather">{weather_temp}°F, {weather_wind} mph {weather_dir}</p>
                </div>
                <div class="info-card">
                    <h3>Model Type</h3>
                    <p>Hybrid PPO + LLM</p>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="visualization-panel">
                <canvas id="fireCanvas" width="800" height="800"></canvas>
                
                <div class="controls">
                    <button class="btn" onclick="playPause()">▶️ Play / ⏸️ Pause</button>
                    <button class="btn" onclick="resetSimulation()">🔄 Reset</button>
                    <button class="btn" onclick="stepForward()">⏭️ Step</button>
                    
                    <div class="slider-container">
                        <label><strong>Playback Speed:</strong></label>
                        <input type="range" min="1" max="60" value="10" class="slider" id="speedSlider">
                        <span id="speedDisplay">10 FPS</span>
                    </div>
                    
                    <div class="slider-container">
                        <label><strong>Step:</strong> <span id="stepDisplay">0 / 0</span></label>
                        <input type="range" min="0" max="100" value="0" class="slider" id="stepSlider" oninput="seekStep(this.value)">
                    </div>
                </div>
            </div>
            
            <div class="side-panel">
                <div class="metrics-display">
                    <h3 style="color: #667eea; margin-bottom: 15px;">📊 Metrics</h3>
                    <div class="metric-row">
                        <span class="metric-label">Current Step:</span>
                        <span class="metric-value" id="currentStep">0</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Burning Cells:</span>
                        <span class="metric-value burning" id="burningCells">0</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Containment:</span>
                        <span class="metric-value" id="containment">0%</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Active Drones:</span>
                        <span class="metric-value" id="activeDrones">0</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">LLM Guidance Calls:</span>
                        <span class="metric-value" id="llmCalls">{llm_calls}</span>
                    </div>
                </div>
                
                <div class="strategy-panel" id="strategyPanel">
                    <h3>LLM Strategic Guidance</h3>
                    <div class="strategy-content" id="strategyContent">
                        Waiting for LLM guidance...
                    </div>
                </div>
                
                <div class="drone-list">
                    <h3 style="color: #667eea; margin-bottom: 15px;">🚁 Drone Status</h3>
                    <div id="droneListContainer"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Load telemetry data
        const telemetryData = {telemetry_json};
        
        // Canvas setup
        const canvas = document.getElementById('fireCanvas');
        const ctx = canvas.getContext('2d');
        const gridSize = 50;
        const cellSize = canvas.width / gridSize;
        
        // Animation state
        let currentStepIndex = 0;
        let isPlaying = false;
        let playbackInterval = null;
        let playbackSpeed = 10; // FPS
        
        // Color palette
        const colors = {{
            empty: '#f0f0f0',
            forest: '#228b22',
            burning: '#ff4444',
            burnt: '#333333',
            water: '#4facfe',
            droneColors: ['#ffeb3b', '#ff9800', '#00bcd4', '#e91e63', '#8bc34a']
        }};
        
        // Initialize
        document.getElementById('stepSlider').max = telemetryData.steps.length - 1;
        document.getElementById('stepDisplay').textContent = `0 / ${{telemetryData.steps.length}}`;
        
        // Speed control
        document.getElementById('speedSlider').oninput = function() {{
            playbackSpeed = parseInt(this.value);
            document.getElementById('speedDisplay').textContent = playbackSpeed + ' FPS';
            if (isPlaying) {{
                stopPlayback();
                startPlayback();
            }}
        }};
        
        function drawStep(stepIndex) {{
            const step = telemetryData.steps[stepIndex];
            
            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw fire state
            const fireState = step.fire_state;
            for (let y = 0; y < gridSize; y++) {{
                for (let x = 0; x < gridSize; x++) {{
                    const state = fireState[y][x];
                    let color;
                    if (state === 0) color = colors.empty;
                    else if (state === 1) color = colors.burning;
                    else if (state === 2) color = colors.burnt;
                    else color = colors.forest;
                    
                    ctx.fillStyle = color;
                    ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
                }}
            }}
            
            // Draw grid
            ctx.strokeStyle = '#e0e0e0';
            ctx.lineWidth = 0.5;
            for (let i = 0; i <= gridSize; i++) {{
                ctx.beginPath();
                ctx.moveTo(i * cellSize, 0);
                ctx.lineTo(i * cellSize, canvas.height);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(0, i * cellSize);
                ctx.lineTo(canvas.width, i * cellSize);
                ctx.stroke();
            }}
            
            // Draw strategic priority zones if available
            if (step.strategy && step.strategy.priority_zones) {{
                ctx.fillStyle = 'rgba(255, 165, 0, 0.3)';
                ctx.strokeStyle = '#ff8c00';
                ctx.lineWidth = 2;
                step.strategy.priority_zones.forEach(zone => {{
                    const [row, col] = zone;
                    ctx.fillRect(col * cellSize, row * cellSize, cellSize, cellSize);
                    ctx.strokeRect(col * cellSize, row * cellSize, cellSize, cellSize);
                }});
            }}
            
            // Draw drones
            step.drones.forEach((drone, idx) => {{
                const [y, x] = drone.position;
                const centerX = x * cellSize + cellSize / 2;
                const centerY = y * cellSize + cellSize / 2;
                
                // Drone body
                ctx.fillStyle = drone.is_active ? colors.droneColors[idx] : '#888888';
                ctx.beginPath();
                ctx.arc(centerX, centerY, cellSize * 0.4, 0, Math.PI * 2);
                ctx.fill();
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 2;
                ctx.stroke();
                
                // Drone ID
                ctx.fillStyle = '#000';
                ctx.font = 'bold 10px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(drone.id, centerX, centerY);
            }});
            
            // Update metrics
            document.getElementById('currentStep').textContent = step.step;
            document.getElementById('burningCells').textContent = step.metrics.burning_cells;
            document.getElementById('containment').textContent = (step.metrics.containment * 100).toFixed(1) + '%';
            document.getElementById('activeDrones').textContent = step.metrics.active_drones;
            document.getElementById('stepDisplay').textContent = `${{stepIndex + 1}} / ${{telemetryData.steps.length}}`;
            document.getElementById('stepSlider').value = stepIndex;
            
            // Update strategy panel
            if (step.strategy) {{
                const rationale = step.strategy.rationale || 'No rationale provided';
                const zones = step.strategy.priority_zones || [];
                document.getElementById('strategyContent').innerHTML = `
                    <strong>Rationale:</strong> ${{rationale}}<br><br>
                    <strong>Priority Zones:</strong> ${{zones.length > 0 ? zones.map(z => `(${{z[0]}}, ${{z[1]}})`).join(', ') : 'None'}}
                `;
            }}
            
            // Update drone list
            const droneListHtml = step.drones.map((drone, idx) => `
                <div class="drone-item ${{drone.is_active ? '' : 'inactive'}}">
                    <strong>${{drone.id}}</strong><br>
                    Position: (${{drone.position[0]}}, ${{drone.position[1]}})<br>
                    Battery:
                    <div class="progress-bar">
                        <div class="progress-fill battery" style="width: ${{drone.battery * 100}}%"></div>
                    </div>
                    Water:
                    <div class="progress-bar">
                        <div class="progress-fill water" style="width: ${{drone.water * 100}}%"></div>
                    </div>
                </div>
            `).join('');
            document.getElementById('droneListContainer').innerHTML = droneListHtml;
        }}
        
        function playPause() {{
            if (isPlaying) {{
                stopPlayback();
            }} else {{
                startPlayback();
            }}
        }}
        
        function startPlayback() {{
            isPlaying = true;
            playbackInterval = setInterval(() => {{
                if (currentStepIndex < telemetryData.steps.length - 1) {{
                    currentStepIndex++;
                    drawStep(currentStepIndex);
                }} else {{
                    stopPlayback();
                }}
            }}, 1000 / playbackSpeed);
        }}
        
        function stopPlayback() {{
            isPlaying = false;
            if (playbackInterval) {{
                clearInterval(playbackInterval);
                playbackInterval = null;
            }}
        }}
        
        function resetSimulation() {{
            stopPlayback();
            currentStepIndex = 0;
            drawStep(currentStepIndex);
        }}
        
        function stepForward() {{
            stopPlayback();
            if (currentStepIndex < telemetryData.steps.length - 1) {{
                currentStepIndex++;
                drawStep(currentStepIndex);
            }}
        }}
        
        function seekStep(value) {{
            stopPlayback();
            currentStepIndex = parseInt(value);
            drawStep(currentStepIndex);
        }}
        
        // Initial draw
        drawStep(0);
    </script>
</body>
</html>
"""


def generate_web_demo(telemetry_path: str, output_path: str):
    """Generate interactive HTML demo from telemetry JSON.
    
    Args:
        telemetry_path: Path to telemetry JSON file
        output_path: Path to output HTML file
    """
    print(f"Loading telemetry from {telemetry_path}...")
    
    with open(telemetry_path, 'r') as f:
        telemetry = json.load(f)
    
    scenario = telemetry['scenario']
    summary = telemetry['summary']
    
    # Format data for HTML
    fire_name = f"{scenario['fire_name']} ({scenario['fire_year']})"
    fire_size = f"{scenario['size_acres']:.0f}"
    weather_temp = scenario['weather']['temperature_f']
    weather_wind = scenario['weather']['wind_speed_mph']
    weather_dir = scenario['weather']['wind_direction']
    llm_calls = summary['llm_calls']
    
    # Generate HTML
    html = HTML_TEMPLATE.format(
        fire_name=fire_name,
        fire_size=fire_size,
        weather_temp=weather_temp,
        weather_wind=weather_wind,
        weather_dir=weather_dir,
        llm_calls=llm_calls,
        telemetry_json=json.dumps(telemetry)
    )
    
    # Save HTML
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"✅ Interactive web demo generated: {output_path}")
    print(f"\n📊 Scenario Summary:")
    print(f"   Fire: {fire_name}")
    print(f"   Size: {fire_size} acres")
    print(f"   Total steps: {summary['total_steps']}")
    print(f"   Fire contained: {'Yes' if summary['fire_contained'] else 'No'}")
    print(f"   Final containment: {summary['final_containment']*100:.1f}%")
    print(f"   LLM guidance calls: {llm_calls}")
    print(f"\n🌐 Open {output_path} in a web browser to view the demo!")


def main():
    parser = argparse.ArgumentParser(description='Generate interactive web demo from telemetry')
    parser.add_argument('--telemetry', type=str, default='results/demo_telemetry.json',
                       help='Path to telemetry JSON file')
    parser.add_argument('--output', type=str, default='results/aurora_isef_demo.html',
                       help='Output HTML file path')
    
    args = parser.parse_args()
    
    generate_web_demo(args.telemetry, args.output)


if __name__ == "__main__":
    main()
