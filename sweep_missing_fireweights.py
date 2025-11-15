#!/usr/bin/env python3
"""
Complete the fire-weight sweep by running only missing fire-weight values.
"""

import json
import subprocess
import sys
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time

# Missing fire-weight values (those that failed or didn't run)
MISSING_FW = [0.00, 1.05, 3.42, 3.68, 3.95, 4.21, 4.47, 4.74, 5.00]


def run_benchmark(fire_weight, num_trials=200, num_firefighters=2):
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


def main():
    """Run only missing fire-weight benchmarks."""
    num_workers = max(1, multiprocessing.cpu_count() - 1)

    print("="*70)
    print("COMPLETING FIRE-WEIGHT PARAMETER SWEEP (MISSING VALUES ONLY)")
    print("="*70)
    print(f"Missing fire-weight values: {len(MISSING_FW)}")
    print(f"Values: {', '.join(f'{fw:.2f}' for fw in MISSING_FW)}")
    print(f"Trials per value: 200")
    print(f"Firefighters: 2")
    print(f"Parallel workers: {num_workers}")
    print("="*70)
    print()

    start_time = time.time()
    results = []

    # Run benchmarks in parallel
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_fw = {
            executor.submit(run_benchmark, fw, 200, 2): fw
            for fw in MISSING_FW
        }

        completed = 0
        for future in as_completed(future_to_fw):
            fw = future_to_fw[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                completed += 1
                print(f"Progress: {completed}/{len(MISSING_FW)} missing fire-weight values completed")
            except Exception as e:
                print(f"ERROR: fire-weight={fw:.2f} raised exception: {e}")

    elapsed = time.time() - start_time
    print()
    print("="*70)
    print(f"Missing benchmarks completed in {elapsed/60:.1f} minutes")
    print(f"Successfully completed: {len(results)}/{len(MISSING_FW)}")
    print("="*70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
