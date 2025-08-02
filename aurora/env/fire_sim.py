"""
Enhanced FireSim module for the AURORA wildfire simulator.

This module contains the ``FireSim`` class which encapsulates the core
wildfire dynamics used throughout the AURORA project.  The simulator
maintains multiple pieces of state: the static terrain map, elevation
map, fuel density map, and the dynamic fire map indicating which cells
are unburned, currently burning or have already burnt out.

The fire logic now includes:
- Wind effects on fire spread direction and intensity
- Elevation effects (fire spreads faster downhill)
- Fuel density variability
- Weather conditions (humidity, temperature)
- More realistic fire spread patterns
"""

from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import random


class FireSim:
    """Enhanced 2D wildfire simulator with wind, elevation, and fuel modeling.

    The simulator loads a numpy terrain map on construction.  Each
    integer entry in the terrain array denotes a different terrain
    type:

      * 0 – empty / non‑vegetated
      * 1 – forest (flammable)
      * 2 – road (non‑flammable)
      * 3 – water (non‑flammable)

    The dynamic fire state is stored separately as an integer array of
    the same shape.  The semantics of the fire state are:

      * 0 – unburned / safe
      * 1 – currently burning
      * 2 – burnt (no longer burning)

    New features:
      * Wind direction and intensity affect fire spread
      * Elevation affects spread rate (downhill faster)
      * Fuel density varies by cell
      * Weather conditions (humidity, temperature)
    """

    def __init__(self, map_path: str | Path = "data/terrain_map.npy", 
                 wind_direction: Tuple[float, float] = (0.0, 0.0),
                 wind_intensity: float = 1.0,
                 humidity: float = 0.5,
                 temperature: float = 25.0) -> None:
        # Resolve the path relative to this file so that the simulator
        # works correctly when executed from other directories.
        map_file = Path(__file__).resolve().parent.parent / map_path
        if not map_file.exists():
            raise FileNotFoundError(f"Terrain map file not found: {map_file}")
        
        self.terrain: np.ndarray = np.load(map_file)
        if self.terrain.ndim != 2:
            raise ValueError("Terrain map must be a 2D array")
        
        self.grid_size: Tuple[int, int] = self.terrain.shape
        
        # Fire state array: 0=safe, 1=burning, 2=burnt
        self.fire_state: np.ndarray = np.zeros(self.grid_size, dtype=np.uint8)
        
        # Step counter
        self.step_count: int = 0
        
        # Wind parameters (direction vector and intensity)
        self.wind_direction = np.array(wind_direction, dtype=np.float32)
        self.wind_intensity = wind_intensity
        
        # Weather conditions
        self.humidity = humidity  # 0.0 = dry, 1.0 = very humid
        self.temperature = temperature  # Celsius
        
        # Generate elevation map (higher values = higher elevation)
        self.elevation = self._generate_elevation_map()
        
        # Generate fuel density map (higher values = more flammable)
        self.fuel_density = self._generate_fuel_density_map()
        
        # Initialize fire at the centre of the map
        self.reset()

    def _generate_elevation_map(self) -> np.ndarray:
        """Generate a realistic elevation map with hills and valleys."""
        from scipy.ndimage import gaussian_filter
        
        # Create random elevation with some structure
        elevation = np.random.rand(*self.grid_size)
        elevation = gaussian_filter(elevation, sigma=2.0)
        
        # Scale to reasonable elevation values (0-100 meters)
        elevation = elevation * 100
        
        # Add some terrain features
        # Water areas are lower elevation
        elevation[self.terrain == 3] *= 0.1
        
        return elevation.astype(np.float32)

    def _generate_fuel_density_map(self) -> np.ndarray:
        """Generate fuel density map based on terrain and elevation."""
        fuel = np.zeros(self.grid_size, dtype=np.float32)
        
        # Forest areas have high fuel density
        fuel[self.terrain == 1] = np.random.uniform(0.7, 1.0, 
                                                   np.sum(self.terrain == 1))
        
        # Empty areas have low fuel density
        fuel[self.terrain == 0] = np.random.uniform(0.1, 0.3, 
                                                   np.sum(self.terrain == 0))
        
        # Roads and water have no fuel
        fuel[self.terrain == 2] = 0.0
        fuel[self.terrain == 3] = 0.0
        
        return fuel

    def set_wind(self, direction: Tuple[float, float], intensity: float) -> None:
        """Update wind conditions during simulation."""
        self.wind_direction = np.array(direction, dtype=np.float32)
        self.wind_intensity = max(0.0, intensity)

    def set_weather(self, humidity: float, temperature: float) -> None:
        """Update weather conditions during simulation."""
        self.humidity = max(0.0, min(1.0, humidity))
        self.temperature = temperature

    def _calculate_spread_probability(self, from_pos: Tuple[int, int], 
                                    to_pos: Tuple[int, int]) -> float:
        """Calculate probability of fire spreading from one cell to another."""
        if self.terrain[to_pos] != 1:  # Not forest
            return 0.0
        
        if self.fire_state[to_pos] != 0:  # Already burning or burnt
            return 0.0
        
        # Base probability
        base_prob = 0.3
        
        # Wind effect
        wind_effect = 0.0
        if self.wind_intensity > 0:
            # Calculate direction from source to target
            direction = np.array([to_pos[0] - from_pos[0], to_pos[1] - from_pos[1]])
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
                # Wind alignment (dot product)
                wind_alignment = np.dot(direction, self.wind_direction)
                wind_effect = wind_alignment * self.wind_intensity * 0.2
        
        # Elevation effect (fire spreads faster downhill)
        elevation_diff = self.elevation[from_pos] - self.elevation[to_pos]
        elevation_effect = elevation_diff / 100.0 * 0.1  # Normalize by max elevation
        
        # Fuel density effect
        fuel_effect = self.fuel_density[to_pos] * 0.3
        
        # Weather effects
        humidity_effect = -self.humidity * 0.2  # Humidity reduces spread
        temperature_effect = (self.temperature - 20) / 30 * 0.1  # Higher temp = faster spread
        
        # Combine all effects
        total_prob = base_prob + wind_effect + elevation_effect + fuel_effect + humidity_effect + temperature_effect
        
        return max(0.0, min(1.0, total_prob))

    def reset(self) -> None:
        """Reset the fire state to the initial configuration.

        All cells are marked safe except for the centre cell which is set
        to burning.  Resets the internal step counter.
        """
        self.fire_state.fill(0)
        centre = (self.grid_size[0] // 2, self.grid_size[1] // 2)
        self.fire_state[centre] = 1
        self.step_count = 0

    def step(self) -> None:
        """Advance the fire simulation by one time step.

        Enhanced fire spread with wind, elevation, and fuel effects.
        """
        new_state = self.fire_state.copy()
        
        # Find all currently burning cells
        burning_indices = np.argwhere(self.fire_state == 1)
        
        for r, c in burning_indices:
            # Current burning cell becomes burnt
            new_state[r, c] = 2
            
            # Check all 8 neighboring cells
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue  # Skip the cell itself
                    
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.grid_size[0] and 0 <= nc < self.grid_size[1]:
                        # Calculate spread probability
                        spread_prob = self._calculate_spread_probability((r, c), (nr, nc))
                        
                        # Apply probabilistic spread
                        if random.random() < spread_prob:
                            new_state[nr, nc] = 1
        
        self.fire_state = new_state
        self.step_count += 1

    def is_fire_active(self) -> bool:
        """Return ``True`` if there is at least one burning cell."""
        return bool(np.any(self.fire_state == 1))

    def get_fire_coverage(self) -> float:
        """Compute the fraction of forest tiles that have been touched by fire.

        Both burning and burnt cells are counted as fire‑affected.  If there
        are no forest tiles on the map the coverage defaults to zero.
        """
        forest_cells = (self.terrain == 1)
        total_forest = float(np.count_nonzero(forest_cells))
        if total_forest == 0:
            return 0.0
        fire_cells = np.logical_and(forest_cells, self.fire_state > 0)
        return float(np.count_nonzero(fire_cells)) / total_forest

    def get_fire_intensity(self) -> float:
        """Get the current fire intensity (number of burning cells)."""
        return float(np.count_nonzero(self.fire_state == 1))

    def get_weather_info(self) -> dict:
        """Get current weather and environmental conditions."""
        return {
            'wind_direction': self.wind_direction.tolist(),
            'wind_intensity': self.wind_intensity,
            'humidity': self.humidity,
            'temperature': self.temperature,
            'step_count': self.step_count
        }

    def copy(self) -> "FireSim":
        """Return a deep copy of the simulator.

        Useful for training environments to duplicate the state of the
        simulator without affecting the original instance.
        """
        clone = object.__new__(FireSim)
        clone.terrain = self.terrain
        clone.grid_size = self.grid_size
        clone.fire_state = self.fire_state.copy()
        clone.step_count = self.step_count
        clone.wind_direction = self.wind_direction.copy()
        clone.wind_intensity = self.wind_intensity
        clone.humidity = self.humidity
        clone.temperature = self.temperature
        clone.elevation = self.elevation.copy()
        clone.fuel_density = self.fuel_density.copy()
        return clone