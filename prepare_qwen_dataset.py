"""
Prepare Aurora wildfire scenarios for Qwen fine-tuning

This script loads your existing training data and validates/enhances it
for fine-tuning Qwen2.5-1.5B-Instruct.

It will:
1. Load scenarios from data/real_training_data/
2. Validate and clean the data
3. Add missing fields if needed
4. Generate training statistics
5. Create enhanced scenarios ready for training
"""

import json
import os
from typing import Dict, List, Any
import numpy as np


def load_scenarios(path: str = "data/real_training_data/real_scenarios.json") -> List[Dict]:
    """Load existing scenarios."""
    print(f"📂 Loading scenarios from {path}...")
    
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        print("\nAvailable data files:")
        for root, dirs, files in os.walk("data"):
            for file in files:
                if file.endswith('.json'):
                    print(f"  - {os.path.join(root, file)}")
        return []
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Handle different formats
    if isinstance(data, list):
        scenarios = data
    elif isinstance(data, dict) and 'scenarios' in data:
        scenarios = data['scenarios']
    else:
        scenarios = [data]
    
    print(f"✅ Loaded {len(scenarios)} scenarios")
    return scenarios


def enhance_scenario(scenario: Dict) -> Dict:
    """Enhance a scenario with derived fields for training."""
    
    enhanced = scenario.copy()
    
    # Ensure fire_info exists
    if 'fire_info' not in enhanced:
        enhanced['fire_info'] = {}
    
    # Calculate fire metrics from fire_state if available
    if 'fire_state' in scenario:
        fire_state = np.array(scenario['fire_state'])
        total_cells = fire_state.size
        burning_cells = np.sum(fire_state > 0)
        burned_pct = (burning_cells / total_cells) * 100 if total_cells > 0 else 0
        
        # Update fire_info
        enhanced['fire_info']['burned_percentage'] = float(burned_pct)
        enhanced['fire_info']['active_cells'] = int(burning_cells)
        enhanced['fire_info']['total_cells'] = int(total_cells)
        
        # Calculate fire center
        if burning_cells > 0:
            fire_positions = np.argwhere(fire_state > 0)
            fire_center = fire_positions.mean(axis=0).tolist()
            enhanced['fire_info']['center'] = [float(x) for x in fire_center]
        
        # Calculate avg intensity
        if burning_cells > 0:
            avg_intensity = float(fire_state[fire_state > 0].mean())
            enhanced['fire_info']['avg_intensity'] = "high" if avg_intensity > 0.7 else "medium" if avg_intensity > 0.3 else "low"
    
    # Ensure weather exists
    if 'weather' not in enhanced:
        enhanced['weather'] = {
            'windSpeed': 10.0,
            'windDir': 0,
            'temp': 25.0,
            'humidity': 0.3
        }
    
    # Normalize weather field names
    weather = enhanced['weather']
    if 'wind_mps' in weather and 'windSpeed' not in weather:
        weather['windSpeed'] = weather['wind_mps']
    if 'wind_deg' in weather and 'windDir' not in weather:
        weather['windDir'] = weather['wind_deg']
    if 'temperature_c' in weather and 'temp' not in weather:
        weather['temp'] = weather['temperature_c']
    
    # Ensure terrain_info exists
    if 'terrain_info' not in enhanced:
        enhanced['terrain_info'] = {'type': 'mixed'}
    
    # Calculate terrain info from terrain array if available
    if 'terrain' in scenario:
        terrain = np.array(scenario['terrain'])
        enhanced['terrain_info']['elevation_range'] = f"{terrain.min():.0f}-{terrain.max():.0f}m"
        enhanced['terrain_info']['avg_elevation'] = float(terrain.mean())
    
    # Ensure agents list exists
    if 'agents' not in enhanced and 'num_drones' in scenario:
        num_drones = scenario['num_drones']
        enhanced['agents'] = [
            {'id': i, 'battery': 1.0, 'water': 1.0}
            for i in range(num_drones)
        ]
    
    # Add scenario metadata
    if 'scenario_id' not in enhanced:
        enhanced['scenario_id'] = f"scenario_{hash(json.dumps(scenario)) % 10000:04d}"
    
    if 'scenario_name' not in enhanced:
        enhanced['scenario_name'] = enhanced.get('scenario_type', 'Wildfire Scenario')
    
    return enhanced


def validate_scenario(scenario: Dict) -> tuple[bool, List[str]]:
    """Validate that a scenario has required fields."""
    
    required_fields = ['scenario_id', 'fire_info', 'weather', 'agents']
    missing = []
    
    for field in required_fields:
        if field not in scenario:
            missing.append(field)
    
    # Check nested required fields
    if 'fire_info' in scenario:
        if 'burned_percentage' not in scenario['fire_info']:
            missing.append('fire_info.burned_percentage')
    
    if 'weather' in scenario:
        weather_required = ['windSpeed', 'windDir', 'temp', 'humidity']
        for field in weather_required:
            if field not in scenario['weather']:
                missing.append(f'weather.{field}')
    
    is_valid = len(missing) == 0
    return is_valid, missing


def generate_statistics(scenarios: List[Dict]) -> Dict[str, Any]:
    """Generate statistics about the scenarios."""
    
    stats = {
        'total_scenarios': len(scenarios),
        'burn_percentages': [],
        'wind_speeds': [],
        'temperatures': [],
        'num_drones': [],
        'scenario_types': {}
    }
    
    for scenario in scenarios:
        # Burn percentages
        if 'fire_info' in scenario and 'burned_percentage' in scenario['fire_info']:
            stats['burn_percentages'].append(scenario['fire_info']['burned_percentage'])
        
        # Wind speeds
        if 'weather' in scenario:
            stats['wind_speeds'].append(scenario['weather'].get('windSpeed', 0))
            stats['temperatures'].append(scenario['weather'].get('temp', 0))
        
        # Num drones
        if 'agents' in scenario:
            stats['num_drones'].append(len(scenario['agents']))
        
        # Scenario types
        scenario_type = scenario.get('scenario_type', 'unknown')
        stats['scenario_types'][scenario_type] = stats['scenario_types'].get(scenario_type, 0) + 1
    
    # Calculate averages
    if stats['burn_percentages']:
        stats['avg_burn_percentage'] = np.mean(stats['burn_percentages'])
        stats['min_burn_percentage'] = np.min(stats['burn_percentages'])
        stats['max_burn_percentage'] = np.max(stats['burn_percentages'])
    
    if stats['wind_speeds']:
        stats['avg_wind_speed'] = np.mean(stats['wind_speeds'])
    
    if stats['temperatures']:
        stats['avg_temperature'] = np.mean(stats['temperatures'])
    
    if stats['num_drones']:
        stats['avg_num_drones'] = np.mean(stats['num_drones'])
    
    return stats


def prepare_training_data(
    input_path: str = "data/real_training_data/real_scenarios.json",
    output_path: str = "data/real_training_data/real_scenarios_enhanced.json"
):
    """Main function to prepare training data."""
    
    print("\n" + "="*60)
    print("🔥 PREPARING QWEN TRAINING DATA")
    print("="*60 + "\n")
    
    # Load scenarios
    scenarios = load_scenarios(input_path)
    
    if not scenarios:
        print("❌ No scenarios loaded. Check your data path.")
        return
    
    # Enhance scenarios
    print("\n🔄 Enhancing scenarios...")
    enhanced_scenarios = []
    invalid_count = 0
    
    for i, scenario in enumerate(scenarios):
        try:
            enhanced = enhance_scenario(scenario)
            is_valid, missing = validate_scenario(enhanced)
            
            if is_valid:
                enhanced_scenarios.append(enhanced)
            else:
                invalid_count += 1
                print(f"⚠️  Scenario {i} invalid, missing: {', '.join(missing)}")
        except Exception as e:
            invalid_count += 1
            print(f"⚠️  Scenario {i} failed: {e}")
    
    print(f"\n✅ Enhanced {len(enhanced_scenarios)} valid scenarios")
    if invalid_count > 0:
        print(f"⚠️  Skipped {invalid_count} invalid scenarios")
    
    # Generate statistics
    print("\n📊 Generating statistics...")
    stats = generate_statistics(enhanced_scenarios)
    
    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)
    print(f"Total scenarios: {stats['total_scenarios']}")
    if 'avg_burn_percentage' in stats:
        print(f"Burn percentage: {stats['min_burn_percentage']:.1f}% - {stats['max_burn_percentage']:.1f}% (avg: {stats['avg_burn_percentage']:.1f}%)")
    if 'avg_wind_speed' in stats:
        print(f"Wind speed: avg {stats['avg_wind_speed']:.1f} m/s")
    if 'avg_temperature' in stats:
        print(f"Temperature: avg {stats['avg_temperature']:.1f}°C")
    if 'avg_num_drones' in stats:
        print(f"Drones: avg {stats['avg_num_drones']:.1f}")
    print("\nScenario types:")
    for stype, count in stats['scenario_types'].items():
        print(f"  - {stype}: {count}")
    print("="*60)
    
    # Save enhanced data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output_data = {
        'scenarios': enhanced_scenarios,
        'metadata': {
            'total_scenarios': len(enhanced_scenarios),
            'statistics': stats,
            'enhanced': True
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Enhanced scenarios saved to: {output_path}")
    
    # Save statistics separately
    stats_path = output_path.replace('.json', '_stats.json')
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"✅ Statistics saved to: {stats_path}")
    
    print("\n" + "="*60)
    print("✅ DATA PREPARATION COMPLETE!")
    print("="*60)
    print(f"\nReady for training! Use:")
    print(f"  python train_qwen_wildfire.py --scenarios {output_path}")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Prepare wildfire scenarios for Qwen training")
    parser.add_argument("--input", type=str, 
                       default="data/real_training_data/real_scenarios.json",
                       help="Input scenarios file")
    parser.add_argument("--output", type=str,
                       default="data/real_training_data/real_scenarios_enhanced.json",
                       help="Output enhanced scenarios file")
    
    args = parser.parse_args()
    
    prepare_training_data(args.input, args.output)
