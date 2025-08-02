"""
Massive Training Data Generator for AURORA

This module generates massive amounts of diverse training data for AURORA AI models.
Features:
- Multiple terrain types and configurations
- Various weather conditions
- Different fire scenarios
- Multiple drone configurations
- Realistic environmental conditions
- Large-scale data generation for AI training
"""

import numpy as np
import pandas as pd
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import random
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available. Install with: pip install scikit-learn")


class MassiveTrainingGenerator:
    """Generator for massive amounts of diverse training data."""
    
    def __init__(self, output_dir: str = "data/massive_training_data"):
        """
        Initialize the massive training generator.
        
        Args:
            output_dir: Directory to save generated data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Training data storage
        self.scenarios = []
        self.training_data = []
        self.metadata = {
            "generator_version": "1.0",
            "created_at": datetime.now().isoformat(),
            "total_scenarios": 0,
            "data_types": ["terrain", "weather", "fire", "drones", "actions", "rewards"]
        }
        
        # Scenario templates
        self.terrain_templates = {
            "forest_dense": {"forest_prob": 0.8, "water_prob": 0.05, "road_prob": 0.05},
            "forest_sparse": {"forest_prob": 0.6, "water_prob": 0.1, "road_prob": 0.1},
            "mixed_terrain": {"forest_prob": 0.4, "water_prob": 0.2, "road_prob": 0.2},
            "urban_interface": {"forest_prob": 0.3, "water_prob": 0.1, "road_prob": 0.4},
            "mountainous": {"forest_prob": 0.5, "water_prob": 0.15, "road_prob": 0.1},
            "coastal": {"forest_prob": 0.4, "water_prob": 0.3, "road_prob": 0.1}
        }
        
        self.weather_templates = {
            "calm": {"wind_speed_range": (0, 5), "humidity_range": (60, 80), "temp_range": (60, 75)},
            "moderate": {"wind_speed_range": (5, 15), "humidity_range": (40, 60), "temp_range": (75, 85)},
            "severe": {"wind_speed_range": (15, 30), "humidity_range": (20, 40), "temp_range": (85, 95)},
            "extreme": {"wind_speed_range": (30, 50), "humidity_range": (10, 30), "temp_range": (95, 105)}
        }
        
        self.fire_templates = {
            "small_outbreak": {"fire_size": (5, 15), "spread_rate": "slow"},
            "medium_fire": {"fire_size": (15, 50), "spread_rate": "moderate"},
            "large_fire": {"fire_size": (50, 100), "spread_rate": "fast"},
            "mega_fire": {"fire_size": (100, 200), "spread_rate": "extreme"}
        }
        
        self.drone_templates = {
            "minimal": {"num_drones": 1, "battery_range": (80, 100), "water_range": (80, 100)},
            "standard": {"num_drones": 3, "battery_range": (60, 100), "water_range": (60, 100)},
            "extended": {"num_drones": 5, "battery_range": (40, 100), "water_range": (40, 100)},
            "massive": {"num_drones": 10, "battery_range": (20, 100), "water_range": (20, 100)}
        }

    def generate_terrain(self, template: str, size: int = 50) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate terrain based on template.
        
        Args:
            template: Terrain template name
            size: Map size
            
        Returns:
            Tuple of (terrain_type, elevation)
        """
        if template not in self.terrain_templates:
            template = "mixed_terrain"
        
        config = self.terrain_templates[template]
        
        # Generate terrain types
        terrain = np.zeros((size, size), dtype=int)
        
        # Fill with forest
        forest_mask = np.random.random((size, size)) < config["forest_prob"]
        terrain[forest_mask] = 1
        
        # Add water bodies
        water_mask = np.random.random((size, size)) < config["water_prob"]
        terrain[water_mask] = 3
        
        # Add roads
        road_mask = np.random.random((size, size)) < config["road_prob"]
        terrain[road_mask] = 2
        
        # Generate elevation
        elevation = self._generate_elevation(size, template)
        
        return terrain, elevation
    
    def _generate_elevation(self, size: int, template: str) -> np.ndarray:
        """Generate realistic elevation data."""
        elevation = np.random.rand(size, size) * 50  # Base elevation
        
        if template == "mountainous":
            # Create mountain ranges
            for _ in range(3):
                center_x = np.random.randint(0, size)
                center_y = np.random.randint(0, size)
                height = np.random.uniform(100, 300)
                
                for i in range(size):
                    for j in range(size):
                        distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                        if distance < size/4:
                            elevation[i, j] += height * np.exp(-distance / (size/8))
        
        elif template == "coastal":
            # Create coastal gradient
            for i in range(size):
                for j in range(size):
                    distance_from_coast = min(i, j, size-i, size-j)
                    elevation[i, j] += 20 * (1 - distance_from_coast / size)
        
        return elevation
    
    def generate_weather_sequence(self, template: str, duration: int = 50) -> List[Dict]:
        """
        Generate weather sequence based on template.
        
        Args:
            template: Weather template name
            duration: Number of time steps
            
        Returns:
            List of weather conditions
        """
        if template not in self.weather_templates:
            template = "moderate"
        
        config = self.weather_templates[template]
        weather_sequence = []
        
        for step in range(duration):
            weather = {
                "step": step,
                "temperature": np.random.uniform(*config["temp_range"]),
                "humidity": np.random.uniform(*config["humidity_range"]),
                "wind_speed": np.random.uniform(*config["wind_speed_range"]),
                "wind_direction": np.random.choice(['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW']),
                "pressure": np.random.uniform(29.5, 30.5),
                "visibility": np.random.uniform(5, 15)
            }
            weather_sequence.append(weather)
        
        return weather_sequence
    
    def generate_fire_scenario(self, template: str, terrain: np.ndarray, size: int = 50) -> Dict:
        """
        Generate fire scenario based on template.
        
        Args:
            template: Fire template name
            terrain: Terrain array
            size: Map size
            
        Returns:
            Fire scenario configuration
        """
        if template not in self.fire_templates:
            template = "medium_fire"
        
        config = self.fire_templates[template]
        
        # Find suitable fire starting locations (forest areas)
        forest_locations = np.where(terrain == 1)
        if len(forest_locations[0]) == 0:
            # No forest, use center
            start_x, start_y = size // 2, size // 2
        else:
            # Random forest location
            idx = np.random.randint(len(forest_locations[0]))
            start_x, start_y = forest_locations[1][idx], forest_locations[0][idx]
        
        fire_size = np.random.randint(*config["fire_size"])
        
        scenario = {
            "start_location": (start_x, start_y),
            "initial_size": fire_size,
            "spread_rate": config["spread_rate"],
            "fuel_density": np.random.uniform(0.5, 1.5),
            "fire_type": template
        }
        
        return scenario
    
    def generate_drone_configuration(self, template: str, size: int = 50) -> List[Dict]:
        """
        Generate drone configuration based on template.
        
        Args:
            template: Drone template name
            size: Map size
            
        Returns:
            List of drone configurations
        """
        if template not in self.drone_templates:
            template = "standard"
        
        config = self.drone_templates[template]
        drones = []
        
        for i in range(config["num_drones"]):
            drone = {
                "id": f"drone_{i}",
                "start_position": (
                    np.random.randint(0, size),
                    np.random.randint(0, size)
                ),
                "battery_percentage": np.random.uniform(*config["battery_range"]),
                "water_percentage": np.random.uniform(*config["water_range"]),
                "max_battery": 100,
                "max_water": 100,
                "suppression_efficiency": np.random.uniform(0.7, 1.0),
                "movement_speed": np.random.uniform(0.8, 1.2),
                "sensor_range": np.random.randint(3, 8)
            }
            drones.append(drone)
        
        return drones
    
    def generate_training_scenario(self, scenario_id: int, complexity: str = "medium") -> Dict:
        """
        Generate a complete training scenario.
        
        Args:
            scenario_id: Unique scenario ID
            complexity: Scenario complexity level
            
        Returns:
            Complete scenario data
        """
        # Select templates based on complexity
        if complexity == "easy":
            terrain_template = np.random.choice(["forest_sparse", "mixed_terrain"])
            weather_template = "calm"
            fire_template = "small_outbreak"
            drone_template = "minimal"
            map_size = 30
        elif complexity == "hard":
            terrain_template = np.random.choice(["mountainous", "urban_interface"])
            weather_template = np.random.choice(["severe", "extreme"])
            fire_template = np.random.choice(["large_fire", "mega_fire"])
            drone_template = np.random.choice(["extended", "massive"])
            map_size = 80
        else:  # medium
            terrain_template = np.random.choice(list(self.terrain_templates.keys()))
            weather_template = np.random.choice(list(self.weather_templates.keys()))
            fire_template = np.random.choice(list(self.fire_templates.keys()))
            drone_template = np.random.choice(list(self.drone_templates.keys()))
            map_size = 50
        
        # Generate components
        terrain, elevation = self.generate_terrain(terrain_template, map_size)
        weather_sequence = self.generate_weather_sequence(weather_template, duration=100)
        fire_scenario = self.generate_fire_scenario(fire_template, terrain, map_size)
        drones = self.generate_drone_configuration(drone_template, map_size)
        
        # Create scenario
        scenario = {
            "scenario_id": scenario_id,
            "complexity": complexity,
            "map_size": map_size,
            "terrain_template": terrain_template,
            "weather_template": weather_template,
            "fire_template": fire_template,
            "drone_template": drone_template,
            "terrain": terrain.tolist(),
            "elevation": elevation.tolist(),
            "weather_sequence": weather_sequence,
            "fire_scenario": fire_scenario,
            "drones": drones,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "estimated_difficulty": self._calculate_difficulty(complexity, fire_template, weather_template),
                "expected_duration": self._estimate_duration(fire_template, drone_template),
                "success_probability": self._estimate_success_probability(complexity, fire_template, drone_template)
            }
        }
        
        return scenario
    
    def _calculate_difficulty(self, complexity: str, fire_template: str, weather_template: str) -> float:
        """Calculate scenario difficulty score."""
        base_scores = {
            "easy": 0.3, "medium": 0.6, "hard": 0.9
        }
        
        fire_scores = {
            "small_outbreak": 0.2, "medium_fire": 0.5, "large_fire": 0.8, "mega_fire": 1.0
        }
        
        weather_scores = {
            "calm": 0.2, "moderate": 0.5, "severe": 0.8, "extreme": 1.0
        }
        
        difficulty = (
            base_scores.get(complexity, 0.5) * 0.4 +
            fire_scores.get(fire_template, 0.5) * 0.3 +
            weather_scores.get(weather_template, 0.5) * 0.3
        )
        
        return min(1.0, difficulty)
    
    def _estimate_duration(self, fire_template: str, drone_template: str) -> int:
        """Estimate scenario duration in steps."""
        fire_durations = {
            "small_outbreak": 20, "medium_fire": 40, "large_fire": 60, "mega_fire": 100
        }
        
        drone_multipliers = {
            "minimal": 1.5, "standard": 1.0, "extended": 0.8, "massive": 0.6
        }
        
        base_duration = fire_durations.get(fire_template, 40)
        multiplier = drone_multipliers.get(drone_template, 1.0)
        
        return int(base_duration * multiplier)
    
    def _estimate_success_probability(self, complexity: str, fire_template: str, drone_template: str) -> float:
        """Estimate probability of successful fire containment."""
        base_probabilities = {
            "easy": 0.9, "medium": 0.7, "hard": 0.4
        }
        
        fire_penalties = {
            "small_outbreak": 0.0, "medium_fire": -0.1, "large_fire": -0.2, "mega_fire": -0.3
        }
        
        drone_boosts = {
            "minimal": -0.2, "standard": 0.0, "extended": 0.1, "massive": 0.2
        }
        
        probability = (
            base_probabilities.get(complexity, 0.7) +
            fire_penalties.get(fire_template, 0.0) +
            drone_boosts.get(drone_template, 0.0)
        )
        
        return max(0.1, min(0.95, probability))
    
    def generate_massive_dataset(self, num_scenarios: int = 1000, 
                               complexity_distribution: Dict[str, float] = None) -> None:
        """
        Generate a massive dataset of training scenarios.
        
        Args:
            num_scenarios: Number of scenarios to generate
            complexity_distribution: Distribution of complexity levels
        """
        if complexity_distribution is None:
            complexity_distribution = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
        
        print(f"🚀 Generating massive training dataset with {num_scenarios} scenarios...")
        
        # Generate scenarios
        for i in range(num_scenarios):
            if i % 100 == 0:
                print(f"📊 Generated {i}/{num_scenarios} scenarios...")
            
            # Select complexity based on distribution
            complexity = np.random.choice(
                list(complexity_distribution.keys()),
                p=list(complexity_distribution.values())
            )
            
            scenario = self.generate_training_scenario(i, complexity)
            self.scenarios.append(scenario)
        
        # Save scenarios
        self._save_scenarios()
        
        # Generate metadata
        self._generate_metadata()
        
        print(f"✅ Generated {num_scenarios} training scenarios!")
        print(f"📁 Data saved to: {self.output_dir}")
    
    def _save_scenarios(self):
        """Save scenarios to files."""
        # Save all scenarios as JSON
        scenarios_file = self.output_dir / "all_scenarios.json"
        with open(scenarios_file, 'w') as f:
            json.dump(self.scenarios, f, indent=2, default=lambda x: int(x) if isinstance(x, np.integer) else float(x) if isinstance(x, np.floating) else x)
        
        # Save scenarios by complexity
        for complexity in ["easy", "medium", "hard"]:
            complexity_scenarios = [s for s in self.scenarios if s["complexity"] == complexity]
            if complexity_scenarios:
                complexity_file = self.output_dir / f"{complexity}_scenarios.json"
                with open(complexity_file, 'w') as f:
                    json.dump(complexity_scenarios, f, indent=2, default=lambda x: int(x) if isinstance(x, np.integer) else float(x) if isinstance(x, np.floating) else x)
        
        # Save as CSV for analysis
        self._save_as_csv()
    
    def _save_as_csv(self):
        """Save scenario metadata as CSV for analysis."""
        csv_data = []
        
        for scenario in self.scenarios:
            row = {
                "scenario_id": scenario["scenario_id"],
                "complexity": scenario["complexity"],
                "map_size": scenario["map_size"],
                "terrain_template": scenario["terrain_template"],
                "weather_template": scenario["weather_template"],
                "fire_template": scenario["fire_template"],
                "drone_template": scenario["drone_template"],
                "num_drones": len(scenario["drones"]),
                "difficulty": scenario["metadata"]["estimated_difficulty"],
                "duration": scenario["metadata"]["expected_duration"],
                "success_probability": scenario["metadata"]["success_probability"]
            }
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data)
        csv_file = self.output_dir / "scenarios_metadata.csv"
        df.to_csv(csv_file, index=False)
    
    def _generate_metadata(self):
        """Generate comprehensive metadata."""
        self.metadata["total_scenarios"] = len(self.scenarios)
        self.metadata["complexity_distribution"] = {}
        self.metadata["template_distributions"] = {}
        
        # Complexity distribution
        for complexity in ["easy", "medium", "hard"]:
            count = len([s for s in self.scenarios if s["complexity"] == complexity])
            self.metadata["complexity_distribution"][complexity] = {
                "count": count,
                "percentage": count / len(self.scenarios) * 100
            }
        
        # Template distributions
        for template_type in ["terrain_template", "weather_template", "fire_template", "drone_template"]:
            self.metadata["template_distributions"][template_type] = {}
            templates = [s[template_type] for s in self.scenarios]
            unique_templates = set(templates)
            
            for template in unique_templates:
                count = templates.count(template)
                self.metadata["template_distributions"][template_type][template] = {
                    "count": count,
                    "percentage": count / len(templates) * 100
                }
        
        # Save metadata
        metadata_file = self.output_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=lambda x: int(x) if isinstance(x, np.integer) else float(x) if isinstance(x, np.floating) else x)
    
    def create_training_batches(self, batch_size: int = 100) -> List[List[Dict]]:
        """
        Create training batches for machine learning.
        
        Args:
            batch_size: Size of each batch
            
        Returns:
            List of scenario batches
        """
        batches = []
        for i in range(0, len(self.scenarios), batch_size):
            batch = self.scenarios[i:i + batch_size]
            batches.append(batch)
        
        return batches
    
    def analyze_dataset(self) -> Dict[str, Any]:
        """
        Analyze the generated dataset.
        
        Returns:
            Analysis results
        """
        if not self.scenarios:
            return {"error": "No scenarios generated"}
        
        analysis = {
            "total_scenarios": len(self.scenarios),
            "complexity_breakdown": {},
            "difficulty_stats": {},
            "template_analysis": {},
            "recommendations": []
        }
        
        # Complexity breakdown
        for complexity in ["easy", "medium", "hard"]:
            complexity_scenarios = [s for s in self.scenarios if s["complexity"] == complexity]
            analysis["complexity_breakdown"][complexity] = {
                "count": len(complexity_scenarios),
                "percentage": len(complexity_scenarios) / len(self.scenarios) * 100
            }
        
        # Difficulty statistics
        difficulties = [s["metadata"]["estimated_difficulty"] for s in self.scenarios]
        analysis["difficulty_stats"] = {
            "mean": np.mean(difficulties),
            "std": np.std(difficulties),
            "min": np.min(difficulties),
            "max": np.max(difficulties),
            "median": np.median(difficulties)
        }
        
        # Template analysis
        for template_type in ["terrain_template", "weather_template", "fire_template", "drone_template"]:
            templates = [s[template_type] for s in self.scenarios]
            unique_templates = set(templates)
            
            analysis["template_analysis"][template_type] = {}
            for template in unique_templates:
                count = templates.count(template)
                analysis["template_analysis"][template_type][template] = {
                    "count": count,
                    "percentage": count / len(templates) * 100
                }
        
        # Recommendations
        if len(self.scenarios) < 100:
            analysis["recommendations"].append("Generate more scenarios for better training")
        
        if analysis["complexity_breakdown"]["hard"]["percentage"] < 10:
            analysis["recommendations"].append("Increase hard scenario generation")
        
        if analysis["difficulty_stats"]["mean"] < 0.5:
            analysis["recommendations"].append("Consider adding more challenging scenarios")
        
        return analysis


def main():
    """Generate massive training dataset."""
    print("🚀 AURORA Massive Training Data Generator")
    print("=" * 50)
    
    # Create generator
    generator = MassiveTrainingGenerator()
    
    # Generate dataset
    generator.generate_massive_dataset(
        num_scenarios=500,  # Start with 500 scenarios
        complexity_distribution={"easy": 0.3, "medium": 0.5, "hard": 0.2}
    )
    
    # Analyze dataset
    analysis = generator.analyze_dataset()
    
    print("\n📊 Dataset Analysis:")
    print(f"Total scenarios: {analysis['total_scenarios']}")
    print(f"Average difficulty: {analysis['difficulty_stats']['mean']:.2f}")
    print(f"Complexity breakdown:")
    for complexity, data in analysis['complexity_breakdown'].items():
        print(f"  {complexity}: {data['count']} scenarios ({data['percentage']:.1f}%)")
    
    if analysis['recommendations']:
        print("\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"  - {rec}")
    
    print(f"\n✅ Massive training dataset generated!")
    print(f"📁 Output directory: {generator.output_dir}")


if __name__ == "__main__":
    main() 