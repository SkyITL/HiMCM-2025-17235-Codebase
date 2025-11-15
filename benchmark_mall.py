#!/usr/bin/env python3
"""
Benchmark optimal rescue system on mall configuration.

Tests multiple random fire origins and fire priority weights.
"""

import json
import random
import argparse
from typing import Dict
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


def run_mall_trial(
    fire_origin: str,
    fire_priority_weight: float = 0.0,
    num_firefighters: int = 6,
    verbose: bool = False
) -> Dict:
    """
    Run a single mall evacuation trial.

    Args:
        fire_origin: Room ID to start fire in
        fire_priority_weight: Fire proximity priority weight (0.0 = disabled)
        num_firefighters: Number of firefighters
        verbose: Print progress

    Returns:
        {
            'fire_origin': str,
            'rescued': int,
            'dead': int,
            'remaining': int,
            'survival_rate': float,
            'total_ticks': int,
            'time_minutes': float,
            'replan_count': int
        }
    """
    # Load mall configuration
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    if verbose:
        print(f"\n{'='*70}")
        print(f"Fire origin: {fire_origin}")
        print(f"Firefighters: {num_firefighters}")
        print(f"Fire priority weight: {fire_priority_weight}")
        print(f"{'='*70}")

    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=num_firefighters,
        fire_origin=fire_origin,
        seed=42
    )

    # Get initial occupant count
    initial_stats = sim.get_stats()
    total_occupants = initial_stats['remaining']

    if verbose:
        print(f"Total occupants: {total_occupants}")

    # Create optimal rescue model
    model = OptimalRescueModel(
        fire_priority_weight=fire_priority_weight
    )

    # Run simulation
    tick = 0
    max_ticks = 2000  # Safety limit
    done = False

    while not done and tick < max_ticks:
        state = sim.read()
        actions = model.get_actions(state)
        sim.update(actions)

        # Check if done
        stats = sim.get_stats()
        done = stats['remaining'] == 0
        tick += 1

        if verbose and tick % 100 == 0:
            print(f"Tick {tick}: {stats['rescued']} rescued, "
                  f"{stats['dead']} dead, "
                  f"{stats['remaining']} remaining")

    # Get final statistics
    final_stats = sim.get_stats()

    survival_rate = 0.0
    if final_stats['rescued'] + final_stats['dead'] > 0:
        survival_rate = (final_stats['rescued'] /
                        (final_stats['rescued'] + final_stats['dead']) * 100)

    result = {
        'fire_origin': fire_origin,
        'rescued': final_stats['rescued'],
        'dead': final_stats['dead'],
        'remaining': final_stats['remaining'],
        'survival_rate': survival_rate,
        'total_ticks': tick,
        'time_minutes': final_stats['time_minutes'],
        'replan_count': model.replan_count
    }

    if verbose:
        print(f"\nFinal: {result['rescued']}/{total_occupants} rescued "
              f"({survival_rate:.1f}% survival) in {tick} ticks "
              f"({result['replan_count']} replans)")

    return result


def benchmark_mall(
    num_trials: int = 5,
    fire_priority_weight: float = 0.0,
    num_firefighters: int = 6,
    random_seed: int = None,
    verbose: bool = True
) -> Dict:
    """
    Run multiple trials with random fire origins on mall.

    Args:
        num_trials: Number of trials to run
        fire_priority_weight: Fire proximity weight
        num_firefighters: Number of firefighters
        random_seed: Random seed for reproducibility
        verbose: Print progress

    Returns:
        {
            'trials': List[Dict],
            'summary': {...}
        }
    """
    if random_seed is not None:
        random.seed(random_seed)

    # Load mall config to get room list
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Get all rooms
    temp_sim = Simulation(
        config=config,
        num_firefighters=num_firefighters,
        fire_origin='room_1',  # Dummy
        seed=42
    )
    temp_state = temp_sim.read()
    rooms = [
        v_id for v_id, v_data in temp_state['graph']['vertices'].items()
        if v_data['type'] == 'room'
    ]

    if verbose:
        print(f"\n{'='*70}")
        print(f"MALL BENCHMARK: {num_trials} trials")
        print(f"Fire priority weight: {fire_priority_weight}")
        print(f"Firefighters: {num_firefighters}")
        print(f"Available rooms: {len(rooms)}")
        print(f"{'='*70}")

    # Run trials
    results = []
    for i in range(num_trials):
        fire_origin = random.choice(rooms)

        if verbose:
            print(f"\n{'='*70}")
            print(f"Trial {i+1}/{num_trials}: Fire in {fire_origin}")
            print(f"{'='*70}")

        result = run_mall_trial(
            fire_origin=fire_origin,
            fire_priority_weight=fire_priority_weight,
            num_firefighters=num_firefighters,
            verbose=verbose
        )
        results.append(result)

    # Compute summary statistics
    survival_rates = [r['survival_rate'] for r in results]
    avg_survival = sum(survival_rates) / len(survival_rates)
    std_survival = (sum((x - avg_survival)**2 for x in survival_rates) / len(survival_rates))**0.5

    avg_time = sum(r['time_minutes'] for r in results) / len(results)
    avg_replans = sum(r['replan_count'] for r in results) / len(results)
    avg_rescued = sum(r['rescued'] for r in results) / len(results)
    avg_dead = sum(r['dead'] for r in results) / len(results)

    best_trial = max(results, key=lambda r: r['survival_rate'])
    worst_trial = min(results, key=lambda r: r['survival_rate'])

    summary = {
        'avg_survival_rate': avg_survival,
        'std_survival_rate': std_survival,
        'avg_time_minutes': avg_time,
        'avg_replan_count': avg_replans,
        'avg_rescued': avg_rescued,
        'avg_dead': avg_dead,
        'best_trial': best_trial,
        'worst_trial': worst_trial
    }

    if verbose:
        print(f"\n{'='*70}")
        print(f"SUMMARY STATISTICS")
        print(f"{'='*70}")
        print(f"Average survival rate: {avg_survival:.1f}% ± {std_survival:.1f}%")
        print(f"Average rescued: {avg_rescued:.1f}")
        print(f"Average dead: {avg_dead:.1f}")
        print(f"Average time: {avg_time:.2f} minutes")
        print(f"Average replans: {avg_replans:.1f}")
        print(f"\nBest trial: {best_trial['survival_rate']:.1f}% (fire: {best_trial['fire_origin']})")
        print(f"Worst trial: {worst_trial['survival_rate']:.1f}% (fire: {worst_trial['fire_origin']})")
        print(f"{'='*70}\n")

    return {
        'trials': results,
        'summary': summary,
        'config': {
            'num_trials': num_trials,
            'fire_priority_weight': fire_priority_weight,
            'num_firefighters': num_firefighters
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark optimal rescue on mall configuration'
    )
    parser.add_argument(
        '--trials', type=int, default=5,
        help='Number of trials to run (default: 5)'
    )
    parser.add_argument(
        '--fire-weight', type=float, default=0.0,
        help='Fire proximity priority weight (default: 0.0 = disabled)'
    )
    parser.add_argument(
        '--firefighters', type=int, default=6,
        help='Number of firefighters (default: 6)'
    )
    parser.add_argument(
        '--seed', type=int, default=None,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--quiet', action='store_true',
        help='Suppress detailed output'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Save results to JSON file'
    )

    args = parser.parse_args()

    # Run benchmark
    results = benchmark_mall(
        num_trials=args.trials,
        fire_priority_weight=args.fire_weight,
        num_firefighters=args.firefighters,
        random_seed=args.seed,
        verbose=not args.quiet
    )

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == '__main__':
    main()
