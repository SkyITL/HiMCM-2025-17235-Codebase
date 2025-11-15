#!/usr/bin/env python3
"""
Analyze fire-weight sweep results and create publication-quality visualization.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Collect all results
fire_weights = np.linspace(0.0, 5.0, 20)
results = []

print("Collecting results from all 20 benchmarks...")
for fw in fire_weights:
    filename = f"sweep_fw{fw:.2f}.json"
    try:
        with open(filename, 'r') as f:
            data = json.load(f)

        # Filter valid trials
        trials = data['trials']
        valid_trials = [t for t in trials if t.get('phase_transitioned', False)]

        if valid_trials:
            survival_rates = [t['survival_rate'] for t in valid_trials]
            results.append({
                'fire_weight': fw,
                'avg_survival': np.mean(survival_rates),
                'min_survival': np.min(survival_rates),
                'max_survival': np.max(survival_rates),
                'std_survival': np.std(survival_rates),
                'valid_trials': len(valid_trials),
                'total_trials': len(trials),
            })
            print(f"  {fw:.2f}: avg={np.mean(survival_rates):.1f}% ({len(valid_trials)} trials)")
    except FileNotFoundError:
        print(f"  WARNING: {filename} not found")

# Save consolidated results
with open('fire_weight_sweep_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nCollected {len(results)}/20 fire-weight values")
print(f"Results saved to: fire_weight_sweep_results.json")

# Extract data for plotting
fw_values = [r['fire_weight'] for r in results]
avg_survival = [r['avg_survival'] for r in results]
min_survival = [r['min_survival'] for r in results]
max_survival = [r['max_survival'] for r in results]
std_survival = [r['std_survival'] for r in results]

# Find optimal
best_idx = np.argmax(avg_survival)
best_fw = fw_values[best_idx]
best_avg = avg_survival[best_idx]

print(f"\n{'='*70}")
print("OPTIMAL FIRE-WEIGHT PARAMETER")
print(f"{'='*70}")
print(f"Fire-weight: {best_fw:.2f}")
print(f"Average survival rate: {best_avg:.2f}%")
print(f"Minimum survival rate: {min_survival[best_idx]:.2f}%")
print(f"Maximum survival rate: {max_survival[best_idx]:.2f}%")
print(f"Standard deviation: {std_survival[best_idx]:.2f}%")
print(f"{'='*70}")

# Create simplified visualization focusing ONLY on average survival rate
fig, ax = plt.subplots(figsize=(12, 7))

# Plot average survival rate only
line_avg = ax.plot(fw_values, avg_survival, 'b-o', linewidth=3.5, markersize=10,
                   label='Average Survival Rate', zorder=3)

# Mark optimal point prominently
ax.plot(best_fw, best_avg, 'g*', markersize=30, label=f'Optimal: fw={best_fw:.2f}',
        zorder=4, markeredgecolor='darkgreen', markeredgewidth=2)
ax.axvline(best_fw, color='green', linestyle=':', linewidth=2.5, alpha=0.7, zorder=0)

# TIGHT scaling - focus only on the range of average survival rates
# Add minimal padding to make variations very conspicuous
avg_min = min(avg_survival)
avg_max = max(avg_survival)
avg_range = avg_max - avg_min
padding = avg_range * 0.3  # 30% padding for visibility

ax.set_ylim(avg_min - padding, avg_max + padding)

# Enhanced grid for easier reading
ax.grid(True, alpha=0.4, linestyle='--', linewidth=1, which='both')
ax.grid(True, alpha=0.2, linestyle=':', linewidth=0.5, which='minor', axis='y')
ax.minorticks_on()

ax.set_xlabel('Fire-Weight Parameter', fontsize=14, fontweight='bold')
ax.set_ylabel('Average Survival Rate (%)', fontsize=14, fontweight='bold')
ax.set_title('Fire-Weight Parameter Sweep: Average Survival Rate\n(2 Firefighters, 200 Trials per Value)',
             fontsize=16, fontweight='bold', pad=20)
ax.legend(loc='best', fontsize=12, framealpha=0.95)

# Annotate the optimal point with exact value
ax.annotate(f'{best_avg:.2f}%',
            xy=(best_fw, best_avg),
            xytext=(best_fw + 0.4, best_avg + 0.15),
            fontsize=13, fontweight='bold', color='darkgreen',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.8),
            arrowprops=dict(arrowstyle='->', color='darkgreen', lw=2))

# Annotate min and max for context
min_idx = np.argmin(avg_survival)
max_idx = np.argmax(avg_survival)
if min_idx != max_idx:
    ax.annotate(f'Min: {avg_survival[min_idx]:.2f}%',
                xy=(fw_values[min_idx], avg_survival[min_idx]),
                xytext=(fw_values[min_idx] - 0.5, avg_survival[min_idx] - 0.25),
                fontsize=10, color='darkred',
                arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5))

plt.tight_layout()
plt.savefig('fire_weight_sweep_focused.png', dpi=300, bbox_inches='tight')
print(f"\nFocused visualization (avg only) saved to: fire_weight_sweep_focused.png")

# Also keep the original multi-panel visualization for reference
fig2 = plt.figure(figsize=(14, 10))
gs = fig2.add_gridspec(3, 1, height_ratios=[2, 1.2, 1], hspace=0.3)

# Panel 1: Survival Rates (larger, more prominent)
ax1 = fig2.add_subplot(gs[0])

# Plot lines
line_avg = ax1.plot(fw_values, avg_survival, 'b-o', linewidth=3, markersize=8,
                    label='Average Survival Rate', zorder=3)
line_min = ax1.plot(fw_values, min_survival, 'r--s', linewidth=2.5, markersize=6,
                    label='Minimum Survival Rate', zorder=2, alpha=0.8)

# Shaded region for std dev
ax1.fill_between(fw_values,
                 [avg - std for avg, std in zip(avg_survival, std_survival)],
                 [avg + std for avg, std in zip(avg_survival, std_survival)],
                 alpha=0.25, color='cornflowerblue', label='±1σ Std Dev', zorder=1)

# Mark optimal point
ax1.plot(best_fw, best_avg, 'g*', markersize=25, label=f'Optimal: fw={best_fw:.2f}',
         zorder=4, markeredgecolor='darkgreen', markeredgewidth=1.5)
ax1.axvline(best_fw, color='green', linestyle=':', linewidth=2, alpha=0.6, zorder=0)

# Improved axis scaling - focus on the interesting range
y_min = min(min_survival) - 5
y_max = max(max_survival) + 5
ax1.set_ylim(y_min, y_max)

ax1.set_xlabel('Fire-Weight Parameter', fontsize=13, fontweight='bold')
ax1.set_ylabel('Survival Rate (%)', fontsize=13, fontweight='bold')
ax1.set_title('Fire-Weight Parameter Sweep: Survival Rates\n(2 Firefighters, 200 Trials per Value)',
              fontsize=15, fontweight='bold', pad=15)
ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
ax1.legend(loc='lower right', fontsize=11, framealpha=0.95)

# Add annotations for key points
ax1.annotate(f'{best_avg:.1f}%',
             xy=(best_fw, best_avg),
             xytext=(best_fw + 0.3, best_avg + 3),
             fontsize=11, fontweight='bold', color='darkgreen',
             arrowprops=dict(arrowstyle='->', color='darkgreen', lw=1.5))

# Panel 2: Standard Deviation (medium size)
ax2 = fig2.add_subplot(gs[1])

# Use bar chart for better visibility
colors = ['green' if fw == best_fw else 'steelblue' for fw in fw_values]
bars = ax2.bar(fw_values, std_survival, width=0.22, color=colors, alpha=0.7,
               edgecolor='black', linewidth=0.8)

# Highlight optimal
ax2.axvline(best_fw, color='green', linestyle=':', linewidth=2, alpha=0.6)

ax2.set_xlabel('Fire-Weight Parameter', fontsize=12, fontweight='bold')
ax2.set_ylabel('Std Dev (%)', fontsize=12, fontweight='bold', color='steelblue')
ax2.set_title('Consistency Analysis: Standard Deviation of Survival Rates',
              fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.8)
ax2.tick_params(axis='y', labelcolor='steelblue')

# Set y-axis to start from 0 for std dev
ax2.set_ylim(0, max(std_survival) * 1.15)

# Panel 3: Range (smaller)
ax3 = fig2.add_subplot(gs[2])

survival_range = [max_val - min_val for max_val, min_val in zip(max_survival, min_survival)]
colors_range = ['green' if fw == best_fw else 'purple' for fw in fw_values]
bars_range = ax3.bar(fw_values, survival_range, width=0.22, color=colors_range, alpha=0.7,
                     edgecolor='black', linewidth=0.8)

ax3.axvline(best_fw, color='green', linestyle=':', linewidth=2, alpha=0.6)

ax3.set_xlabel('Fire-Weight Parameter', fontsize=12, fontweight='bold')
ax3.set_ylabel('Range (%)', fontsize=12, fontweight='bold', color='purple')
ax3.set_title('Variability Analysis: Range (Max - Min) of Survival Rates',
              fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.8)
ax3.tick_params(axis='y', labelcolor='purple')

# Set y-axis to start from 0 for range
ax3.set_ylim(0, max(survival_range) * 1.15)

plt.tight_layout()
plt.savefig('fire_weight_sweep_complete.png', dpi=300, bbox_inches='tight')
print(f"\nComplete multi-panel visualization saved to: fire_weight_sweep_complete.png")

# Print summary table
print(f"\n{'='*90}")
print("DETAILED RESULTS TABLE")
print(f"{'='*90}")
print(f"{'FW':<6} {'Avg %':<8} {'Min %':<8} {'Max %':<8} {'Std %':<8} {'Range %':<8} {'Trials':<10}")
print("-"*90)
for r in results:
    fw = r['fire_weight']
    marker = " ★" if fw == best_fw else ""
    range_val = r['max_survival'] - r['min_survival']
    print(f"{fw:<6.2f} {r['avg_survival']:<8.2f} {r['min_survival']:<8.2f} "
          f"{r['max_survival']:<8.2f} {r['std_survival']:<8.2f} {range_val:<8.2f} "
          f"{r['valid_trials']}/{r['total_trials']:<7}{marker}")
print(f"{'='*90}")

print("\nAnalysis complete!")
