#!/usr/bin/env python3
"""
Generate publication-quality plots for ISEF presentation.
Creates 4 key plots from evaluation metrics.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

# Try to import matplotlib, provide helpful error if not available
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
except ImportError:
    print("⚠️  matplotlib not installed. Plots will not be generated.")
    print("   Install with: pip install matplotlib")
    exit(1)

def read_csv(filepath):
    """Read CSV file and return list of dicts."""
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for key in row:
                try:
                    if '.' in row[key]:
                        row[key] = float(row[key])
                    else:
                        row[key] = int(row[key])
                except (ValueError, AttributeError):
                    pass
            data.append(row)
    return data

def plot_returns_vs_latency(hybrid_data, output_path):
    """Plot 1: Returns vs LLM Latency Trade-off."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Group by cadence
    cadence_colors = {25: '#e74c3c', 50: '#9b59b6', 100: '#3498db'}
    cadence_labels = {25: 'Cadence=25 (Frequent)', 50: 'Cadence=50 (Optimal)', 100: 'Cadence=100 (Rare)'}
    
    for cadence in [25, 50, 100]:
        cadence_data = [d for d in hybrid_data if d['llm_cadence'] == cadence]
        returns = [d['return'] for d in cadence_data]
        latencies = [d['llm_latency'] for d in cadence_data]
        
        ax.scatter(latencies, returns, c=cadence_colors[cadence], 
                  label=cadence_labels[cadence], alpha=0.6, s=80, edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('LLM Latency (ms per step)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Mean Episode Return', fontsize=12, fontweight='bold')
    ax.set_title('Returns vs LLM Latency Trade-off', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(y=-45.2, color='gray', linestyle='--', linewidth=2, label='PPO Baseline', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Plot 1 saved: {output_path}")

def plot_containment_vs_cadence(ppo_data, hybrid_data, output_path):
    """Plot 2: Containment Time vs Cadence."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Calculate means and std errors
    cadences = [25, 50, 100, 999999]  # Include PPO as infinite cadence
    means = []
    errors = []
    
    for cadence in cadences:
        if cadence == 999999:
            data = ppo_data
        else:
            data = [d for d in hybrid_data if d['llm_cadence'] == cadence]
        
        times = [d['containment_time'] for d in data]
        mean = sum(times) / len(times)
        std = (sum((x - mean) ** 2 for x in times) / len(times)) ** 0.5
        sem = std / (len(times) ** 0.5)
        
        means.append(mean)
        errors.append(1.96 * sem)  # 95% CI
    
    x_labels = ['25', '50', '100', '∞ (PPO)']
    x_pos = range(len(x_labels))
    
    ax.errorbar(x_pos, means, yerr=errors, marker='o', markersize=10, 
               linewidth=2, capsize=5, capthick=2, color='#2c3e50', 
               markerfacecolor='#3498db', markeredgecolor='black', markeredgewidth=1.5)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=11)
    ax.set_xlabel('LLM Guidance Cadence (steps)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time to 95% Containment (steps)', fontsize=12, fontweight='bold')
    ax.set_title('Containment Time vs LLM Cadence', fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Highlight optimal
    ax.axvline(x=1, color='#27ae60', linestyle='--', linewidth=2, alpha=0.5, label='Optimal Cadence')
    ax.legend(loc='upper right', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Plot 2 saved: {output_path}")

def plot_completion_rate_boxplot(ppo_data, hybrid_data, output_path):
    """Plot 3: Completion Rate Across Models."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Prepare data for box plot
    ppo_success = [d['success'] * 100 for d in ppo_data]
    hybrid_25 = [d['success'] * 100 for d in hybrid_data if d['llm_cadence'] == 25]
    hybrid_50 = [d['success'] * 100 for d in hybrid_data if d['llm_cadence'] == 50]
    hybrid_100 = [d['success'] * 100 for d in hybrid_data if d['llm_cadence'] == 100]
    
    data_to_plot = [ppo_success, hybrid_25, hybrid_50, hybrid_100]
    labels = ['PPO-Only', 'Hybrid-25', 'Hybrid-50', 'Hybrid-100']
    colors = ['#95a5a6', '#e74c3c', '#9b59b6', '#3498db']
    
    bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True,
                    boxprops=dict(linewidth=1.5),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5),
                    medianprops=dict(linewidth=2, color='black'))
    
    # Color boxes
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_ylabel('Success Rate (% fires fully contained)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Model Configuration', fontsize=12, fontweight='bold')
    ax.set_title('Completion Rate Across Models', fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Plot 3 saved: {output_path}")

def plot_robustness_under_noise(robustness_data, output_path):
    """Plot 4: Robustness Under Observation Noise."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Group by model and noise level
    noise_levels = sorted(set(d['noise_level'] for d in robustness_data))
    
    ppo_means = []
    ppo_errors = []
    hybrid_means = []
    hybrid_errors = []
    
    for noise in noise_levels:
        ppo_drops = [d['return_drop_pct'] for d in robustness_data 
                     if d['model'] == 'ppo' and d['noise_level'] == noise]
        hybrid_drops = [d['return_drop_pct'] for d in robustness_data 
                       if d['model'] == 'hybrid' and d['noise_level'] == noise]
        
        ppo_mean = sum(ppo_drops) / len(ppo_drops)
        ppo_std = (sum((x - ppo_mean) ** 2 for x in ppo_drops) / len(ppo_drops)) ** 0.5
        ppo_sem = ppo_std / (len(ppo_drops) ** 0.5)
        
        hybrid_mean = sum(hybrid_drops) / len(hybrid_drops)
        hybrid_std = (sum((x - hybrid_mean) ** 2 for x in hybrid_drops) / len(hybrid_drops)) ** 0.5
        hybrid_sem = hybrid_std / (len(hybrid_drops) ** 0.5)
        
        ppo_means.append(ppo_mean)
        ppo_errors.append(1.96 * ppo_sem)
        hybrid_means.append(hybrid_mean)
        hybrid_errors.append(1.96 * hybrid_sem)
    
    noise_pct = [n * 100 for n in noise_levels]
    
    ax.errorbar(noise_pct, ppo_means, yerr=ppo_errors, marker='s', markersize=10,
               linewidth=2.5, capsize=5, capthick=2, label='PPO-Only',
               color='#e74c3c', markerfacecolor='#e74c3c', markeredgecolor='black', markeredgewidth=1.5)
    
    ax.errorbar(noise_pct, hybrid_means, yerr=hybrid_errors, marker='o', markersize=10,
               linewidth=2.5, capsize=5, capthick=2, label='Hybrid (PPO+Qwen)',
               color='#27ae60', markerfacecolor='#27ae60', markeredgecolor='black', markeredgewidth=1.5)
    
    ax.set_xlabel('Observation Noise Level (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Return Drop (%)', fontsize=12, fontweight='bold')
    ax.set_title('Robustness Under Observation Noise', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(-1, 21)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Plot 4 saved: {output_path}")

def main():
    """Main execution function."""
    print("📊 AURORA Publication-Quality Plot Generator")
    print("=" * 60)
    
    # Setup paths
    results_dir = Path('/vercel/sandbox/results/eval_metrics')
    plots_dir = Path('/vercel/sandbox/plots')
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\n📂 Loading evaluation data...")
    ppo_data = read_csv(results_dir / 'eval_metrics_ppo.csv')
    hybrid_data = read_csv(results_dir / 'eval_metrics_hybrid.csv')
    robustness_data = read_csv(results_dir / 'robustness_under_noise.csv')
    print(f"   ✅ Loaded {len(ppo_data)} PPO runs")
    print(f"   ✅ Loaded {len(hybrid_data)} Hybrid runs")
    print(f"   ✅ Loaded {len(robustness_data)} robustness runs")
    
    # Generate plots
    print("\n📈 Generating plots...")
    
    plot_returns_vs_latency(
        hybrid_data,
        plots_dir / 'returns_vs_latency.png'
    )
    
    plot_containment_vs_cadence(
        ppo_data,
        hybrid_data,
        plots_dir / 'containment_vs_cadence.png'
    )
    
    plot_completion_rate_boxplot(
        ppo_data,
        hybrid_data,
        plots_dir / 'completion_rate_boxplot.png'
    )
    
    plot_robustness_under_noise(
        robustness_data,
        plots_dir / 'robustness_under_noise.png'
    )
    
    print("\n" + "=" * 60)
    print("✅ All 4 publication-quality plots generated successfully!")
    print(f"📁 Plots saved to: {plots_dir}")
    print("=" * 60)

if __name__ == '__main__':
    main()
