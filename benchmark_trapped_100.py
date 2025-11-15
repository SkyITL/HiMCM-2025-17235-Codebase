#!/usr/bin/env python3
"""
Run 100-trial benchmark with trapped firefighter detection.
"""

import json
import sys
import os
import time
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


def main():
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    num_trials = 100
    num_firefighters = 2
    fire_origins = ['room_1', 'room_2', 'room_7', 'room_10', 'room_15']

    print('='*80)
    print('K-MEDOIDS + MST SWEEP BENCHMARK WITH TRAPPED DETECTION')
    print('='*80)
    print(f'Trials: {num_trials}')
    print(f'Firefighters: {num_firefighters}')
    fire_origins_str = ', '.join(fire_origins)
    print(f'Fire origins: {len(fire_origins)} ({fire_origins_str})')
    print()

    results = []
    start_time = time.time()

    for trial_idx in range(num_trials):
        # Cycle through fire origins
        fire_origin = fire_origins[trial_idx % len(fire_origins)]
        seed = trial_idx

        # Suppress output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

        sim = Simulation(
            config=config,
            num_firefighters=num_firefighters,
            fire_origin=fire_origin,
            seed=seed
        )

        model = OptimalRescueModel(fire_priority_weight=0.0)

        initial_stats = sim.get_stats()
        total_occupants = initial_stats['remaining']

        completed = False
        final_tick = 0
        phase_switch_tick = None

        for tick in range(1000):
            state = sim.read()

            # Track phase switch
            if model.phase == 'optimal_rescue' and phase_switch_tick is None:
                phase_switch_tick = tick

            actions = model.get_actions(state)
            sim.update(actions)

            stats = sim.get_stats()
            if stats['remaining'] == 0:
                completed = True
                final_tick = tick
                break

        sys.stdout = old_stdout
        sys.stderr = old_stderr

        stats = sim.get_stats()

        # Determine stuck phase
        stuck_in = None
        if not completed:
            if model.phase == 'exploration':
                stuck_in = 'sweep'
            else:
                stuck_in = 'rescue'

        result = {
            'trial': trial_idx,
            'seed': seed,
            'fire_origin': fire_origin,
            'completed': completed,
            'ticks': final_tick if completed else 1000,
            'phase_switch_tick': phase_switch_tick,
            'rescued': stats['rescued'],
            'dead': stats['dead'],
            'total_occupants': total_occupants,
            'survival_rate': (stats['rescued'] / total_occupants * 100) if total_occupants > 0 else 0,
            'replans': model.replan_count,
            'stuck_in': stuck_in
        }
        results.append(result)

        # Progress update
        if (trial_idx + 1) % 10 == 0:
            completed_so_far = sum(1 for r in results if r['completed'])
            pct = completed_so_far * 100 // (trial_idx + 1)
            print(f'Progress: {trial_idx + 1}/{num_trials} trials | {completed_so_far} completed ({pct}%)')

    elapsed = time.time() - start_time

    # Calculate statistics
    valid_trials = [r for r in results if r['completed'] or r['ticks'] > 0]
    completed_trials = [r for r in results if r['completed']]

    print()
    print('='*80)
    print('BENCHMARK RESULTS')
    print('='*80)
    pct_complete = len(completed_trials) * 100 // len(valid_trials)
    print(f'Completed: {len(completed_trials)}/{len(valid_trials)} ({pct_complete}%)')
    print(f'Time elapsed: {elapsed:.1f}s')
    print()

    # Breakdown by stuck phase
    stuck_sweep = sum(1 for r in results if r['stuck_in'] == 'sweep')
    stuck_rescue = sum(1 for r in results if r['stuck_in'] == 'rescue')
    print(f'Stuck in sweep: {stuck_sweep}')
    print(f'Stuck in rescue: {stuck_rescue}')
    print()

    if completed_trials:
        avg_ticks = sum(r['ticks'] for r in completed_trials) / len(completed_trials)
        avg_survival = sum(r['survival_rate'] for r in completed_trials) / len(completed_trials)
        avg_replans = sum(r['replans'] for r in completed_trials) / len(completed_trials)

        print(f'Completed trials stats:')
        print(f'  Avg time: {avg_ticks:.1f} ticks')
        print(f'  Avg survival: {avg_survival:.1f}%')
        print(f'  Avg replans: {avg_replans:.1f}')
        print()

    # All trials stats
    avg_replans_all = sum(r['replans'] for r in results) / len(results)
    print(f'All trials:')
    print(f'  Avg replans: {avg_replans_all:.1f}')

    # Save results
    output_file = 'benchmark_sweep_2ff_trapped_100trials.json'
    with open(output_file, 'w') as f:
        json.dump({
            'trials': results,
            'config': {
                'num_trials': num_trials,
                'num_firefighters': num_firefighters,
                'fire_origins': fire_origins
            }
        }, f, indent=2)

    print(f'\nResults saved to: {output_file}')
    print('='*80)


if __name__ == '__main__':
    main()
