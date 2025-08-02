"""
Global Fire Data Processor for AURORA

This module processes massive fire datasets (50GB+) and extracts:
- Real coordinates from NASA FIRMS data
- Country information
- Fire types and intensities
- Date ranges
- Size estimates

Handles multiple satellite datasets and formats them for the 3D Earth interface.
"""

import os
import json
import geopandas as gpd
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from datetime import datetime, timedelta
import pycountry

class GlobalFireDataProcessor:
    """Processes massive global fire datasets for 3D visualization."""
    
    def __init__(self, fire_data_dir: str = "../Fire_Data"):
        """
        Initialize the global fire data processor.
        
        Args:
            fire_data_dir: Directory containing fire data files
        """
        self.fire_data_dir = Path(fire_data_dir)
        self.processed_data = {}
        self.country_mapping = self._load_country_mapping()
        
    def _load_country_mapping(self) -> Dict[str, str]:
        """Load country code to name mapping."""
        mapping = {}
        for country in pycountry.countries:
            mapping[country.alpha_2] = country.name
        return mapping
    
    def scan_fire_datasets(self) -> Dict[str, Any]:
        """Scan all fire datasets and return summary."""
        print("🔍 Scanning global fire datasets...")
        
        datasets = {}
        total_size = 0
        
        for fire_dir in self.fire_data_dir.glob("DL_FIRE_*"):
            if fire_dir.is_dir():
                dataset_name = fire_dir.name
                print(f"📁 Processing {dataset_name}...")
                
                # Get all files in dataset
                files = list(fire_dir.glob("*"))
                dataset_size = sum(f.stat().st_size for f in files if f.is_file())
                total_size += dataset_size
                
                # Extract satellite type
                satellite_type = dataset_name.split('_')[2] if len(dataset_name.split('_')) > 2 else 'Unknown'
                
                # Find shapefiles
                shapefiles = [f for f in files if f.suffix == '.shp']
                
                dataset_info = {
                    'name': dataset_name,
                    'satellite_type': satellite_type,
                    'files': [f.name for f in files],
                    'file_count': len(files),
                    'shapefiles': [f.name for f in shapefiles],
                    'size_mb': dataset_size / (1024 * 1024),
                    'total_size_gb': total_size / (1024 * 1024 * 1024)
                }
                
                datasets[dataset_name] = dataset_info
                print(f"  ✅ {len(files)} files, {dataset_size / (1024*1024):.1f} MB")
        
        print(f"🎯 Total datasets: {len(datasets)}")
        print(f"💾 Total size: {total_size / (1024*1024*1024):.1f} GB")
        
        return datasets
    
    def extract_fire_coordinates(self, dataset_name: str, max_fires: int = 1000) -> List[Dict]:
        """Extract fire coordinates from a specific dataset."""
        dataset_path = self.fire_data_dir / dataset_name
        
        if not dataset_path.exists():
            print(f"❌ Dataset {dataset_name} not found")
            return []
        
        # Find shapefiles
        shapefiles = list(dataset_path.glob("*.shp"))
        
        if not shapefiles:
            print(f"❌ No shapefiles found in {dataset_name}")
            return []
        
        fires = []
        
        for shp_file in shapefiles:
            try:
                print(f"📊 Loading {shp_file.name}...")
                
                # Load shapefile
                gdf = gpd.read_file(shp_file)
                
                # Sample data if too large
                if len(gdf) > max_fires:
                    gdf = gdf.sample(n=max_fires, random_state=42)
                
                # Extract coordinates and attributes
                for idx, row in gdf.iterrows():
                    try:
                        # Get coordinates
                        if hasattr(row.geometry, 'x') and hasattr(row.geometry, 'y'):
                            lon, lat = row.geometry.x, row.geometry.y
                        else:
                            # Get centroid
                            lon, lat = row.geometry.centroid.x, row.geometry.centroid.y
                        
                        # Validate coordinates
                        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                            continue
                        
                        # Determine country from coordinates
                        country = self._get_country_from_coordinates(lat, lon)
                        
                        # Extract fire attributes
                        fire_data = {
                            'id': f"{dataset_name}_{idx}",
                            'lat': float(lat),
                            'lng': float(lon),
                            'country': country['code'],
                            'country_name': country['name'],
                            'satellite_type': dataset_name.split('_')[2],
                            'dataset': dataset_name,
                            'file': shp_file.name
                        }
                        
                        # Add available attributes
                        for col in gdf.columns:
                            if col != 'geometry':
                                try:
                                    value = row[col]
                                    if pd.notna(value):
                                        if isinstance(value, (int, float)):
                                            fire_data[col.lower()] = float(value)
                                        else:
                                            fire_data[col.lower()] = str(value)
                                except:
                                    continue
                        
                        fires.append(fire_data)
                        
                    except Exception as e:
                        print(f"  ⚠️ Error processing fire {idx}: {e}")
                        continue
                
                print(f"  ✅ Extracted {len(fires)} fires from {shp_file.name}")
                
            except Exception as e:
                print(f"❌ Error loading {shp_file}: {e}")
                continue
        
        return fires
    
    def _get_country_from_coordinates(self, lat: float, lon: float) -> Dict[str, str]:
        """Get country information from coordinates."""
        # Simple country detection based on coordinate ranges
        # In a real implementation, you'd use a proper geocoding service
        
        country_ranges = {
            'US': {'lat': (24, 71), 'lng': (-180, -66)},
            'CA': {'lat': (41, 84), 'lng': (-141, -52)},
            'AU': {'lat': (-44, -10), 'lng': (113, 154)},
            'BR': {'lat': (-34, 6), 'lng': (-74, -34)},
            'RU': {'lat': (41, 82), 'lng': (26, 190)},
            'CN': {'lat': (18, 54), 'lng': (73, 135)},
            'IN': {'lat': (6, 37), 'lng': (68, 97)},
            'ZA': {'lat': (-35, -22), 'lng': (16, 33)},
            'AR': {'lat': (-56, -21), 'lng': (-74, -53)},
            'MX': {'lat': (14, 33), 'lng': (-118, -86)}
        }
        
        for code, ranges in country_ranges.items():
            if (ranges['lat'][0] <= lat <= ranges['lat'][1] and 
                ranges['lng'][0] <= lon <= ranges['lng'][1]):
                return {
                    'code': code,
                    'name': self.country_mapping.get(code, code)
                }
        
        return {'code': 'UNKNOWN', 'name': 'Unknown'}
    
    def process_all_datasets(self, max_fires_per_dataset: int = 500) -> Dict[str, Any]:
        """Process all fire datasets and return consolidated data."""
        print("🚀 Processing all global fire datasets...")
        
        # Scan datasets
        datasets = self.scan_fire_datasets()
        
        all_fires = []
        processed_datasets = 0
        
        for dataset_name in datasets.keys():
            try:
                print(f"\n🔥 Processing {dataset_name}...")
                fires = self.extract_fire_coordinates(dataset_name, max_fires_per_dataset)
                all_fires.extend(fires)
                processed_datasets += 1
                
                print(f"  ✅ Added {len(fires)} fires from {dataset_name}")
                
            except Exception as e:
                print(f"❌ Error processing {dataset_name}: {e}")
                continue
        
        # Organize by country
        fires_by_country = {}
        for fire in all_fires:
            country = fire['country']
            if country not in fires_by_country:
                fires_by_country[country] = []
            fires_by_country[country].append(fire)
        
        # Create summary
        summary = {
            'total_fires': len(all_fires),
            'processed_datasets': processed_datasets,
            'total_datasets': len(datasets),
            'fires_by_country': {country: len(fires) for country, fires in fires_by_country.items()},
            'satellite_types': list(set(fire['satellite_type'] for fire in all_fires)),
            'date_range': {
                'earliest': min(fire.get('date', datetime.now()) for fire in all_fires if 'date' in fire),
                'latest': max(fire.get('date', datetime.now()) for fire in all_fires if 'date' in fire)
            }
        }
        
        self.processed_data = {
            'summary': summary,
            'fires': all_fires,
            'fires_by_country': fires_by_country,
            'datasets': datasets
        }
        
        print(f"\n🎯 Processing complete!")
        print(f"📊 Total fires: {len(all_fires)}")
        print(f"🌍 Countries: {len(fires_by_country)}")
        print(f"🛰️ Satellite types: {len(summary['satellite_types'])}")
        
        return self.processed_data
    
    def save_processed_data(self, output_file: str = "results/global_fire_data.json"):
        """Save processed data to JSON file."""
        if not self.processed_data:
            print("❌ No data to save. Run process_all_datasets() first.")
            return
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        # Convert datetime objects to strings for JSON serialization
        data_to_save = json.loads(json.dumps(self.processed_data, default=str))
        
        with open(output_path, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        
        print(f"💾 Saved processed data to {output_path}")
        return str(output_path)
    
    def generate_3d_earth_data(self) -> Dict[str, Any]:
        """Generate data specifically formatted for the 3D Earth interface."""
        if not self.processed_data:
            print("❌ No processed data available. Run process_all_datasets() first.")
            return {}
        
        print("🌍 Generating 3D Earth data...")
        
        # Group fires by country for the interface
        earth_data = {
            'countries': {},
            'fires': self.processed_data['fires'],
            'summary': self.processed_data['summary']
        }
        
        # Organize by country
        for fire in self.processed_data['fires']:
            country_code = fire['country']
            if country_code not in earth_data['countries']:
                earth_data['countries'][country_code] = {
                    'name': fire['country_name'],
                    'fires': [],
                    'fire_count': 0,
                    'satellite_types': set()
                }
            
            earth_data['countries'][country_code]['fires'].append(fire)
            earth_data['countries'][country_code]['fire_count'] += 1
            earth_data['countries'][country_code]['satellite_types'].add(fire['satellite_type'])
        
        # Convert sets to lists for JSON serialization
        for country in earth_data['countries'].values():
            country['satellite_types'] = list(country['satellite_types'])
        
        print(f"✅ Generated 3D Earth data for {len(earth_data['countries'])} countries")
        return earth_data
    
    def get_fires_by_country(self, country_code: str) -> List[Dict]:
        """Get all fires for a specific country."""
        if not self.processed_data:
            return []
        
        return [fire for fire in self.processed_data['fires'] if fire['country'] == country_code]
    
    def get_fires_by_type(self, satellite_type: str) -> List[Dict]:
        """Get all fires for a specific satellite type."""
        if not self.processed_data:
            return []
        
        return [fire for fire in self.processed_data['fires'] if fire['satellite_type'] == satellite_type]


def main():
    """Main function to process global fire data."""
    processor = GlobalFireDataProcessor()
    
    # Process all datasets
    data = processor.process_all_datasets(max_fires_per_dataset=1000)
    
    # Generate 3D Earth data
    earth_data = processor.generate_3d_earth_data()
    
    # Save processed data
    processor.save_processed_data()
    
    # Save 3D Earth data
    earth_data_path = Path("results/3d_earth_fire_data.json")
    earth_data_path.parent.mkdir(exist_ok=True)
    
    with open(earth_data_path, 'w') as f:
        json.dump(earth_data, f, indent=2, default=str)
    
    print(f"🌍 3D Earth data saved to {earth_data_path}")
    
    return data


if __name__ == "__main__":
    main() 