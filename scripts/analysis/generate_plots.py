#!/usr/bin/env python3
"""
Generate publication-quality plots for AURORA evaluation
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Style
sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (16, 12)
plt.rcParams['font.size'] = 11

base_dir = Path("results+models")

# Load all data
all_data = []
for model_dir in sorted(base_dir.iterdir()):
    if not model_dir.is_dir():
        continue
    
    seed_dirs = [d for d in model_dir.iterdir() if d.is_dir() and d.name.startswith("seed_")]
    
    for seed_dir in sorted(seed_dirs):
        csv_file = seed_dir / "episodes.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            df['model'] = model_dir.name
            df['seed'] = seed_dir.name
            all_data.append(df)

df_all = pd.concat(all_data, ignore_index=True)

# Create figures
fig = plt.figure(figsize=(20, 14))

# =============================================================================
# PLOT 1: Episode Return Over Training Time
# =============================================================================
ax1 = plt.subplot(2, 3, 1)
colors = {'ppo_baseline_no_llm': '#FF6B6B', 
          'ppo_llm_qwen2_5_3b_freq50': '#4ECDC4',
          'ppo_llm_qwen2_5_7b_freq50': '#95E1D3'}

for model_name in ['ppo_baseline_no_llm', 'ppo_llm_qwen2_5_3b_freq50', 'ppo_llm_qwen2_5_7b_freq50']:
    df_model = df_all[df_all['model'] == model_name].reset_index(drop=True)
    
    # Rolling average
    window = 50
    rolling = df_model['episode_return'].rolling(window=window, center=True).mean()
    
    ax1.plot(rolling.index, rolling.values, label=model_name.replace('ppo_', '').replace('_no_llm', ' (Baseline)'), 
             linewidth=2.5, color=colors[model_name], alpha=0.8)

ax1.set_xlabel('Episode', fontsize=12, fontweight='bold')
ax1.set_ylabel('Return (50-step Rolling Avg)', fontsize=12, fontweight='bold')
ax1.set_title('Training Progress: Episode Return', fontsize=13, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# =============================================================================
# PLOT 2: Final Return Distribution by Seed
# =============================================================================
ax2 = plt.subplot(2, 3, 2)

final_returns = []
for model_name in ['ppo_baseline_no_llm', 'ppo_llm_qwen2_5_3b_freq50', 'ppo_llm_qwen2_5_7b_freq50']:
    df_model = df_all[df_all['model'] == model_name]
    for seed in df_model['seed'].unique():
        df_seed = df_model[df_model['seed'] == seed]
        final_ret = df_seed['episode_return'].iloc[-1]
        final_returns.append({
            'model': model_name.replace('ppo_', '').replace('_no_llm', ' (Baseline)'),
            'seed': seed,
            'final_return': final_ret
        })

df_final = pd.DataFrame(final_returns)
df_final_pivot = df_final.pivot(index='seed', columns='model', values='final_return')

x = np.arange(len(df_final_pivot.index))
width = 0.25

for i, col in enumerate(df_final_pivot.columns):
    offset = (i - 1) * width
    ax2.bar(x + offset, df_final_pivot[col].values, width, label=col, color=list(colors.values())[i], alpha=0.8)

ax2.set_xlabel('Random Seed', fontsize=12, fontweight='bold')
ax2.set_ylabel('Final Episode Return', fontsize=12, fontweight='bold')
ax2.set_title('Final Return by Seed', fontsize=13, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(df_final_pivot.index)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3, axis='y')

# Add values on bars
for i, col in enumerate(df_final_pivot.columns):
    for j, v in enumerate(df_final_pivot[col].values):
        ax2.text(j + (i-1)*width, v + 1, f'{v:.1f}', ha='center', va='bottom', fontsize=8)

# =============================================================================
# PLOT 3: Fire Containment Performance
# =============================================================================
ax3 = plt.subplot(2, 3, 3)

containment_by_seed = []
for model_name in ['ppo_baseline_no_llm', 'ppo_llm_qwen2_5_3b_freq50', 'ppo_llm_qwen2_5_7b_freq50']:
    df_model = df_all[df_all['model'] == model_name]
    avg_containment = df_model.groupby('seed')['final_containment'].mean().mean()
    std_containment = df_model.groupby('seed')['final_containment'].mean().std()
    
    containment_by_seed.append({
        'model': model_name.replace('ppo_', '').replace('_no_llm', ' (Baseline)'),
        'avg': avg_containment,
        'std': std_containment
    })

df_cont = pd.DataFrame(containment_by_seed)
ax3.bar(range(len(df_cont)), df_cont['avg'].values, yerr=df_cont['std'].values, 
        color=list(colors.values()), alpha=0.8, capsize=5, width=0.6)
ax3.set_xticks(range(len(df_cont)))
ax3.set_xticklabels(df_cont['model'].values, rotation=15, ha='right', fontsize=10)
ax3.set_ylabel('Final Containment (%)', fontsize=12, fontweight='bold')
ax3.set_title('Fire Containment Performance', fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')

# Add value labels
for i, v in enumerate(df_cont['avg'].values):
    ax3.text(i, v + df_cont['std'].values[i] + 0.02, f'{v:.2%}', ha='center', va='bottom', fontweight='bold')

# =============================================================================
# PLOT 4: Improvement Scatter (Seed 3003 vs 4004 Effects)
# =============================================================================
ax4 = plt.subplot(2, 3, 4)

seeds_of_interest = ['seed_3003', 'seed_4004']
improvements = []

for seed in seeds_of_interest:
    baseline_return = df_all[(df_all['model'] == 'ppo_baseline_no_llm') & (df_all['seed'] == seed)]['episode_return'].iloc[-1]
    qwen_return = df_all[(df_all['model'] == 'ppo_llm_qwen2_5_3b_freq50') & (df_all['seed'] == seed)]['episode_return'].iloc[-1]
    improvement_pct = ((qwen_return - baseline_return) / baseline_return) * 100
    
    improvements.append({'seed': seed, 'improvement': improvement_pct})

df_imp = pd.DataFrame(improvements)
bars = ax4.bar(df_imp['seed'].values, df_imp['improvement'].values, 
               color=['#FF6B6B' if x < 0 else '#4ECDC4' for x in df_imp['improvement'].values], 
               alpha=0.8, width=0.5)
ax4.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax4.set_ylabel('Improvement (%)', fontsize=12, fontweight='bold')
ax4.set_title('Qwen 3B Improvement on Harder Seeds', fontsize=13, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')

# Add value labels
for i, (seed, imp) in enumerate(zip(df_imp['seed'].values, df_imp['improvement'].values)):
    ax4.text(i, imp + (2 if imp > 0 else -5), f'{imp:+.1f}%', ha='center', 
             va='bottom' if imp > 0 else 'top', fontweight='bold', fontsize=11)

# =============================================================================
# PLOT 5: Mean Return Comparison
# =============================================================================
ax5 = plt.subplot(2, 3, 5)

mean_returns = []
for model_name in ['ppo_baseline_no_llm', 'ppo_llm_qwen2_5_3b_freq50', 'ppo_llm_qwen2_5_7b_freq50']:
    df_model = df_all[df_all['model'] == model_name]
    mean_ret = df_model['episode_return'].mean()
    std_ret = df_model['episode_return'].std()
    
    mean_returns.append({
        'model': model_name.replace('ppo_', '').replace('_no_llm', ' (Baseline)'),
        'mean': mean_ret,
        'std': std_ret
    })

df_mean = pd.DataFrame(mean_returns)
ax5.bar(range(len(df_mean)), df_mean['mean'].values, yerr=df_mean['std'].values,
        color=list(colors.values()), alpha=0.8, capsize=5, width=0.6)
ax5.set_xticks(range(len(df_mean)))
ax5.set_xticklabels(df_mean['model'].values, rotation=15, ha='right', fontsize=10)
ax5.set_ylabel('Mean Episode Return', fontsize=12, fontweight='bold')
ax5.set_title('Average Performance Across All Episodes', fontsize=13, fontweight='bold')
ax5.grid(True, alpha=0.3, axis='y')

# Add value labels
for i, v in enumerate(df_mean['mean'].values):
    ax5.text(i, v + df_mean['std'].values[i] + 0.5, f'{v:.2f}', ha='center', va='bottom', fontweight='bold')

# =============================================================================
# PLOT 6: Summary Statistics Table
# =============================================================================
ax6 = plt.subplot(2, 3, 6)
ax6.axis('tight')
ax6.axis('off')

summary_stats = []
for model_name in ['ppo_baseline_no_llm', 'ppo_llm_qwen2_5_3b_freq50', 'ppo_llm_qwen2_5_7b_freq50']:
    df_model = df_all[df_all['model'] == model_name]
    
    final_ret = df_model.groupby('seed')['episode_return'].tail(1).mean()
    mean_ret = df_model['episode_return'].mean()
    episodes = len(df_model)
    
    summary_stats.append([
        model_name.replace('ppo_', '').replace('_no_llm', 'PPO (Baseline)'),
        f"{episodes:,}",
        f"{final_ret:.2f}",
        f"{mean_ret:.2f}"
    ])

table = ax6.table(cellText=summary_stats,
                  colLabels=['Model', 'Episodes', 'Final Return', 'Mean Return'],
                  cellLoc='center',
                  loc='center',
                  bbox=[0, 0, 1, 1])

table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2.5)

# Style header
for i in range(4):
    table[(0, i)].set_facecolor('#4ECDC4')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Alternate row colors
for i in range(1, len(summary_stats) + 1):
    for j in range(4):
        if i % 2 == 0:
            table[(i, j)].set_facecolor('#F0F0F0')
        else:
            table[(i, j)].set_facecolor('#FFFFFF')

ax6.set_title('Summary Statistics', fontsize=13, fontweight='bold', pad=20)

plt.suptitle('AURORA: PPO vs Hybrid PPO+LLM Performance Analysis', 
             fontsize=16, fontweight='bold', y=0.995)

plt.tight_layout()
plt.savefig('results/aurora_evaluation_plots.png', dpi=300, bbox_inches='tight')
print("✅ Saved: results/aurora_evaluation_plots.png")

plt.show()

# =============================================================================
# Create metrics CSV
# =============================================================================
metrics_data = []

for model_name in ['ppo_baseline_no_llm', 'ppo_llm_qwen2_5_3b_freq50', 'ppo_llm_qwen2_5_7b_freq50']:
    df_model = df_all[df_all['model'] == model_name]
    
    for seed in sorted(df_model['seed'].unique()):
        df_seed = df_model[df_model['seed'] == seed]
        
        metrics_data.append({
            'model': model_name,
            'seed': seed,
            'num_episodes': len(df_seed),
            'final_return': df_seed['episode_return'].iloc[-1],
            'mean_return': df_seed['episode_return'].mean(),
            'std_return': df_seed['episode_return'].std(),
            'final_containment': df_seed['final_containment'].iloc[-1],
            'avg_containment': df_seed['avg_containment'].mean(),
            'final_fire_coverage': df_seed['final_fire_coverage'].iloc[-1],
            'avg_episode_length': df_seed['episode_length'].mean(),
            'avg_containment_step': df_seed['containment_reach_step'].mean(),
        })

df_metrics = pd.DataFrame(metrics_data)
df_metrics.to_csv('results/aurora_metrics.csv', index=False)
print("✅ Saved: results/aurora_metrics.csv")

# Print summary
print("\n" + "="*80)
print("📊 METRICS SUMMARY")
print("="*80)
print(df_metrics.to_string())
print("\n" + "="*80)
