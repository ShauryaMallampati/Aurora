#!/usr/bin/env python3
"""
Pre-flight checks.
Runs before takeoff to verify deps and data.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("="*80)
    print("📦 CHECKING DEPENDENCIES")
    print("="*80)
    
    missing = []
    
    deps = [
        ('numpy', 'NumPy'),
        ('matplotlib', 'Matplotlib'),
        ('pandas', 'Pandas'),
        ('gymnasium', 'Gymnasium'),
        ('stable_baselines3', 'Stable-Baselines3'),
        ('torch', 'PyTorch'),
        ('transformers', 'Transformers'),
        ('geopandas', 'GeoPandas'),
        ('rasterio', 'Rasterio'),
        ('shapely', 'Shapely'),
    ]
    
    for module, name in deps:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name}")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies installed\n")
    return True


def check_data_files():
    """Check if required data files exist."""
    print("="*80)
    print("📂 CHECKING DATA FILES")
    print("="*80)
    
    data_dir = Path(__file__).parent / 'data'
    
    checks = [
        ('InterAgencyFirePerimeterHistory_All_Years_View_5507083134356011387', 
         'Fire perimeter shapefile directory'),
        ('weather_cache', 'Weather cache directory'),
    ]
    
    all_ok = True
    
    for item, desc in checks:
        path = data_dir / item
        if path.exists():
            print(f"✅ {desc}: {path.name}")
        else:
            print(f"❌ {desc}: NOT FOUND")
            all_ok = False
    
    # Check for shapefile components
    shp_dir = data_dir / 'InterAgencyFirePerimeterHistory_All_Years_View_5507083134356011387'
    if shp_dir.exists():
        shp_file = shp_dir / 'InteragencyFirePerimeterHistory.shp'
        if shp_file.exists():
            print(f"✅ Shapefile: {shp_file.name}")
        else:
            print(f"❌ Shapefile: NOT FOUND")
            all_ok = False
    
    if all_ok:
        print("\n✅ All data files present\n")
    else:
        print("\n⚠️  Some data files missing\n")
    
    return all_ok


def check_modules():
    """Check if project modules can be imported."""
    print("="*80)
    print("🔧 CHECKING PROJECT MODULES")
    print("="*80)
    
    modules = [
        ('env.fire_sim', 'FireSim'),
        ('agents.drone_agent', 'DroneAgent'),
        ('agents.hybrid_ppo_llm_agent', 'HybridPPOLLMAgent'),
        ('evaluation_battery', 'Evaluation Battery'),
        ('callbacks', 'Training Callbacks'),
    ]
    
    all_ok = True
    
    for module, name in modules:
        try:
            __import__(module)
            print(f"✅ {name}: {module}")
        except Exception as e:
            print(f"❌ {name}: {str(e)[:60]}")
            all_ok = False
    
    if all_ok:
        print("\n✅ All modules importable\n")
    else:
        print("\n⚠️  Some modules have import errors\n")
    
    return all_ok


def check_output_dirs():
    """Check/create output directories."""
    print("="*80)
    print("📁 CHECKING OUTPUT DIRECTORIES")
    print("="*80)
    
    dirs = [
        'results',
        'results/checkpoints',
        'results/videos',
        'results/poster_figures',
        'logs',
    ]
    
    for dir_path in dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {dir_path}")
        else:
            print(f"✅ Exists: {dir_path}")
    
    print("\n✅ All output directories ready\n")
    return True


def main():
    """Run all pre-flight checks."""
    
    print("\n" + "="*80)
    print("🚀 AURORA PRE-FLIGHT CHECK")
    print("="*80 + "\n")
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Data Files", check_data_files),
        ("Project Modules", check_modules),
        ("Output Directories", check_output_dirs),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed: {e}\n")
            results.append((name, False))
    
    # Summary
    print("="*80)
    print("📊 PRE-FLIGHT SUMMARY")
    print("="*80)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {name}")
        if not result:
            all_passed = False
    
    print("="*80)
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED - READY FOR TRAINING!\n")
        print("Next steps:")
        print("  1. Quick test: python train_manager.py --mode ppo --phase quick --dry_run")
        print("  2. Full training: python train_manager.py --mode ppo --phase phase_a")
        print("  3. Hybrid training: python train_manager.py --mode hybrid --phase phase_a")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED - PLEASE FIX BEFORE TRAINING\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
