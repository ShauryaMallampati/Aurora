"""
Drone agent for wildfire suppression.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Optional, List, Dict, Any
import random

try:
    from ..env.fire_sim import FireSim
except ImportError:
    from env.fire_sim import FireSim


class DroneAgent:
    """Individual drone with battery, water, sensors, and movement."""

    ACTIONS = {
        0: "stay",
        1: "up",
        2: "down", 
        3: "left",
        4: "right",
        5: "suppress",
        6: "scan",
        7: "communicate",
    }

    def __init__(self, start_pos: Tuple[int, int], 
                 agent_id: str = None,
                 cooldown_steps: int = 3,
                 max_battery: float = 100.0,
                 max_water: float = 50.0,
                 sensor_range: int = 5,
                 communication_range: int = 8) -> None:
        """Initialize drone at given position."""
        self.position = list(start_pos)
        self.agent_id = agent_id or f"drone_{random.randint(1000, 9999)}"
        self.cooldown_steps = cooldown_steps
        self._cooldown = 0
        
        # Battery and resource management
        self.max_battery = max_battery
        self.battery = max_battery
        self.battery_drain_rate = 1.0  # per step
        self.recharge_rate = 5.0  # per step when at recharge zone
        
        # Water capacity for fire suppression
        self.max_water = max_water
        self.water = max_water
        self.water_per_suppression = 10.0
        
        # Sensor and communication capabilities
        self.sensor_range = sensor_range
        self.communication_range = communication_range
        self.field_of_view = 3  # 3x3 observation window
        
        # Agent state and history
        self.is_active = True
        self.faults = []  # List of current faults
        self.action_history = []
        self.suppression_count = 0
        self.distance_traveled = 0
        
        # Communication state
        self.last_communication = 0
        self.received_messages = []
        self.sent_messages = []

    @property
    def cooldown(self) -> int:
        """Remaining cooldown steps before next suppression."""
        return self._cooldown

    @property
    def battery_percentage(self) -> float:
        """Return battery level as a percentage."""
        return (self.battery / self.max_battery) * 100.0

    @property
    def water_percentage(self) -> float:
        """Return water level as a percentage."""
        return (self.water / self.max_water) * 100.0

    def is_at_recharge_zone(self, fire_sim: FireSim) -> bool:
        """Check if drone is at a refill location (road or water)."""
        r, c = self.position
        return fire_sim.terrain[r, c] in [2, 3]  # Road or water

    def can_suppress(self) -> bool:
        """Check if drone can perform suppression action."""
        return (self._cooldown == 0 and 
                self.water >= self.water_per_suppression and
                self.battery > 10.0 and  # Need some battery to operate
                self.is_active)

    def observe(self, fire_sim: FireSim) -> np.ndarray:
        """Get 3x3 observation grid with terrain, fire, and drone state."""
        r, c = self.position
        obs = np.zeros((self.field_of_view, self.field_of_view, 6), dtype=np.float32)
        
        for i in range(-1, 2):
            for j in range(-1, 2):
                rr, cc = r + i, c + j
                if 0 <= rr < fire_sim.grid_size[0] and 0 <= cc < fire_sim.grid_size[1]:
                    obs[i + 1, j + 1, 0] = fire_sim.terrain[rr, cc]
                    obs[i + 1, j + 1, 1] = fire_sim.fire_state[rr, cc]
                    obs[i + 1, j + 1, 2] = fire_sim.elevation[rr, cc] / 100.0  # Normalize
                    obs[i + 1, j + 1, 3] = fire_sim.fuel_density[rr, cc]
                
                # Add agent state to center cell
                if i == 0 and j == 0:
                    obs[i + 1, j + 1, 4] = self.battery_percentage / 100.0
                    obs[i + 1, j + 1, 5] = self.water_percentage / 100.0
        
        return obs

    def scan_environment(self, fire_sim: FireSim) -> Dict[str, Any]:
        """Detailed scan of fires, recharge zones, and weather nearby."""
        r, c = self.position
        scan_data = {
            'nearby_fires': [],
            'recharge_zones': [],
            'other_agents': [],
            'terrain_features': {},
            'weather_info': fire_sim.get_weather_info()
        }
        
        # Scan for fires within sensor range
        for dr in range(-self.sensor_range, self.sensor_range + 1):
            for dc in range(-self.sensor_range, self.sensor_range + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < fire_sim.grid_size[0] and 0 <= nc < fire_sim.grid_size[1]:
                    if fire_sim.fire_state[nr, nc] == 1:  # Burning
                        distance = abs(dr) + abs(dc)  # Manhattan distance
                        scan_data['nearby_fires'].append({
                            'position': (nr, nc),
                            'distance': distance,
                            'intensity': fire_sim.fuel_density[nr, nc]
                        })
                    
                    # Check for recharge zones
                    if fire_sim.terrain[nr, nc] in [2, 3]:  # Road or water
                        distance = abs(dr) + abs(dc)
                        scan_data['recharge_zones'].append({
                            'position': (nr, nc),
                            'distance': distance,
                            'type': 'road' if fire_sim.terrain[nr, nc] == 2 else 'water'
                        })
        
        return scan_data

    def communicate(self, other_agents: List['DroneAgent'], fire_sim: FireSim) -> List[Dict[str, Any]]:
        """Share position and scan data with nearby drones."""
        messages = []
        r, c = self.position
        
        for agent in other_agents:
            if agent.agent_id == self.agent_id:
                continue
                
            ar, ac = agent.position
            distance = abs(r - ar) + abs(c - ac)
            
            if distance <= self.communication_range:
                message = {
                    'from': self.agent_id,
                    'to': agent.agent_id,
                    'position': self.position,
                    'battery': self.battery_percentage,
                    'water': self.water_percentage,
                    'scan_data': self.scan_environment(fire_sim),
                    'timestamp': fire_sim.step_count
                }
                
                agent.received_messages.append(message)
                messages.append(message)
        
        self.sent_messages.extend(messages)
        self.last_communication = fire_sim.step_count
        return messages

    def _update_resources(self, fire_sim: FireSim) -> None:
        """Update battery/water and handle depletion."""
        # Drain battery
        self.battery = max(0.0, self.battery - self.battery_drain_rate)
        
        # Recharge if at recharge zone
        if self.is_at_recharge_zone(fire_sim):
            self.battery = min(self.max_battery, self.battery + self.recharge_rate)
            self.water = min(self.max_water, self.water + self.recharge_rate * 0.5)
        
        # Deactivate if battery is critically low
        if self.battery <= 0:
            self.is_active = False
            self.faults.append('battery_depleted')

    def _simulate_faults(self) -> None:
        """Random fault simulation for realism."""
        # 1% chance per step of developing a fault
        if random.random() < 0.01:
            fault_types = ['sensor_malfunction', 'communication_error', 'suppression_system_fault']
            fault = random.choice(fault_types)
            if fault not in self.faults:
                self.faults.append(fault)
        
        # 5% chance per step of recovering from a fault
        if self.faults and random.random() < 0.05:
            recovered_fault = random.choice(self.faults)
            self.faults.remove(recovered_fault)

    def act(self, action: int, fire_sim: FireSim, other_agents: List['DroneAgent'] = None) -> Dict[str, Any]:
        """Execute action and return result dict."""
        if not self.is_active:
            return {'action': 'inactive', 'suppressed': False, 'message': 'Agent is inactive'}
        
        result = {
            'action': self.ACTIONS.get(int(action), 'unknown'),
            'suppressed': False,
            'battery_used': 0.0,
            'water_used': 0.0,
            'distance_moved': 0,
            'messages_sent': 0,
            'scan_data': None
        }
        
        # Update resources and check for faults
        self._update_resources(fire_sim)
        self._simulate_faults()
        
        # Decrement cooldown at the start of the step
        if self._cooldown > 0:
            self._cooldown -= 1
        
        # Execute action
        if action == 1:  # up
            if self.position[0] > 0:
                self.position[0] -= 1
                result['distance_moved'] = 1
        elif action == 2:  # down
            if self.position[0] < fire_sim.grid_size[0] - 1:
                self.position[0] += 1
                result['distance_moved'] = 1
        elif action == 3:  # left
            if self.position[1] > 0:
                self.position[1] -= 1
                result['distance_moved'] = 1
        elif action == 4:  # right
            if self.position[1] < fire_sim.grid_size[1] - 1:
                self.position[1] += 1
                result['distance_moved'] = 1
        elif action == 5:  # suppress
            if self.can_suppress():
                # Check orthogonally adjacent cells for fire
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = self.position[0] + dr, self.position[1] + dc
                    if 0 <= nr < fire_sim.grid_size[0] and 0 <= nc < fire_sim.grid_size[1]:
                        if fire_sim.fire_state[nr, nc] == 1:
                            fire_sim.fire_state[nr, nc] = 2  # extinguish burning cell
                            self._cooldown = self.cooldown_steps
                            self.water -= self.water_per_suppression
                            self.suppression_count += 1
                            result['suppressed'] = True
                            result['water_used'] = self.water_per_suppression
                            break
        elif action == 6:  # scan
            result['scan_data'] = self.scan_environment(fire_sim)
            result['battery_used'] = 0.5  # Scanning uses extra battery
        elif action == 7:  # communicate
            if other_agents:
                messages = self.communicate(other_agents, fire_sim)
                result['messages_sent'] = len(messages)
                result['battery_used'] = 0.2  # Communication uses some battery
        
        # Update metrics
        self.distance_traveled += result['distance_moved']
        self.battery -= result['battery_used']
        self.action_history.append({
            'step': fire_sim.step_count,
            'action': action,
            'position': self.position.copy(),
            'result': result
        })
        
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get current drone state snapshot."""
        return {
            'agent_id': self.agent_id,
            'position': self.position,
            'is_active': self.is_active,
            'battery_percentage': self.battery_percentage,
            'water_percentage': self.water_percentage,
            'cooldown': self.cooldown,
            'faults': self.faults.copy(),
            'suppression_count': self.suppression_count,
            'distance_traveled': self.distance_traveled,
            'total_actions': len(self.action_history)
        }

    def reset(self, start_pos: Optional[Tuple[int, int]] = None) -> None:
        """Reset drone to initial state."""
        if start_pos is not None:
            self.position = list(start_pos)
        
        self._cooldown = 0
        self.battery = self.max_battery
        self.water = self.max_water
        self.is_active = True
        self.faults = []
        self.action_history = []
        self.suppression_count = 0
        self.distance_traveled = 0
        self.received_messages = []
        self.sent_messages = []