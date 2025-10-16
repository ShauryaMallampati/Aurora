"""
AURORA Evaluation Battery - Fixed Held-Out Test Set

This file defines the official evaluation battery for AURORA ISEF 2025.
These scenarios are held out from training and used consistently across all experiments.

5 historical fires × 5 evaluation seeds = 25 evaluation episodes per model

Author: Shaurya Mallampati
Date: October 16, 2025
"""

# Evaluation Battery: 5 Representative Historical Fires
# Selected for diversity in:
# - Geography (CA, WA, OR, CO, MT)
# - Size (small to large)
# - Wind regimes (calm to high wind)
# - Terrain (flat to mountainous)
# - Year (temporal diversity)

EVALUATION_FIRES = [
    {
        'name': 'Camp Fire',
        'state': 'CA',
        'year': 2018,
        'acres': 153336,
        'lat': 39.8,
        'lon': -121.4,
        'description': 'Devastating California fire - high wind, steep terrain'
    },
    {
        'name': 'Riverside Fire',
        'state': 'OR',
        'year': 2020,
        'acres': 138054,
        'lat': 45.0,
        'lon': -122.0,
        'description': 'Large Oregon fire - moderate wind, mixed terrain'
    },
    {
        'name': 'East Troublesome Fire',
        'state': 'CO',
        'year': 2020,
        'acres': 193812,
        'lat': 40.2,
        'lon': -106.1,
        'description': 'Colorado Rocky Mountain fire - variable wind, high elevation'
    },
    {
        'name': 'Okanogan Complex',
        'state': 'WA',
        'year': 2015,
        'acres': 304711,
        'lat': 48.5,
        'lon': -119.7,
        'description': 'Large Washington fire - dry conditions, low wind'
    },
    {
        'name': 'Lolo Peak Fire',
        'state': 'MT',
        'year': 2017,
        'acres': 53962,
        'lat': 46.6,
        'lon': -114.3,
        'description': 'Montana wilderness fire - moderate size, diverse fuel types'
    }
]

# Evaluation seeds for reproducibility
# Each fire is evaluated with these 5 different random seeds
EVALUATION_SEEDS = [42, 123, 456, 789, 1024]

# Evaluation frequency during training
EVAL_EVERY_N_STEPS = 81_920  # Every 10 updates (8192 steps/update × 10)

# Metrics to track per evaluation episode
EVAL_METRICS = [
    'episode_return',
    'time_to_containment',
    'final_burned_area',
    'water_used',
    'idle_steps',
    'success_flag',  # 1 if contained, 0 if not
    'containment_percent',
    'agent_efficiency'  # water used per contained hectare
]


def get_evaluation_battery():
    """Get the complete evaluation battery configuration.
    
    Returns:
        Dict with fires, seeds, and evaluation config
    """
    return {
        'fires': EVALUATION_FIRES,
        'seeds': EVALUATION_SEEDS,
        'total_episodes': len(EVALUATION_FIRES) * len(EVALUATION_SEEDS),
        'eval_frequency': EVAL_EVERY_N_STEPS,
        'metrics': EVAL_METRICS
    }


def save_eval_results(results, output_path='results/metrics.csv'):
    """Save evaluation results to CSV.
    
    Args:
        results: List of dicts with eval metrics
        output_path: Path to save CSV
    """
    import pandas as pd
    from pathlib import Path
    
    df = pd.DataFrame(results)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Append to existing file or create new
    if Path(output_path).exists():
        df_existing = pd.read_csv(output_path)
        df = pd.concat([df_existing, df], ignore_index=True)
    
    df.to_csv(output_path, index=False)
    print(f"✅ Saved evaluation results to {output_path}")


def load_eval_results(output_path='results/metrics.csv'):
    """Load evaluation results from CSV.
    
    Returns:
        DataFrame with eval metrics
    """
    import pandas as pd
    from pathlib import Path
    
    if not Path(output_path).exists():
        print(f"⚠️  No evaluation results found at {output_path}")
        return None
    
    return pd.read_csv(output_path)


def compute_summary_stats(mode='ppo', metrics_path='results/metrics.csv'):
    """Compute summary statistics for a model.
    
    Args:
        mode: 'ppo' or 'hybrid'
        metrics_path: Path to metrics CSV
    
    Returns:
        Dict with summary statistics
    """
    import pandas as pd
    import numpy as np
    
    df = load_eval_results(metrics_path)
    if df is None or len(df) == 0:
        return None
    
    # Filter by mode
    df_mode = df[df['mode'] == mode]
    
    if len(df_mode) == 0:
        print(f"⚠️  No results found for mode={mode}")
        return None
    
    summary = {
        'mode': mode,
        'num_episodes': len(df_mode),
        'mean_return': df_mode['episode_return'].mean(),
        'std_return': df_mode['episode_return'].std(),
        'mean_containment_time': df_mode['time_to_containment'].mean(),
        'std_containment_time': df_mode['time_to_containment'].std(),
        'mean_burned_area': df_mode['final_burned_area'].mean(),
        'std_burned_area': df_mode['final_burned_area'].std(),
        'mean_water_used': df_mode['water_used'].mean(),
        'std_water_used': df_mode['water_used'].std(),
        'mean_idle_steps': df_mode['idle_steps'].mean(),
        'std_idle_steps': df_mode['idle_steps'].std(),
        'success_rate': df_mode['success_flag'].mean()
    }
    
    return summary


def compare_models(metrics_path='results/metrics.csv'):
    """Compare PPO baseline vs Hybrid model.
    
    Returns:
        Dict with comparison statistics and percent improvements
    """
    ppo_stats = compute_summary_stats('ppo', metrics_path)
    hybrid_stats = compute_summary_stats('hybrid', metrics_path)
    
    if ppo_stats is None or hybrid_stats is None:
        print("⚠️  Cannot compare models - missing results for one or both modes")
        return None
    
    def pct_improvement(baseline, improved, higher_is_better=True):
        """Compute percent improvement."""
        if baseline == 0:
            return 0.0
        delta = improved - baseline
        pct = (delta / baseline) * 100
        return pct if higher_is_better else -pct
    
    comparison = {
        'return_improvement': pct_improvement(
            ppo_stats['mean_return'], 
            hybrid_stats['mean_return'], 
            higher_is_better=True
        ),
        'containment_time_improvement': pct_improvement(
            ppo_stats['mean_containment_time'],
            hybrid_stats['mean_containment_time'],
            higher_is_better=False  # Lower is better
        ),
        'burned_area_reduction': pct_improvement(
            ppo_stats['mean_burned_area'],
            hybrid_stats['mean_burned_area'],
            higher_is_better=False  # Lower is better
        ),
        'water_efficiency': pct_improvement(
            ppo_stats['mean_water_used'],
            hybrid_stats['mean_water_used'],
            higher_is_better=False  # Lower is better (more efficient)
        ),
        'idle_reduction': pct_improvement(
            ppo_stats['mean_idle_steps'],
            hybrid_stats['mean_idle_steps'],
            higher_is_better=False  # Lower is better
        ),
        'success_rate_improvement': pct_improvement(
            ppo_stats['success_rate'],
            hybrid_stats['success_rate'],
            higher_is_better=True
        ),
        'ppo': ppo_stats,
        'hybrid': hybrid_stats
    }
    
    return comparison


if __name__ == "__main__":
    # Print evaluation battery configuration
    battery = get_evaluation_battery()
    
    print("="*80)
    print("AURORA EVALUATION BATTERY")
    print("="*80)
    print(f"\nTotal evaluation episodes: {battery['total_episodes']}")
    print(f"Evaluation frequency: Every {battery['eval_frequency']:,} steps\n")
    
    print("Held-out fires:")
    for i, fire in enumerate(battery['fires'], 1):
        print(f"  {i}. {fire['name']} ({fire['state']} {fire['year']})")
        print(f"     {fire['acres']:,} acres - {fire['description']}")
    
    print(f"\nEvaluation seeds: {battery['seeds']}")
    print(f"\nTracked metrics: {', '.join(battery['metrics'])}")
    print("="*80)
