"""
Evaluation battery: 5 historical fires x 5 seeds = 25 episodes.
Use this to keep comparisons consistent across runs.
"""

# The gauntlet: five real fires that were tough IRL.
# Picked to stress-test the policy, not make it look good.

EVALUATION_FIRES = [
    {
        'name': 'Camp Fire',
        'state': 'CA',
        'year': 2018,
        'acres': 153336,
        'lat': 39.8,
        'lon': -121.4,
        'description': 'Devastating CA fire - high wind, steep terrain'
    },
    {
        'name': 'Riverside Fire',
        'state': 'OR',
        'year': 2020,
        'acres': 138054,
        'lat': 45.0,
        'lon': -122.0,
        'description': 'Large OR fire - moderate wind, mixed terrain'
    },
    {
        'name': 'East Troublesome Fire',
        'state': 'CO',
        'year': 2020,
        'acres': 193812,
        'lat': 40.2,
        'lon': -106.1,
        'description': 'Rocky Mountain fire - variable wind, high elevation'
    },
    {
        'name': 'Okanogan Complex',
        'state': 'WA',
        'year': 2015,
        'acres': 304711,
        'lat': 48.5,
        'lon': -119.7,
        'description': 'Large WA fire - dry conditions, low wind'
    },
    {
        'name': 'Lolo Peak Fire',
        'state': 'MT',
        'year': 2017,
        'acres': 53962,
        'lat': 46.6,
        'lon': -114.3,
        'description': 'MT wilderness fire - moderate size, varied fuel'
    }
]

# Fixed seeds so runs are comparable and reproducible.
EVALUATION_SEEDS = [42, 123, 456, 789, 1024]

# Evaluation cadence during training
EVAL_EVERY_N_STEPS = 81_920  # Every 10 updates (8192 steps/update x 10)

# Metrics we track per episode
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
    """Return the full evaluation config bundle."""
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
        results: list of dicts with eval metrics
        output_path: where the CSV should live
    """
    import pandas as pd
    from pathlib import Path

    df = pd.DataFrame(results)

    # Make sure the parent folder exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Append if file exists, else create fresh
    if Path(output_path).exists():
        df_existing = pd.read_csv(output_path)
        df = pd.concat([df_existing, df], ignore_index=True)

    df.to_csv(output_path, index=False)
    print(f"✅ Saved evaluation results to {output_path}")


def load_eval_results(output_path='results/metrics.csv'):
    """Load evaluation results from CSV."""
    import pandas as pd
    from pathlib import Path

    if not Path(output_path).exists():
        print(f"⚠️  No evaluation results found at {output_path}")
        return None

    return pd.read_csv(output_path)


def compute_summary_stats(mode='ppo', metrics_path='results/metrics.csv'):
    """Compute summary stats for a given model mode.

    Args:
        mode: 'ppo' or 'hybrid'
        metrics_path: path to metrics CSV
    """
    import pandas as pd

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
    """Compare PPO baseline vs Hybrid model and return % deltas."""
    ppo_stats = compute_summary_stats('ppo', metrics_path)
    hybrid_stats = compute_summary_stats('hybrid', metrics_path)

    if ppo_stats is None or hybrid_stats is None:
        print("⚠️  Can't compare models - missing results for one or both modes")
        return None

    def pct_improvement(baseline, improved, higher_is_better=True):
        """Percent improvement helper."""
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
            higher_is_better=False  # lower is better
        ),
        'burned_area_reduction': pct_improvement(
            ppo_stats['mean_burned_area'],
            hybrid_stats['mean_burned_area'],
            higher_is_better=False  # lower is better
        ),
        'water_efficiency': pct_improvement(
            ppo_stats['mean_water_used'],
            hybrid_stats['mean_water_used'],
            higher_is_better=False  # lower is better
        ),
        'idle_reduction': pct_improvement(
            ppo_stats['mean_idle_steps'],
            hybrid_stats['mean_idle_steps'],
            higher_is_better=False  # lower is better
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
    # Print evaluation battery config
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
