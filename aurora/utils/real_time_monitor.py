"""
Real-time Monitoring System for AURORA

This module provides real-time monitoring capabilities for:
- Live simulation tracking
- Performance metrics
- System health monitoring
- Real-time data visualization
- Alert system
"""

import time
import json
import threading
import psutil
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np


class AURORAMonitor:
    """Real-time monitoring system for AURORA."""
    
    def __init__(self):
        """Initialize the monitoring system."""
        self.start_time = time.time()
        self.metrics_history = []
        self.active_simulations = {}
        self.system_metrics = {}
        self.alerts = []
        self.max_history_size = 1000
        
        # Start monitoring threads
        self.monitoring_active = True
        self.system_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.system_thread.start()
        
        print("🔍 AURORA Real-time Monitor initialized")
    
    def _monitor_system(self):
        """Monitor system resources in background."""
        while self.monitoring_active:
            try:
                # System metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Process metrics
                aurora_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        if 'python' in proc.info['name'].lower():
                            aurora_processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Update system metrics
                self.system_metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available": memory.available,
                    "disk_percent": disk.percent,
                    "disk_free": disk.free,
                    "aurora_processes": aurora_processes,
                    "uptime": time.time() - self.start_time
                }
                
                # Check for alerts
                self._check_alerts()
                
                # Store in history
                self.metrics_history.append(self.system_metrics.copy())
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                time.sleep(10)
    
    def _check_alerts(self):
        """Check for system alerts."""
        alerts = []
        
        # CPU alert
        if self.system_metrics.get('cpu_percent', 0) > 80:
            alerts.append({
                "type": "warning",
                "message": f"High CPU usage: {self.system_metrics['cpu_percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # Memory alert
        if self.system_metrics.get('memory_percent', 0) > 85:
            alerts.append({
                "type": "warning",
                "message": f"High memory usage: {self.system_metrics['memory_percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # Disk alert
        if self.system_metrics.get('disk_percent', 0) > 90:
            alerts.append({
                "type": "critical",
                "message": f"Low disk space: {100 - self.system_metrics['disk_percent']:.1f}% free",
                "timestamp": datetime.now().isoformat()
            })
        
        # Add new alerts
        for alert in alerts:
            if alert not in self.alerts:
                self.alerts.append(alert)
        
        # Keep only recent alerts (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = [
            alert for alert in self.alerts 
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
    
    def register_simulation(self, simulation_id: str, simulation_type: str, config: Dict[str, Any]):
        """Register a new simulation for monitoring."""
        self.active_simulations[simulation_id] = {
            "type": simulation_type,
            "config": config,
            "start_time": time.time(),
            "status": "running",
            "metrics": {
                "steps": 0,
                "fire_coverage": 0.0,
                "suppressions": 0,
                "active_drones": 0,
                "battery_levels": [],
                "water_levels": []
            }
        }
        print(f"📊 Registered simulation: {simulation_id} ({simulation_type})")
    
    def update_simulation(self, simulation_id: str, metrics: Dict[str, Any]):
        """Update simulation metrics."""
        if simulation_id in self.active_simulations:
            self.active_simulations[simulation_id]["metrics"].update(metrics)
            self.active_simulations[simulation_id]["last_update"] = time.time()
    
    def complete_simulation(self, simulation_id: str, final_metrics: Dict[str, Any]):
        """Mark simulation as completed."""
        if simulation_id in self.active_simulations:
            sim = self.active_simulations[simulation_id]
            sim["status"] = "completed"
            sim["end_time"] = time.time()
            sim["duration"] = sim["end_time"] - sim["start_time"]
            sim["final_metrics"] = final_metrics
            
            # Move to completed simulations
            self._save_completed_simulation(simulation_id, sim)
            
            print(f"✅ Simulation completed: {simulation_id} (Duration: {sim['duration']:.1f}s)")
    
    def _save_completed_simulation(self, simulation_id: str, simulation_data: Dict[str, Any]):
        """Save completed simulation data."""
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # Save to JSON file
        simulation_file = results_dir / f"simulation_{simulation_id}.json"
        with open(simulation_file, 'w') as f:
            json.dump(simulation_data, f, indent=2, default=str)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - self.start_time,
            "system_metrics": self.system_metrics,
            "active_simulations": len(self.active_simulations),
            "total_alerts": len(self.alerts),
            "monitoring_active": self.monitoring_active
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self.system_metrics,
            "aurora": {
                "total_simulations": len(self.active_simulations) + len(self._get_completed_simulations()),
                "active_simulations": len(self.active_simulations),
                "data_sources": ["NASA FIRMS", "NOAA Weather", "USGS Elevation"],
                "ai_models": ["DialoGPT", "World Model", "PPO Agents"],
                "recent_alerts": self.alerts[-5:] if self.alerts else []
            }
        }
    
    def get_simulation_history(self) -> Dict[str, Any]:
        """Get simulation history."""
        completed_sims = self._get_completed_simulations()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_simulations": list(self.active_simulations.values()),
            "recent_simulations": completed_sims[-10:],  # Last 10 completed
            "total_completed": len(completed_sims)
        }
    
    def _get_completed_simulations(self) -> List[Dict[str, Any]]:
        """Get list of completed simulations."""
        completed = []
        results_dir = Path("results")
        
        if results_dir.exists():
            for file in results_dir.glob("simulation_*.json"):
                try:
                    with open(file, 'r') as f:
                        sim_data = json.load(f)
                        completed.append(sim_data)
                except Exception as e:
                    print(f"⚠️  Error reading {file}: {e}")
        
        # Sort by completion time
        completed.sort(key=lambda x: x.get('end_time', 0), reverse=True)
        return completed
    
    def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get metrics history for the last N hours."""
        cutoff_time = time.time() - (hours * 3600)
        return [
            metric for metric in self.metrics_history 
            if metric.get('timestamp', 0) > cutoff_time
        ]
    
    def stop_monitoring(self):
        """Stop the monitoring system."""
        self.monitoring_active = False
        print("🛑 AURORA Monitor stopped")


# Global monitor instance
aurora_monitor = AURORAMonitor()


def get_monitor() -> AURORAMonitor:
    """Get the global monitor instance."""
    return aurora_monitor


def create_monitoring_dashboard() -> str:
    """Create a real-time monitoring dashboard HTML."""
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AURORA - Real-time Monitoring Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .metric-card h3 {
            margin-top: 0;
            color: #ffd700;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .chart-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .alerts {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .alert-item {
            background: rgba(255, 193, 7, 0.2);
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            border-left: 4px solid #ffc107;
        }
        .alert-critical {
            background: rgba(220, 53, 69, 0.2);
            border-left-color: #dc3545;
        }
        .refresh-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background: #218838;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 AURORA Real-time Monitor</h1>
            <p>Live system monitoring and performance tracking</p>
        </div>
        
        <button class="refresh-btn" onclick="refreshAll()">🔄 Refresh All Data</button>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>🖥️ CPU Usage</h3>
                <div class="metric-value" id="cpuUsage">--</div>
                <div>System CPU utilization</div>
            </div>
            <div class="metric-card">
                <h3>💾 Memory Usage</h3>
                <div class="metric-value" id="memoryUsage">--</div>
                <div>System memory utilization</div>
            </div>
            <div class="metric-card">
                <h3>💿 Disk Usage</h3>
                <div class="metric-value" id="diskUsage">--</div>
                <div>Available disk space</div>
            </div>
            <div class="metric-card">
                <h3>🚀 Active Simulations</h3>
                <div class="metric-value" id="activeSims">--</div>
                <div>Currently running simulations</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>📈 System Performance Over Time</h3>
            <div id="performanceChart"></div>
        </div>
        
        <div class="alerts">
            <h3>⚠️ System Alerts</h3>
            <div id="alertsList">
                <div class="alert-item">
                    <strong>No alerts</strong> - System running normally
                </div>
            </div>
        </div>
    </div>

    <script>
        let performanceData = {
            timestamps: [],
            cpu: [],
            memory: [],
            disk: []
        };
        
        function refreshAll() {
            loadSystemMetrics();
            loadPerformanceData();
            loadAlerts();
        }
        
        function loadSystemMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('cpuUsage').textContent = data.performance.cpu_usage;
                    document.getElementById('memoryUsage').textContent = data.performance.memory_usage;
                    document.getElementById('diskUsage').textContent = data.performance.disk_usage;
                    document.getElementById('activeSims').textContent = data.aurora_metrics.active_models;
                })
                .catch(error => console.log('Error loading metrics:', error));
        }
        
        function loadPerformanceData() {
            // Simulate performance data for demo
            const now = new Date();
            performanceData.timestamps.push(now);
            performanceData.cpu.push(Math.random() * 30 + 10);
            performanceData.memory.push(Math.random() * 20 + 30);
            performanceData.disk.push(Math.random() * 10 + 20);
            
            // Keep only last 20 points
            if (performanceData.timestamps.length > 20) {
                performanceData.timestamps.shift();
                performanceData.cpu.shift();
                performanceData.memory.shift();
                performanceData.disk.shift();
            }
            
            // Update chart
            const trace1 = {
                x: performanceData.timestamps,
                y: performanceData.cpu,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'CPU %',
                line: {color: '#ff6b6b'}
            };
            
            const trace2 = {
                x: performanceData.timestamps,
                y: performanceData.memory,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Memory %',
                line: {color: '#4ecdc4'}
            };
            
            const trace3 = {
                x: performanceData.timestamps,
                y: performanceData.disk,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Disk %',
                line: {color: '#45b7d1'}
            };
            
            const layout = {
                title: 'System Performance Metrics',
                xaxis: {title: 'Time'},
                yaxis: {title: 'Usage %'},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {color: 'white'}
            };
            
            Plotly.newPlot('performanceChart', [trace1, trace2, trace3], layout);
        }
        
        function loadAlerts() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    const alertsList = document.getElementById('alertsList');
                    const alerts = data.aurora.recent_alerts || [];
                    
                    if (alerts.length === 0) {
                        alertsList.innerHTML = '<div class="alert-item"><strong>No alerts</strong> - System running normally</div>';
                    } else {
                        alertsList.innerHTML = '';
                        alerts.forEach(alert => {
                            const alertDiv = document.createElement('div');
                            alertDiv.className = `alert-item ${alert.type === 'critical' ? 'alert-critical' : ''}`;
                            alertDiv.innerHTML = `<strong>${alert.type.toUpperCase()}:</strong> ${alert.message}`;
                            alertsList.appendChild(alertDiv);
                        });
                    }
                })
                .catch(error => console.log('Error loading alerts:', error));
        }
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            refreshAll();
            
            // Refresh every 10 seconds
            setInterval(() => {
                loadSystemMetrics();
                loadPerformanceData();
                loadAlerts();
            }, 10000);
        });
    </script>
</body>
</html>
"""
    
    # Save dashboard
    dashboard_path = Path("results/aurora_monitoring_dashboard.html")
    dashboard_path.parent.mkdir(exist_ok=True)
    
    with open(dashboard_path, 'w') as f:
        f.write(dashboard_html)
    
    print(f"✅ Real-time monitoring dashboard created: {dashboard_path}")
    return str(dashboard_path)


def main():
    """Test the monitoring system."""
    print("🔍 Testing AURORA Real-time Monitor")
    print("=" * 50)
    
    # Create monitoring dashboard
    dashboard_path = create_monitoring_dashboard()
    
    # Test monitoring for a few seconds
    print("📊 Monitoring system metrics for 30 seconds...")
    for i in range(6):
        status = aurora_monitor.get_system_status()
        print(f"Status: CPU {status['system_metrics'].get('cpu_percent', 0):.1f}%, "
              f"Memory {status['system_metrics'].get('memory_percent', 0):.1f}%, "
              f"Uptime {status['uptime']:.1f}s")
        time.sleep(5)
    
    print(f"\n✅ Monitoring test complete!")
    print(f"📊 Dashboard available at: {dashboard_path}")
    print("💡 Use the web server to view the dashboard: ./run.sh web-server")


if __name__ == "__main__":
    main() 