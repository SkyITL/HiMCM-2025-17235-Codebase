#!/usr/bin/env python3
"""
Fast benchmark for mall evacuation with random occupant generation.

This script:
- Uses occupancy ranges from JSON (realistic random generation)
- Runs 1000+ trials in ~10 seconds
- NO seeding by default (true randomness)
- Tests different fire origins and occupant distributions
"""

import json
import random
import argparse
import time
from typing import Dict, List
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


def run_single_trial(
    config: Dict,
    fire_origin: str,
    fire_priority_weight: float = 0.0,
    num_firefighters: int = 6,
    trial_seed: int = None
) -> Dict:
    """
    Run a single mall evacuation trial with random occupants.

    Args:
        config: Mall configuration (will be copied to avoid mutation)
        fire_origin: Room ID to start fire in
        fire_priority_weight: Fire proximity priority weight
        num_firefighters: Number of firefighters
        trial_seed: Random seed for THIS trial only (for reproducibility if needed)

    Returns:
        {
            'fire_origin': str,
            'total_occupants': int,
            'rescued': int,
            'dead': int,
            'survival_rate': float,
            'total_ticks': int,
            'replan_count': int
        }
    """
    # Set trial-specific seed if provided
    if trial_seed is not None:
        random.seed(trial_seed)
        sim_seed = trial_seed
    else:
        # Generate unique seed for this simulation using current time + random value
        sim_seed = int(time.time() * 1000000) % (2**31) + random.randint(0, 100000)

    # Create simulation (automatically generates random occupants from ranges)
    sim = Simulation(
        config=config,
        num_firefighters=num_firefighters,
        fire_origin=fire_origin,
        seed=sim_seed
    )

    # Get initial occupant count
    initial_stats = sim.get_stats()
    total_occupants = initial_stats['remaining']

    # Skip if no occupants (can happen with random generation)
    if total_occupants == 0:
        return {
            'fire_origin': fire_origin,
            'total_occupants': 0,
            'rescued': 0,
            'dead': 0,
            'survival_rate': 0.0,
            'total_ticks': 0,
            'replan_count': 0
        }

    # Create optimal rescue model
    model = OptimalRescueModel(fire_priority_weight=fire_priority_weight)

    # Track phase transition for filtering bugged trials
    phase_transitioned = False

    # Run simulation
    # Max ticks = 400 (~80 seconds real time with 0.2s per tick)
    # Any evacuation taking longer than this is considered failed
    tick = 0
    max_ticks = 400
    done = False
    last_rescue_tick = 0
    last_rescued_count = 0

    while not done and tick < max_ticks:
        state = sim.read()

        # Track if phase transition occurred
        if model.phase == 'optimal_rescue' and not phase_transitioned:
            phase_transitioned = True

        actions = model.get_actions(state)

        # Early termination: Check if firefighters can do anything
        has_meaningful_actions = any(len(ff_actions) > 0 for ff_actions in actions.values())
        stats = sim.get_stats()

        if not has_meaningful_actions and stats['remaining'] > 0:
            # No firefighters can reach anyone - remaining occupants are stranded
            # They will die from fire/smoke, so terminate early
            done = True
            break

        sim.update(actions)

        stats = sim.get_stats()

        # Track when last person was rescued
        if stats['rescued'] > last_rescued_count:
            last_rescue_tick = tick
            last_rescued_count = stats['rescued']

        done = stats['remaining'] == 0
        tick += 1

    # Get final statistics
    final_stats = sim.get_stats()

    # Survival rate = rescued / total_occupants
    survival_rate = 0.0
    if total_occupants > 0:
        survival_rate = (final_stats['rescued'] / total_occupants) * 100

    return {
        'fire_origin': fire_origin,
        'total_occupants': total_occupants,
        'rescued': final_stats['rescued'],
        'dead': final_stats['dead'],
        'survival_rate': survival_rate,
        'total_ticks': tick,
        'last_rescue_tick': last_rescue_tick,
        'replan_count': model.replan_count,
        'phase_transitioned': phase_transitioned  # Track if sweep->rescue happened
    }


def benchmark_mall_fast(
    num_trials: int = 20,
    fire_priority_weight: float = 0.0,
    num_firefighters: int = 2,
    random_seed: int = None,
    verbose: bool = False,
    use_fixed_seeds: bool = True  # Use same seeds across fire-weight tests
) -> Dict:
    """
    Run fast benchmark with random occupants and fire origins.

    Args:
        num_trials: Number of trials to run (default 20)
        fire_priority_weight: Fire proximity weight
        num_firefighters: Number of firefighters
        random_seed: ONLY use for debugging/comparison (not for final results!)
        verbose: Print progress
        use_fixed_seeds: If True, use deterministic seeds (1000, 1001, ...) for consistent
                        comparison across fire-weight values

    Returns:
        {
            'trials': List[Dict],
            'summary': {...},
            'config': {...}
        }
    """
    # Seed management for consistent cross-parameter comparison
    if use_fixed_seeds and random_seed is None:
        # Use deterministic seeds starting from 1000
        # This ensures trial 0 uses seed 1000, trial 1 uses seed 1001, etc.
        # So all fire-weight tests compare the same scenarios
        base_seed = 1000
        if verbose:
            print(f"Using fixed seeds for consistent comparison (base={base_seed})")
    elif random_seed is not None:
        print(f"WARNING: Using seed={random_seed}. Remove --seed for final results!")
        random.seed(random_seed)
        base_seed = None
    else:
        base_seed = None

    # Load mall config
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Get list of all rooms
    temp_sim = Simulation(config=config, num_firefighters=2, fire_origin='room_1')
    temp_state = temp_sim.read()
    rooms = [
        v_id for v_id, v_data in temp_state['graph']['vertices'].items()
        if v_data['type'] == 'room'
    ]

    if verbose:
        print(f"\n{'='*70}")
        print(f"FAST BENCHMARK: {num_trials} trials")
        print(f"Fire priority weight: {fire_priority_weight}")
        print(f"Firefighters: {num_firefighters}")
        print(f"Available rooms: {len(rooms)}")
        print(f"Random seed: {'NONE (true randomness)' if random_seed is None else random_seed}")
        print(f"{'='*70}")

    # Run trials
    start_time = time.time()
    results = []

    for i in range(num_trials):
        # Determine seed for this trial
        if base_seed is not None:
            trial_seed = base_seed + i
        else:
            trial_seed = None

        # Set seed for this trial (for fire origin selection)
        if trial_seed is not None:
            random.seed(trial_seed)

        # Random fire origin for each trial
        fire_origin = random.choice(rooms)

        if verbose and (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            print(f"Progress: {i+1}/{num_trials} trials ({rate:.1f} trials/sec)")

        result = run_single_trial(
            config=config,
            fire_origin=fire_origin,
            fire_priority_weight=fire_priority_weight,
            num_firefighters=num_firefighters,
            trial_seed=trial_seed  # Pass seed to ensure consistency
        )
        results.append(result)

    elapsed_time = time.time() - start_time

    # Filter out trials with 0 occupants AND trials that didn't transition phases (bugged)
    valid_results = [r for r in results
                     if r['total_occupants'] > 0 and r.get('phase_transitioned', False)]

    skipped_no_occupants = len([r for r in results if r['total_occupants'] == 0])
    skipped_no_transition = len([r for r in results
                                  if r['total_occupants'] > 0 and not r.get('phase_transitioned', False)])

    if not valid_results:
        print("ERROR: No valid trials")
        print(f"  Skipped {skipped_no_occupants} trials with 0 occupants")
        print(f"  Skipped {skipped_no_transition} trials without phase transition (bugged)")
        return None

    # Compute summary statistics
    survival_rates = [r['survival_rate'] for r in valid_results]
    avg_survival = sum(survival_rates) / len(survival_rates)
    std_survival = (sum((x - avg_survival)**2 for x in survival_rates) / len(survival_rates))**0.5

    avg_occupants = sum(r['total_occupants'] for r in valid_results) / len(valid_results)
    avg_rescued = sum(r['rescued'] for r in valid_results) / len(valid_results)
    avg_dead = sum(r['dead'] for r in valid_results) / len(valid_results)
    avg_ticks = sum(r['total_ticks'] for r in valid_results) / len(valid_results)
    avg_last_rescue = sum(r['last_rescue_tick'] for r in valid_results) / len(valid_results)
    avg_replans = sum(r['replan_count'] for r in valid_results) / len(valid_results)

    best_trial = max(valid_results, key=lambda r: r['survival_rate'])
    worst_trial = min(valid_results, key=lambda r: r['survival_rate'])

    summary = {
        'valid_trials': len(valid_results),
        'skipped_no_occupants': skipped_no_occupants,
        'skipped_no_transition': skipped_no_transition,
        'skipped_trials': len(results) - len(valid_results),
        'avg_survival_rate': avg_survival,
        'std_survival_rate': std_survival,
        'avg_occupants': avg_occupants,
        'avg_rescued': avg_rescued,
        'avg_dead': avg_dead,
        'avg_ticks': avg_ticks,
        'avg_last_rescue_tick': avg_last_rescue,
        'avg_replans': avg_replans,
        'best_trial': best_trial,
        'worst_trial': worst_trial,
        'elapsed_seconds': elapsed_time,
        'trials_per_second': num_trials / elapsed_time
    }

    if verbose:
        print(f"\n{'='*70}")
        print(f"SUMMARY STATISTICS ({elapsed_time:.1f}s, {summary['trials_per_second']:.1f} trials/sec)")
        print(f"{'='*70}")
        print(f"Valid trials: {len(valid_results)}/{num_trials}")
        if skipped_no_transition > 0:
            print(f"  Skipped {skipped_no_transition} trials without phase transition (bugged)")
        if skipped_no_occupants > 0:
            print(f"  Skipped {skipped_no_occupants} trials with 0 occupants")
        print(f"Average occupants per trial: {avg_occupants:.1f}")
        print(f"Average survival rate: {avg_survival:.1f}% ± {std_survival:.1f}%")
        print(f"Average rescued: {avg_rescued:.1f}")
        print(f"Average dead: {avg_dead:.1f}")
        print(f"Average ticks: {avg_ticks:.1f}")
        print(f"Average replans: {avg_replans:.2f}")
        print(f"\nBest trial: {best_trial['survival_rate']:.1f}% "
              f"({best_trial['rescued']}/{best_trial['total_occupants']} rescued, "
              f"fire: {best_trial['fire_origin']})")
        print(f"Worst trial: {worst_trial['survival_rate']:.1f}% "
              f"({worst_trial['rescued']}/{worst_trial['total_occupants']} rescued, "
              f"fire: {worst_trial['fire_origin']})")
        print(f"{'='*70}\n")

    return {
        'trials': results,
        'summary': summary,
        'config': {
            'num_trials': num_trials,
            'fire_priority_weight': fire_priority_weight,
            'num_firefighters': num_firefighters,
            'random_seed': random_seed
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description='Fast benchmark for mall with random occupants'
    )
    parser.add_argument(
        '--trials', type=int, default=20,
        help='Number of trials (default: 20)'
    )
    parser.add_argument(
        '--fire-weight', type=float, default=0.0,
        help='Fire proximity priority weight (default: 0.0)'
    )
    parser.add_argument(
        '--firefighters', type=int, default=2,
        help='Number of firefighters (default: 2)'
    )
    parser.add_argument(
        '--seed', type=int, default=None,
        help='Random seed (ONLY for debugging/comparison, NOT for final results!)'
    )
    parser.add_argument(
        '--no-fixed-seeds', action='store_true',
        help='Disable fixed seeds (use true randomness instead of deterministic seeds)'
    )
    parser.add_argument(
        '--quiet', action='store_true',
        help='Suppress progress output'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Save results to JSON file'
    )

    args = parser.parse_args()

    # Run benchmark
    results = benchmark_mall_fast(
        num_trials=args.trials,
        fire_priority_weight=args.fire_weight,
        num_firefighters=args.firefighters,
        random_seed=args.seed,
        verbose=not args.quiet,
        use_fixed_seeds=not args.no_fixed_seeds
    )

    if results is None:
        return

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()
