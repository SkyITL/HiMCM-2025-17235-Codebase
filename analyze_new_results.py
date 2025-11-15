#!/usr/bin/env python3
"""
Analyze new fixed-seed benchmark results with working replanning.
Compare fire-weight values (0.0, 1.0, 2.0, 5.0) on identical scenarios.
"""

import json

def analyze_benchmark(filename):
    """Load and analyze a benchmark JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)

        trials = data['trials']
        n = len(trials)

        # Get fire_weight from config
        fire_weight = data.get('config', {}).get('fire_priority_weight', 0.0)

        # Filter valid trials (phase transitioned)
        valid_trials = [t for t in trials if t.get('phase_transitioned', False)]

        if not valid_trials:
            return None

        # Basic statistics
        survival_rates = [t['survival_rate'] for t in valid_trials]
        rescued = [t['rescued'] for t in valid_trials]
        dead = [t['dead'] for t in valid_trials]

        avg_survival = sum(survival_rates) / len(valid_trials)
        avg_rescued = sum(rescued) / len(valid_trials)
        avg_dead = sum(dead) / len(valid_trials)

        variance = sum((x - avg_survival) ** 2 for x in survival_rates) / len(valid_trials)
        std_survival = variance ** 0.5

        # Replanning statistics
        replan_counts = [t.get('replan_count', 0) for t in valid_trials]
        avg_replans = sum(replan_counts) / len(valid_trials)
        max_replans = max(replan_counts)

        # Last rescue tick analysis
        last_rescue_ticks = [t['last_rescue_tick'] for t in valid_trials]
        avg_last_rescue = sum(last_rescue_ticks) / len(valid_trials)

        # Wasted time
        total_ticks = [t['total_ticks'] for t in valid_trials]
        wasted_ticks = [total - last for total, last in zip(total_ticks, last_rescue_ticks)]
        avg_wasted = sum(wasted_ticks) / len(valid_trials)

        return {
            'fire_weight': fire_weight,
            'trials': n,
            'valid_trials': len(valid_trials),
            'avg_survival': avg_survival,
            'std_survival': std_survival,
            'avg_rescued': avg_rescued,
            'avg_dead': avg_dead,
            'best_survival': max(survival_rates),
            'worst_survival': min(survival_rates),
            'avg_replans': avg_replans,
            'max_replans': max_replans,
            'avg_last_rescue': avg_last_rescue,
            'avg_wasted_ticks': avg_wasted,
        }
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def main():
    """Analyze all fire-weight benchmarks."""
    files = [
        ('fixed_fw0.0_2ff.json', 'Baseline'),
        ('fixed_fw1.0_2ff.json', 'Moderate'),
        ('fixed_fw2.0_2ff.json', 'Strong'),
        ('fixed_fw5.0_2ff.json', 'Very Strong'),
    ]

    results = []
    for fname, label in files:
        result = analyze_benchmark(fname)
        if result:
            result['label'] = label
            results.append(result)

    if not results:
        print("No benchmark results found.")
        return

    # Sort by fire_weight
    results.sort(key=lambda x: x['fire_weight'])

    print("="*90)
    print("FIXED-SEED FIRE-WEIGHT ANALYSIS (2 Firefighters, Working Replanning)")
    print("="*90)
    print()

    # Survival rate comparison
    print("SURVIVAL RATE COMPARISON")
    print("-"*90)
    print(f"{'Label':<15} {'FW':<6} {'Survival':<12} {'StdDev':<10} {'Best':<10} {'Worst':<10}")
    print("-"*90)
    for r in results:
        print(f"{r['label']:<15} {r['fire_weight']:<6.1f} "
              f"{r['avg_survival']:<12.2f}% {r['std_survival']:<10.2f}% "
              f"{r['best_survival']:<10.1f}% {r['worst_survival']:<10.1f}%")
    print()

    # Replanning statistics
    print("REPLANNING STATISTICS (Confirms replanning is working)")
    print("-"*90)
    print(f"{'Label':<15} {'FW':<6} {'Avg Replans':<14} {'Max Replans':<14}")
    print("-"*90)
    for r in results:
        print(f"{r['label']:<15} {r['fire_weight']:<6.1f} "
              f"{r['avg_replans']:<14.2f} {r['max_replans']:<14}")
    print()

    # Evacuation efficiency
    print("EVACUATION EFFICIENCY")
    print("-"*90)
    print(f"{'Label':<15} {'FW':<6} {'Avg Last Rescue':<18} {'Avg Wasted Ticks':<18}")
    print("-"*90)
    for r in results:
        print(f"{r['label']:<15} {r['fire_weight']:<6.1f} "
              f"{r['avg_last_rescue']:<18.1f} {r['avg_wasted_ticks']:<18.1f}")
    print()

    # Best configuration
    print("="*90)
    print("RECOMMENDATION")
    print("="*90)
    best = max(results, key=lambda x: x['avg_survival'])
    print(f"Best fire-weight: {best['fire_weight']} ({best['label']})")
    print(f"  Avg survival: {best['avg_survival']:.2f}% (±{best['std_survival']:.2f}%)")
    print(f"  Avg rescued: {best['avg_rescued']:.1f}")
    print(f"  Avg replans: {best['avg_replans']:.2f}")

    baseline = next((r for r in results if r['fire_weight'] == 0.0), None)
    if baseline and best['fire_weight'] != 0.0:
        improvement = best['avg_survival'] - baseline['avg_survival']
        print(f"  Improvement over baseline: {improvement:+.2f}%")
    print()
    print("="*90)


if __name__ == '__main__':
    main()
