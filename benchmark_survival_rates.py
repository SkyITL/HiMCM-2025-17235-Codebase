#!/usr/bin/env python3
"""
Benchmark script to assess average survival rate across random fire origins.

Tests the optimal rescue system with different initial conditions:
- Random fire origins from all rooms
- Multiple trials per configuration
- Statistics on survival rates, rescue times, replanning frequency

Usage:
    python3 benchmark_survival_rates.py --trials 10 --fire-weight 0.5
"""

import argparse
import random
import json
from typing import Dict, List
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


def run_single_trial(
    fire_origin: str,
    num_firefighters: int = 2,
    fire_priority_weight: float = 0.0,
    verbose: bool = False
) -> Dict:
    """
    Run a single simulation trial.

    Args:
        fire_origin: Room ID to start fire in
        num_firefighters: Number of firefighters
        fire_priority_weight: Fire proximity weight (0.0 = disabled)
        verbose: Print detailed progress

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
    # Load config
    with open('config_example.json', 'r') as f:
        config = json.load(f)

    # Create simulator
    sim = Simulation(
        config=config,
        num_firefighters=num_firefighters,
        fire_origin=fire_origin
    )

    # Modify occupants to all be incapable and pre-discover all rooms
    state = sim.read()
    state['discovered_occupants'] = {}
    total_incapable = 0

    for room_id, room_data in state['graph']['vertices'].items():
        if room_data['type'] == 'room':
            # Set all to incapable (3 per room for consistency)
            count = 3
            room_data['occupants'] = {
                'total': count,
                'capable': 0,
                'incapable': count
            }
            # Pre-discover
            state['discovered_occupants'][room_id] = {
                'total': count,
                'capable': 0,
                'incapable': count
            }
            total_incapable += count

    # Create model with fire weighting
    model = OptimalRescueModel(
        fire_priority_weight=fire_priority_weight
    )

    # Force immediate phase transition
    model.phase = 'optimal_rescue'

    if verbose:
        print(f"\n{'='*70}")
        print(f"Fire origin: {fire_origin}")
        print(f"Total incapable: {total_incapable}")
        print(f"Fire priority weight: {fire_priority_weight}")
        print(f"{'='*70}")

    # Run simulation
    tick = 0
    max_ticks = 1000  # Safety limit
    done = False

    while not done and tick < max_ticks:
        state = sim.read()
        actions = model.get_actions(state)
        sim.update(actions)

        # Check if simulation is complete (compute stats from graph)
        state = sim.read()
        remaining = sum(
            v_data.get('occupants', {}).get('incapable', 0)
            for v_data in state['graph']['vertices'].values()
            if v_data['type'] == 'room'
        )
        done = remaining == 0
        tick += 1

        if verbose and tick % 50 == 0:
            rescued = sum(
                ff_data.get('total_rescued', 0)
                for ff_data in state['firefighters'].values()
            )
            print(f"Tick {tick}: {rescued} rescued, {remaining} remaining")

    # Get final statistics
    final_state = sim.read()

    # Compute stats from final state
    total_rescued = sum(
        ff_data.get('total_rescued', 0)
        for ff_data in final_state['firefighters'].values()
    )
    remaining = sum(
        v_data.get('occupants', {}).get('incapable', 0)
        for v_data in final_state['graph']['vertices'].values()
        if v_data['type'] == 'room'
    )
    total_dead = total_incapable - total_rescued - remaining

    survival_rate = (total_rescued / total_incapable * 100) if total_incapable > 0 else 0.0

    result = {
        'fire_origin': fire_origin,
        'rescued': total_rescued,
        'dead': total_dead,
        'remaining': remaining,
        'survival_rate': survival_rate,
        'total_ticks': tick,
        'time_minutes': tick * 1.0 / 60.0,  # Assume 1 second per tick
        'replan_count': model.replan_count
    }

    if verbose:
        print(f"\nFinal: {result['rescued']}/{total_incapable} rescued "
              f"({survival_rate:.1f}% survival) in {tick} ticks "
              f"({result['replan_count']} replans)")

    return result


def benchmark(
    num_trials: int = 10,
    fire_priority_weight: float = 0.0,
    random_seed: int = None,
    verbose: bool = True
) -> Dict:
    """
    Run multiple trials with random fire origins.

    Args:
        num_trials: Number of trials to run
        fire_priority_weight: Fire proximity weight
        random_seed: Random seed for reproducibility
        verbose: Print progress

    Returns:
        {
            'trials': List[Dict],  # Individual trial results
            'summary': {
                'avg_survival_rate': float,
                'std_survival_rate': float,
                'avg_time_minutes': float,
                'avg_replan_count': float,
                'best_trial': Dict,
                'worst_trial': Dict
            }
        }
    """
    if random_seed is not None:
        random.seed(random_seed)

    # Load config to get list of rooms
    with open('config_example.json', 'r') as f:
        config = json.load(f)

    # Create temporary sim just to get room list
    temp_sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin='room_1'  # Dummy value
    )
    temp_state = temp_sim.read()
    rooms = [
        v_id for v_id, v_data in temp_state['graph']['vertices'].items()
        if v_data['type'] == 'room'
    ]

    if verbose:
        print(f"\n{'='*70}")
        print(f"BENCHMARK: {num_trials} trials with random fire origins")
        print(f"Fire priority weight: {fire_priority_weight}")
        print(f"Available rooms: {len(rooms)}")
        print(f"{'='*70}")

    # Run trials
    results = []
    for i in range(num_trials):
        fire_origin = random.choice(rooms)

        if verbose:
            print(f"\nTrial {i+1}/{num_trials}: Fire in {fire_origin}")

        result = run_single_trial(
            fire_origin=fire_origin,
            fire_priority_weight=fire_priority_weight,
            verbose=verbose
        )
        results.append(result)

    # Compute summary statistics
    survival_rates = [r['survival_rate'] for r in results]
    avg_survival = sum(survival_rates) / len(survival_rates)
    std_survival = (sum((x - avg_survival)**2 for x in survival_rates) / len(survival_rates))**0.5

    avg_time = sum(r['time_minutes'] for r in results) / len(results)
    avg_replans = sum(r['replan_count'] for r in results) / len(results)

    best_trial = max(results, key=lambda r: r['survival_rate'])
    worst_trial = min(results, key=lambda r: r['survival_rate'])

    summary = {
        'avg_survival_rate': avg_survival,
        'std_survival_rate': std_survival,
        'avg_time_minutes': avg_time,
        'avg_replan_count': avg_replans,
        'best_trial': best_trial,
        'worst_trial': worst_trial
    }

    if verbose:
        print(f"\n{'='*70}")
        print(f"SUMMARY STATISTICS")
        print(f"{'='*70}")
        print(f"Average survival rate: {avg_survival:.1f}% ± {std_survival:.1f}%")
        print(f"Average time: {avg_time:.2f} minutes")
        print(f"Average replans: {avg_replans:.1f}")
        print(f"\nBest trial: {best_trial['survival_rate']:.1f}% (fire: {best_trial['fire_origin']})")
        print(f"Worst trial: {worst_trial['survival_rate']:.1f}% (fire: {worst_trial['fire_origin']})")
        print(f"{'='*70}\n")

    return {
        'trials': results,
        'summary': summary
    }


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark survival rates across random fire origins'
    )
    parser.add_argument(
        '--trials', type=int, default=10,
        help='Number of trials to run (default: 10)'
    )
    parser.add_argument(
        '--fire-weight', type=float, default=0.0,
        help='Fire proximity priority weight (default: 0.0 = disabled)'
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
    results = benchmark(
        num_trials=args.trials,
        fire_priority_weight=args.fire_weight,
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
