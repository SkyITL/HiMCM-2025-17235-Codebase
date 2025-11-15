#!/usr/bin/env python3
"""
Benchmark the K-medoids + MST sweep strategy.

Runs multiple trials and collects statistics on:
- Survival rate
- Time to complete sweep phase
- Time to complete full evacuation
- Rooms discovered per tick
- Instruction coverage
- Total rescues vs deaths
"""

import json
import time
from typing import Dict, List
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


def run_single_trial(
    config: Dict,
    num_firefighters: int,
    fire_origin: str,
    seed: int
) -> Dict:
    """
    Run a single trial and collect statistics.

    Args:
        config: Building configuration
        num_firefighters: Number of firefighters
        fire_origin: Starting fire location
        seed: Random seed

    Returns:
        Trial statistics dictionary
    """
    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=num_firefighters,
        fire_origin=fire_origin,
        seed=seed
    )

    # Get initial state
    initial_state = sim.read()
    initial_stats = sim.get_stats()

    total_occupants = initial_stats['remaining']
    total_rooms = sum(
        1 for v in initial_state['graph']['vertices'].values()
        if v['type'] == 'room'
    )

    # Create model with sweep coordinator (quiet mode)
    import sys
    import os
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    model = OptimalRescueModel(fire_priority_weight=0.0)

    sys.stdout = old_stdout
    sys.stderr = old_stderr

    # Track metrics
    sweep_ticks = 0
    total_ticks = 0
    max_ticks = 1000
    sweep_complete_tick = None
    phase_switch_tick = None
    rooms_discovered_over_time = []
    capable_instructed_over_time = []
    sweep_replan_count = 0
    rescue_replan_count = 0

    # Run simulation (suppress verbose output)
    while sim.get_stats()['remaining'] > 0 and total_ticks < max_ticks:
        state = sim.read()

        # Track current phase
        current_phase = model.phase

        # Get actions (suppress output)
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        actions = model.get_actions(state)
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        # Count replanning events
        if current_phase == 'exploration':
            # Track sweep replanning
            if model.sweep_coordinator and hasattr(model.sweep_coordinator, 'replan_count'):
                sweep_replan_count = model.sweep_coordinator.replan_count
        else:
            # Track rescue replanning
            if hasattr(model, 'last_replan_tick'):
                if model.last_replan_tick == total_ticks:
                    rescue_replan_count += 1

        # Track rooms discovered (from sweep coordinator's globally_visited)
        if model.sweep_coordinator and model.sweep_initialized:
            rooms_discovered = len(model.sweep_coordinator.globally_visited)
            rooms_discovered_over_time.append(rooms_discovered)

            # Track capable occupants instructed
            discovered = state.get('discovered_occupants', {})
            total_capable = sum(occ.get('capable', 0) for occ in discovered.values())
            capable_instructed_over_time.append(total_capable)

            # Check if sweep just completed
            if current_phase == 'exploration' and sweep_complete_tick is None:
                if model.sweep_coordinator.is_sweep_complete(state):
                    sweep_complete_tick = total_ticks

        # Check if phase switched
        if current_phase == 'optimal_rescue' and phase_switch_tick is None:
            phase_switch_tick = total_ticks
            sweep_ticks = total_ticks

        # Update simulation
        sim.update(actions)
        total_ticks += 1

    # Final statistics
    final_stats = sim.get_stats()

    # If phase never switched, sweep took all ticks
    if sweep_ticks == 0:
        sweep_ticks = total_ticks

    if sweep_complete_tick is None:
        sweep_complete_tick = sweep_ticks

    if phase_switch_tick is None:
        phase_switch_tick = sweep_ticks

    # Calculate sweep efficiency metrics
    if total_rooms > 0 and len(rooms_discovered_over_time) > 0:
        # Find tick when all rooms discovered
        all_rooms_discovered_tick = None
        for tick, count in enumerate(rooms_discovered_over_time):
            if count >= total_rooms:
                all_rooms_discovered_tick = tick
                break

        rooms_per_tick = total_rooms / sweep_complete_tick if sweep_complete_tick > 0 else 0
    else:
        all_rooms_discovered_tick = sweep_complete_tick
        rooms_per_tick = 0

    # Calculate instruction efficiency
    initial_capable = sum(
        occ.get('capable', 0)
        for occ in initial_state.get('discovered_occupants', {}).values()
    )

    return {
        'fire_origin': fire_origin,
        'seed': seed,
        'total_occupants': total_occupants,
        'total_rooms': total_rooms,
        'rescued': final_stats['rescued'],
        'dead': final_stats['dead'],
        'remaining': final_stats['remaining'],
        'survival_rate': (final_stats['rescued'] / total_occupants * 100) if total_occupants > 0 else 0,
        'sweep_ticks': sweep_ticks,
        'sweep_complete_tick': sweep_complete_tick,
        'phase_switch_tick': phase_switch_tick,
        'total_ticks': total_ticks,
        'all_rooms_discovered_tick': all_rooms_discovered_tick,
        'rooms_per_tick': rooms_per_tick,
        'sweep_replan_count': sweep_replan_count,
        'rescue_replan_count': rescue_replan_count,
        'total_replan_count': sweep_replan_count + rescue_replan_count,
        'completed': final_stats['remaining'] == 0
    }


def run_benchmark(
    config_file: str,
    num_trials: int = 100,
    num_firefighters: int = 6,
    fire_origins: List[str] = None,
    output_file: str = 'benchmark_sweep_results.json'
):
    """
    Run benchmark with multiple trials.

    Args:
        config_file: Path to building configuration
        num_trials: Number of trials to run
        num_firefighters: Number of firefighters
        fire_origins: List of fire origin rooms (cycles through them)
        output_file: Output JSON file
    """
    print("=" * 70)
    print("K-MEDOIDS + MST SWEEP STRATEGY BENCHMARK")
    print("=" * 70)

    # Load configuration
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Default fire origins if not specified
    if fire_origins is None:
        # Use first few rooms from config
        all_rooms = [
            v_id for v_id, v_data in config['graph']['vertices'].items()
            if v_data['type'] == 'room'
        ]
        fire_origins = all_rooms[:5] if len(all_rooms) >= 5 else all_rooms

    print(f"\nConfiguration:")
    print(f"  Building: {config_file}")
    print(f"  Trials: {num_trials}")
    print(f"  Firefighters: {num_firefighters}")
    print(f"  Fire origins: {len(fire_origins)} ({', '.join(fire_origins)})")
    print(f"  Output: {output_file}")

    # Run trials
    trials = []
    start_time = time.time()

    print(f"\nRunning trials...")

    for trial_num in range(num_trials):
        # Cycle through fire origins
        fire_origin = fire_origins[trial_num % len(fire_origins)]

        # Use different seed for each trial
        seed = 42 + trial_num

        try:
            result = run_single_trial(
                config=config,
                num_firefighters=num_firefighters,
                fire_origin=fire_origin,
                seed=seed
            )

            trials.append(result)

            # Print progress every 10 trials
            if (trial_num + 1) % 10 == 0:
                avg_survival = sum(t['survival_rate'] for t in trials) / len(trials)
                avg_sweep_ticks = sum(t['sweep_ticks'] for t in trials) / len(trials)
                print(f"  Trial {trial_num + 1}/{num_trials}: "
                      f"Avg survival={avg_survival:.1f}%, "
                      f"Avg sweep time={avg_sweep_ticks:.1f} ticks")

        except Exception as e:
            print(f"  Trial {trial_num + 1} failed: {e}")
            continue

    elapsed_time = time.time() - start_time

    # Calculate summary statistics
    if not trials:
        print("\nNo successful trials!")
        return

    valid_trials = [t for t in trials if t['completed']]

    summary = {
        'total_trials': num_trials,
        'valid_trials': len(valid_trials),
        'failed_trials': num_trials - len(valid_trials),
        'avg_survival_rate': sum(t['survival_rate'] for t in valid_trials) / len(valid_trials),
        'std_survival_rate': _std_dev([t['survival_rate'] for t in valid_trials]),
        'avg_occupants': sum(t['total_occupants'] for t in valid_trials) / len(valid_trials),
        'avg_rescued': sum(t['rescued'] for t in valid_trials) / len(valid_trials),
        'avg_dead': sum(t['dead'] for t in valid_trials) / len(valid_trials),
        'avg_sweep_ticks': sum(t['sweep_ticks'] for t in valid_trials) / len(valid_trials),
        'avg_total_ticks': sum(t['total_ticks'] for t in valid_trials) / len(valid_trials),
        'avg_rooms_per_tick': sum(t['rooms_per_tick'] for t in valid_trials) / len(valid_trials),
        'avg_sweep_replans': sum(t['sweep_replan_count'] for t in valid_trials) / len(valid_trials),
        'avg_rescue_replans': sum(t['rescue_replan_count'] for t in valid_trials) / len(valid_trials),
        'avg_total_replans': sum(t['total_replan_count'] for t in valid_trials) / len(valid_trials),
        'best_trial': max(valid_trials, key=lambda t: t['survival_rate']),
        'worst_trial': min(valid_trials, key=lambda t: t['survival_rate']),
        'fastest_sweep': min(valid_trials, key=lambda t: t['sweep_ticks']),
        'slowest_sweep': max(valid_trials, key=lambda t: t['sweep_ticks']),
        'elapsed_seconds': elapsed_time,
        'trials_per_second': len(trials) / elapsed_time
    }

    # Save results
    results = {
        'trials': trials,
        'summary': summary,
        'config': {
            'num_trials': num_trials,
            'num_firefighters': num_firefighters,
            'fire_origins': fire_origins,
            'config_file': config_file
        }
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)
    print(f"Valid trials: {summary['valid_trials']}/{num_trials}")
    print(f"Failed trials: {summary['failed_trials']}")
    print(f"\nSurvival Rate:")
    print(f"  Average: {summary['avg_survival_rate']:.2f}%")
    print(f"  Std Dev: {summary['std_survival_rate']:.2f}%")
    print(f"\nTiming:")
    print(f"  Avg sweep time: {summary['avg_sweep_ticks']:.1f} ticks")
    print(f"  Avg total time: {summary['avg_total_ticks']:.1f} ticks")
    print(f"  Avg rooms/tick: {summary['avg_rooms_per_tick']:.2f}")
    print(f"\nOccupants:")
    print(f"  Avg rescued: {summary['avg_rescued']:.1f}/{summary['avg_occupants']:.1f}")
    print(f"  Avg dead: {summary['avg_dead']:.1f}")
    print(f"\nReplanning:")
    print(f"  Avg sweep replans: {summary['avg_sweep_replans']:.2f}")
    print(f"  Avg rescue replans: {summary['avg_rescue_replans']:.2f}")
    print(f"  Avg total replans: {summary['avg_total_replans']:.2f}")
    print(f"\nBest Trial:")
    print(f"  Fire origin: {summary['best_trial']['fire_origin']}")
    print(f"  Survival: {summary['best_trial']['survival_rate']:.1f}%")
    print(f"  Sweep time: {summary['best_trial']['sweep_ticks']} ticks")
    print(f"\nWorst Trial:")
    print(f"  Fire origin: {summary['worst_trial']['fire_origin']}")
    print(f"  Survival: {summary['worst_trial']['survival_rate']:.1f}%")
    print(f"  Sweep time: {summary['worst_trial']['sweep_ticks']} ticks")
    print(f"\nFastest Sweep:")
    print(f"  Fire origin: {summary['fastest_sweep']['fire_origin']}")
    print(f"  Time: {summary['fastest_sweep']['sweep_ticks']} ticks")
    print(f"\nSlowest Sweep:")
    print(f"  Fire origin: {summary['slowest_sweep']['fire_origin']}")
    print(f"  Time: {summary['slowest_sweep']['sweep_ticks']} ticks")
    print(f"\nBenchmark Performance:")
    print(f"  Elapsed time: {elapsed_time:.2f}s")
    print(f"  Trials/second: {summary['trials_per_second']:.2f}")
    print(f"\nResults saved to: {output_file}")
    print("=" * 70)


def _std_dev(values: List[float]) -> float:
    """Calculate standard deviation."""
    if len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


def main():
    """Run benchmark on mall configuration."""
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'

    # Run benchmark with 20 trials for quick testing
    run_benchmark(
        config_file=config_file,
        num_trials=20,
        num_firefighters=6,
        fire_origins=['room_1', 'room_2', 'room_7', 'room_10', 'room_15'],
        output_file='benchmark_sweep_with_replan.json'
    )


if __name__ == '__main__':
    main()
