#!/usr/bin/env python3
"""
Detailed analysis of benchmark results including:
- Fire-weight comparison
- Timeout trial analysis (hit max_ticks=3000)
- Last rescue tick analysis
- Replanning statistics
"""

import json
import sys


def analyze_benchmark(filename):
    """Load and analyze a benchmark JSON file in detail."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)

        trials = data['trials']
        n = len(trials)

        # Get fire_weight from config
        fire_weight = data.get('config', {}).get('fire_priority_weight', 0.0)

        # Basic statistics
        survival_rates = [t['survival_rate'] for t in trials]
        rescued = [t['rescued'] for t in trials]
        dead = [t['dead'] for t in trials]

        avg_survival = sum(survival_rates) / n
        avg_rescued = sum(rescued) / n
        avg_dead = sum(dead) / n

        variance = sum((x - avg_survival) ** 2 for x in survival_rates) / n
        std_survival = variance ** 0.5

        # Timeout trials (hit max_ticks=3000)
        timeout_trials = [t for t in trials if t['total_ticks'] >= 3000]
        timeout_rate = len(timeout_trials) / n * 100

        # Last rescue tick analysis (if available)
        has_last_rescue = 'last_rescue_tick' in trials[0]
        if has_last_rescue:
            last_rescue_ticks = [t['last_rescue_tick'] for t in trials]
            avg_last_rescue = sum(last_rescue_ticks) / n

            # Efficiency: how much time wasted after last rescue?
            total_ticks = [t['total_ticks'] for t in trials]
            wasted_ticks = [total - last for total, last in zip(total_ticks, last_rescue_ticks)]
            avg_wasted = sum(wasted_ticks) / n
        else:
            avg_last_rescue = None
            avg_wasted = None

        # Replanning statistics
        replan_counts = [t.get('replan_count', 0) for t in trials]
        avg_replans = sum(replan_counts) / n
        max_replans = max(replan_counts)
        trials_with_replans = sum(1 for r in replan_counts if r > 0)

        return {
            'fire_weight': fire_weight,
            'trials': n,
            'avg_survival': avg_survival,
            'std_survival': std_survival,
            'avg_rescued': avg_rescued,
            'avg_dead': avg_dead,
            'best_survival': max(survival_rates),
            'worst_survival': min(survival_rates),
            'timeout_count': len(timeout_trials),
            'timeout_rate': timeout_rate,
            'avg_last_rescue': avg_last_rescue,
            'avg_wasted_ticks': avg_wasted,
            'avg_replans': avg_replans,
            'max_replans': max_replans,
            'trials_with_replans': trials_with_replans,
        }
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print(f"Warning: {filename} is not valid JSON (benchmark may still be running)")
        return None


def main():
    """Analyze all fire-weight benchmarks with detailed metrics."""
    files = [
        ('sweep_benchmark_100.json', 'Baseline'),
        ('sweep_fw1.0.json', 'Moderate'),
        ('sweep_fw2.0.json', 'Strong'),
        ('sweep_fw5.0.json', 'Very Strong'),
    ]

    results = []
    for fname, label in files:
        result = analyze_benchmark(fname)
        if result:
            result['label'] = label
            results.append(result)

    if not results:
        print("No benchmark results found yet. Please wait for benchmarks to complete.")
        return

    # Sort by fire_weight
    results.sort(key=lambda x: x['fire_weight'])

    print("="*90)
    print("DETAILED FIRE-WEIGHT ANALYSIS")
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

    # Timeout analysis
    print("TIMEOUT ANALYSIS (Trials hitting max_ticks=3000)")
    print("-"*90)
    print(f"{'Label':<15} {'FW':<6} {'Timeouts':<12} {'Rate':<10}")
    print("-"*90)
    for r in results:
        print(f"{r['label']:<15} {r['fire_weight']:<6.1f} "
              f"{r['timeout_count']:<12} {r['timeout_rate']:<10.1f}%")
    print()
    print("Note: Timeout trials represent failed evacuations (>600 sec / 10 min simulated time)")
    print("Lower timeout rate = more efficient evacuation strategy")
    print()

    # Last rescue tick analysis (if available)
    if results[0]['avg_last_rescue'] is not None:
        print("EVACUATION EFFICIENCY (Last Rescue Tick)")
        print("-"*90)
        print(f"{'Label':<15} {'FW':<6} {'Avg Last Rescue':<18} {'Avg Wasted Ticks':<18}")
        print("-"*90)
        for r in results:
            print(f"{r['label']:<15} {r['fire_weight']:<6.1f} "
                  f"{r['avg_last_rescue']:<18.1f} {r['avg_wasted_ticks']:<18.1f}")
        print()
        print("Note: Wasted ticks = time spent after last person rescued")
        print("This happens when firefighters are still executing rescue plans after everyone is saved")
        print()

    # Replanning analysis
    print("REPLANNING STATISTICS")
    print("-"*90)
    print(f"{'Label':<15} {'FW':<6} {'Avg Replans':<14} {'Max Replans':<14} {'Trials w/ Replans':<18}")
    print("-"*90)
    for r in results:
        replan_pct = r['trials_with_replans'] / r['trials'] * 100
        print(f"{r['label']:<15} {r['fire_weight']:<6.1f} "
              f"{r['avg_replans']:<14.2f} {r['max_replans']:<14} "
              f"{r['trials_with_replans']}/{r['trials']} ({replan_pct:.1f}%)")
    print()

    if all(r['avg_replans'] == 0 for r in results):
        print("⚠️  WARNING: No replanning detected in any trials!")
        print("   This suggests the replanning algorithm may not be working correctly.")
        print()

    # Best configuration
    print("="*90)
    print("RECOMMENDATION")
    print("="*90)
    best = max(results, key=lambda x: x['avg_survival'])
    print(f"Best fire-weight: {best['fire_weight']} ({best['label']})")
    print(f"  Avg survival: {best['avg_survival']:.2f}% (±{best['std_survival']:.2f}%)")
    print(f"  Avg rescued: {best['avg_rescued']:.1f}")
    print(f"  Timeout rate: {best['timeout_rate']:.1f}%")

    baseline = next((r for r in results if r['fire_weight'] == 0.0), None)
    if baseline and best['fire_weight'] != 0.0:
        improvement = best['avg_survival'] - baseline['avg_survival']
        print(f"  Improvement over baseline: {improvement:+.2f}%")
    print()
    print("="*90)


if __name__ == '__main__':
    main()
