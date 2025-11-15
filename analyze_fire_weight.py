#!/usr/bin/env python3
"""
Analyze fire-weight tuning results.

Compare survival rates and rescue efficiency across different fire-weight values.
"""

import json
import sys

def analyze_benchmark(filename):
    """Load and analyze a benchmark JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)

        trials = data['trials']
        n = len(trials)

        survival_rates = [t['survival_rate'] for t in trials]
        rescued = [t['rescued'] for t in trials]
        dead = [t['dead'] for t in trials]

        avg_survival = sum(survival_rates) / n
        avg_rescued = sum(rescued) / n
        avg_dead = sum(dead) / n

        # Calculate std dev
        variance = sum((x - avg_survival) ** 2 for x in survival_rates) / n
        std_survival = variance ** 0.5

        # Get fire_weight from config
        fire_weight = data.get('config', {}).get('fire_priority_weight', 0.0)

        return {
            'fire_weight': fire_weight,
            'trials': n,
            'avg_survival': avg_survival,
            'std_survival': std_survival,
            'avg_rescued': avg_rescued,
            'avg_dead': avg_dead,
            'best_survival': max(survival_rates),
            'worst_survival': min(survival_rates)
        }
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print(f"Warning: {filename} is not valid JSON (benchmark may still be running)")
        return None


def main():
    """Analyze all fire-weight benchmarks."""
    files = [
        'sweep_benchmark_100.json',  # fire_weight=0.0
        'sweep_fw1.0.json',           # fire_weight=1.0
        'sweep_fw2.0.json',           # fire_weight=2.0
        'sweep_fw5.0.json',           # fire_weight=5.0
    ]

    results = []
    for fname in files:
        result = analyze_benchmark(fname)
        if result:
            results.append(result)

    if not results:
        print("No benchmark results found yet. Please wait for benchmarks to complete.")
        return

    # Sort by fire_weight
    results.sort(key=lambda x: x['fire_weight'])

    print("="*80)
    print("FIRE-WEIGHT TUNING RESULTS")
    print("="*80)
    print()
    print(f"{'Fire Weight':<12} {'Avg Survival':<14} {'Std Dev':<10} {'Avg Rescued':<12} {'Avg Dead':<10}")
    print("-" * 80)

    for r in results:
        print(f"{r['fire_weight']:<12.1f} {r['avg_survival']:<14.2f}% {r['std_survival']:<10.2f}% "
              f"{r['avg_rescued']:<12.1f} {r['avg_dead']:<10.1f}")

    print()
    print("Best configuration:")
    best = max(results, key=lambda x: x['avg_survival'])
    print(f"  Fire weight: {best['fire_weight']}")
    print(f"  Avg survival: {best['avg_survival']:.2f}% (±{best['std_survival']:.2f}%)")
    print(f"  Avg rescued: {best['avg_rescued']:.1f}")
    print()

    # Show improvement
    baseline = next((r for r in results if r['fire_weight'] == 0.0), None)
    if baseline and best['fire_weight'] != 0.0:
        improvement = best['avg_survival'] - baseline['avg_survival']
        print(f"Improvement over baseline (fw=0.0): {improvement:+.2f}%")

    print("="*80)


if __name__ == '__main__':
    main()
