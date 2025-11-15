#!/usr/bin/env python3
"""
Sweep fire-weight parameter from 0.0 to 5.0 with 20 intermediate values.
Run benchmarks and generate visualization of survival rates.

Uses parallel processing to run multiple benchmarks simultaneously.
"""

import json
import subprocess
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time


def run_benchmark(fire_weight, num_trials=20, num_firefighters=2):
    """Run benchmark for a specific fire-weight value."""
    output_file = f"sweep_fw{fire_weight:.2f}.json"

    start_time = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Starting fire-weight = {fire_weight:.2f}")

    cmd = [
        'python3', 'benchmark_mall_fast.py',
        '--trials', str(num_trials),
        '--fire-weight', str(fire_weight),
        '--firefighters', str(num_firefighters),
        '--output', output_file,
        '--quiet'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout

        if result.returncode != 0:
            elapsed = time.time() - start_time
            print(f"[{time.strftime('%H:%M:%S')}] FAILED fire-weight={fire_weight:.2f} ({elapsed:.1f}s)")
            print(result.stderr)
            return None

        # Load and parse results
        with open(output_file, 'r') as f:
            data = json.load(f)

        # Filter valid trials (phase transitioned)
        trials = data['trials']
        valid_trials = [t for t in trials if t.get('phase_transitioned', False)]

        if not valid_trials:
            elapsed = time.time() - start_time
            print(f"[{time.strftime('%H:%M:%S')}] WARNING fire-weight={fire_weight:.2f}: No valid trials ({elapsed:.1f}s)")
            return None

        survival_rates = [t['survival_rate'] for t in valid_trials]

        result_summary = {
            'fire_weight': fire_weight,
            'avg_survival': np.mean(survival_rates),
            'min_survival': np.min(survival_rates),
            'max_survival': np.max(survival_rates),
            'std_survival': np.std(survival_rates),
            'valid_trials': len(valid_trials),
            'total_trials': len(trials),
        }

        elapsed = time.time() - start_time
        print(f"[{time.strftime('%H:%M:%S')}] DONE fire-weight={fire_weight:.2f}: "
              f"avg={result_summary['avg_survival']:.1f}% min={result_summary['min_survival']:.1f}% ({elapsed:.1f}s)")

        return result_summary

    except subprocess.TimeoutExpired:
        print(f"ERROR: Benchmark timed out for fire-weight={fire_weight}")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def generate_plot(results, output_file='fire_weight_sweep.png'):
    """Generate visualization of fire-weight sweep results."""
    fire_weights = [r['fire_weight'] for r in results]
    avg_survival = [r['avg_survival'] for r in results]
    min_survival = [r['min_survival'] for r in results]
    max_survival = [r['max_survival'] for r in results]
    std_survival = [r['std_survival'] for r in results]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot 1: Average and Min Survival Rates
    ax1.plot(fire_weights, avg_survival, 'b-o', linewidth=2, markersize=6, label='Average Survival Rate')
    ax1.plot(fire_weights, min_survival, 'r--s', linewidth=2, markersize=5, label='Minimum Survival Rate')
    ax1.fill_between(fire_weights,
                     [avg - std for avg, std in zip(avg_survival, std_survival)],
                     [avg + std for avg, std in zip(avg_survival, std_survival)],
                     alpha=0.2, color='blue', label='±1 Std Dev')

    ax1.set_xlabel('Fire-Weight Parameter', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Survival Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Fire-Weight Parameter Sweep: Survival Rates (2 Firefighters, 20 Trials Each)',
                  fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best', fontsize=10)

    # Find and mark optimal fire-weight
    best_idx = np.argmax(avg_survival)
    best_fw = fire_weights[best_idx]
    best_avg = avg_survival[best_idx]
    ax1.axvline(best_fw, color='green', linestyle=':', linewidth=2, alpha=0.7, label=f'Optimal: {best_fw:.2f}')
    ax1.plot(best_fw, best_avg, 'g*', markersize=20, label=f'Best Avg: {best_avg:.2f}%')
    ax1.legend(loc='best', fontsize=10)

    # Plot 2: Range (Max - Min) and Std Dev
    survival_range = [max_val - min_val for max_val, min_val in zip(max_survival, min_survival)]

    ax2_twin = ax2.twinx()

    line1 = ax2.plot(fire_weights, survival_range, 'purple', marker='o', linewidth=2,
                     markersize=6, label='Range (Max - Min)')
    line2 = ax2_twin.plot(fire_weights, std_survival, 'orange', marker='s', linewidth=2,
                          markersize=5, label='Standard Deviation')

    ax2.set_xlabel('Fire-Weight Parameter', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Survival Rate Range (%)', fontsize=11, fontweight='bold', color='purple')
    ax2_twin.set_ylabel('Standard Deviation (%)', fontsize=11, fontweight='bold', color='orange')
    ax2.set_title('Fire-Weight Parameter Sweep: Consistency Metrics',
                  fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='y', labelcolor='purple')
    ax2_twin.tick_params(axis='y', labelcolor='orange')

    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc='upper right', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n{'='*70}")
    print(f"Plot saved to: {output_file}")
    print(f"{'='*70}")

    # Also display the plot
    plt.show()


def main():
    """Main sweep function with parallel processing."""
    # Generate 20 fire-weight values from 0.0 to 5.0
    fire_weights = np.linspace(0.0, 5.0, 20)

    # Determine number of workers (leave 1 core free for system)
    num_workers = max(1, multiprocessing.cpu_count() - 1)

    print("="*70)
    print("FIRE-WEIGHT PARAMETER SWEEP (PARALLEL)")
    print("="*70)
    print(f"Fire-weight values: {len(fire_weights)} points from 0.0 to 5.0")
    print(f"Trials per value: 200")
    print(f"Firefighters: 2")
    print(f"Max ticks: 400 (~80 seconds)")
    print(f"Total benchmarks: {len(fire_weights)} x 200 = {len(fire_weights) * 200} trials")
    print(f"Parallel workers: {num_workers}")
    print("="*70)
    print()

    start_time = time.time()
    results = []

    # Run benchmarks in parallel using ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all jobs
        future_to_fw = {
            executor.submit(run_benchmark, fw, 200, 2): fw
            for fw in fire_weights
        }

        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_fw):
            fw = future_to_fw[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                completed += 1
                print(f"Progress: {completed}/{len(fire_weights)} fire-weight values completed")
            except Exception as e:
                print(f"ERROR: fire-weight={fw:.2f} raised exception: {e}")

    elapsed = time.time() - start_time
    print()
    print("="*70)
    print(f"All benchmarks completed in {elapsed/60:.1f} minutes")
    print("="*70)

    if not results:
        print("\nERROR: No successful benchmarks!")
        return 1

    # Sort results by fire-weight for consistent output
    results.sort(key=lambda x: x['fire_weight'])

    # Save results summary
    summary_file = 'fire_weight_sweep_results.json'
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Results saved to: {summary_file}")
    print(f"{'='*70}")

    # Generate visualization
    generate_plot(results)

    # Print summary table
    print(f"\n{'='*70}")
    print("SUMMARY TABLE")
    print(f"{'='*70}")
    print(f"{'Fire-Weight':<12} {'Avg Survival':<14} {'Min Survival':<14} {'Std Dev':<10}")
    print("-"*70)
    for r in results:
        print(f"{r['fire_weight']:<12.2f} {r['avg_survival']:<14.2f}% {r['min_survival']:<14.2f}% {r['std_survival']:<10.2f}%")

    # Find optimal
    best = max(results, key=lambda x: x['avg_survival'])
    print(f"\n{'='*70}")
    print("OPTIMAL FIRE-WEIGHT")
    print(f"{'='*70}")
    print(f"Fire-weight: {best['fire_weight']:.2f}")
    print(f"Avg survival: {best['avg_survival']:.2f}%")
    print(f"Min survival: {best['min_survival']:.2f}%")
    print(f"Max survival: {best['max_survival']:.2f}%")
    print(f"Std dev: {best['std_survival']:.2f}%")
    print(f"{'='*70}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
