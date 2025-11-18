#!/usr/bin/env python3
"""
Debug stuck trials by tracking firefighter positions and actions in detail.

This script runs specific problematic seeds and logs:
- Firefighter positions over time
- Actions taken each tick
- Rooms visited progress
- Graph connectivity changes
- Stall detection triggers
"""

import json
import sys
from typing import Dict, List
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


def debug_single_trial(
    config: Dict,
    num_firefighters: int,
    fire_origin: str,
    seed: int,
    max_ticks: int = 200
) -> Dict:
    """
    Run a single trial with detailed debugging output.

    Args:
        config: Building configuration
        num_firefighters: Number of firefighters
        fire_origin: Starting fire location
        seed: Random seed
        max_ticks: Maximum ticks to run

    Returns:
        Debug information dictionary
    """
    print("=" * 80)
    print(f"DEBUGGING TRIAL: seed={seed}, fire_origin={fire_origin}")
    print("=" * 80)

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
    all_rooms = {
        v_id for v_id, v_data in initial_state['graph']['vertices'].items()
        if v_data['type'] == 'room'
    }
    total_rooms = len(all_rooms)

    print(f"\nInitial State:")
    print(f"  Total occupants: {total_occupants}")
    print(f"  Total rooms: {total_rooms}")
    print(f"  Firefighters: {num_firefighters}")

    # Create model (suppress initialization output)
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = open('/dev/null', 'w')
    sys.stderr = open('/dev/null', 'w')

    model = OptimalRescueModel(fire_priority_weight=0.0)

    sys.stdout = old_stdout
    sys.stderr = old_stderr

    # Track detailed metrics
    tick = 0
    position_history = {ff_id: [] for ff_id in initial_state['firefighters'].keys()}
    action_history = {ff_id: [] for ff_id in initial_state['firefighters'].keys()}
    visited_over_time = []
    phase_history = []

    # Track position stability (detect trapped firefighters)
    position_stability = {ff_id: {'position': None, 'ticks_stationary': 0}
                         for ff_id in initial_state['firefighters'].keys()}

    print(f"\n{'Tick':>4} | {'Phase':^12} | {'Visited':>7} | {'FF Positions':^50} | {'Actions':^40}")
    print("-" * 130)

    while sim.get_stats()['remaining'] > 0 and tick < max_ticks:
        state = sim.read()
        current_phase = model.phase

        # Get actions
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')
        actions = model.get_actions(state)
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        # Track firefighter positions
        ff_positions = {}
        for ff_id, ff_data in state['firefighters'].items():
            ff_pos = ff_data['position']
            ff_positions[ff_id] = ff_pos
            position_history[ff_id].append(ff_pos)

            # Track position stability
            if position_stability[ff_id]['position'] == ff_pos:
                position_stability[ff_id]['ticks_stationary'] += 1
            else:
                position_stability[ff_id]['position'] = ff_pos
                position_stability[ff_id]['ticks_stationary'] = 0

        # Track actions
        for ff_id, ff_actions in actions.items():
            action_history[ff_id].append(ff_actions)

        # Track visited rooms
        if model.sweep_coordinator and model.sweep_initialized:
            visited_count = len(model.sweep_coordinator.globally_visited)
            visited_over_time.append(visited_count)
        else:
            visited_over_time.append(0)

        phase_history.append(current_phase)

        # Format output for this tick
        visited_str = f"{visited_over_time[-1]}/{total_rooms}" if visited_over_time else "0/0"

        # Show positions
        pos_str = ", ".join([f"{ff_id[-2:]}: {pos[-8:]}" for ff_id, pos in list(ff_positions.items())[:3]])

        # Show actions (abbreviated)
        action_types = []
        for ff_id, ff_actions in actions.items():
            if ff_actions:
                types = [a.get('type', '?')[0].upper() for a in ff_actions[:2]]
                action_types.append(f"{ff_id[-2:]}:{''.join(types)}")
        action_str = ", ".join(action_types[:3])

        # Print every 10 ticks or when interesting events happen
        if tick % 10 == 0 or tick < 20 or current_phase != phase_history[-2] if len(phase_history) > 1 else False:
            print(f"{tick:4d} | {current_phase:^12} | {visited_str:>7} | {pos_str:^50} | {action_str:^40}")

        # Check for stationary firefighters
        for ff_id, stability in position_stability.items():
            if stability['ticks_stationary'] >= 10:
                print(f"\n⚠️  WARNING: {ff_id} has been stationary at {stability['position']} for {stability['ticks_stationary']} ticks")

                # Check if trapped
                ff_pos = stability['position']
                graph = state['graph']
                edges = graph['edges']

                # Count available edges
                available_edges = 0
                for edge_id, edge_data in edges.items():
                    if edge_data.get('is_burned'):
                        continue
                    if edge_data['vertex_a'] == ff_pos or edge_data['vertex_b'] == ff_pos:
                        available_edges += 1

                if available_edges == 0:
                    print(f"   🚨 {ff_id} IS TRAPPED - no available edges from {ff_pos}")
                else:
                    print(f"   {ff_id} has {available_edges} available edges but is not moving")
                    # Show what actions they're taking
                    recent_actions = action_history[ff_id][-5:] if len(action_history[ff_id]) >= 5 else action_history[ff_id]
                    print(f"   Recent actions: {recent_actions}")

        # Update simulation
        sim.update(actions)
        tick += 1

        # Early exit if phase switched to rescue
        if current_phase == 'optimal_rescue' and tick > 50:
            print(f"\n✓ Phase switched to rescue at tick {tick}")
            break

    # Final analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    final_stats = sim.get_stats()
    final_visited = visited_over_time[-1] if visited_over_time else 0

    print(f"\nFinal State (tick {tick}):")
    print(f"  Phase: {phase_history[-1] if phase_history else 'unknown'}")
    print(f"  Rooms visited: {final_visited}/{total_rooms} ({final_visited/total_rooms*100:.1f}%)")
    print(f"  Occupants remaining: {final_stats['remaining']}")
    print(f"  Rescued: {final_stats['rescued']}")
    print(f"  Dead: {final_stats['dead']}")

    # Analyze firefighter movement patterns
    print(f"\nFirefighter Movement Analysis:")
    for ff_id in position_history.keys():
        positions = position_history[ff_id]
        unique_positions = len(set(positions))
        total_positions = len(positions)

        # Calculate movement rate
        movement_rate = unique_positions / total_positions * 100 if total_positions > 0 else 0

        print(f"  {ff_id}:")
        print(f"    Unique positions: {unique_positions}/{total_positions} ({movement_rate:.1f}% movement rate)")

        # Check for loops (visiting same position multiple times)
        if total_positions > 0:
            from collections import Counter
            position_counts = Counter(positions)
            most_common = position_counts.most_common(3)
            print(f"    Most visited: {most_common[0][0][-8:]} ({most_common[0][1]}x)")

            # Check if stuck in loop
            if most_common[0][1] > 10:
                print(f"    ⚠️  Possible loop detected - same position visited {most_common[0][1]} times")

    # Analyze visited rooms progress
    if visited_over_time:
        print(f"\nRoom Discovery Progress:")

        # Calculate discovery rate
        discovery_milestones = []
        for target in [0.25, 0.5, 0.75, 1.0]:
            target_count = int(total_rooms * target)
            for t, count in enumerate(visited_over_time):
                if count >= target_count:
                    discovery_milestones.append((target, t))
                    break

        for target, t in discovery_milestones:
            print(f"  {target*100:.0f}% rooms discovered at tick {t}")

        # Check for stalls
        stall_periods = []
        last_count = 0
        stall_start = 0
        for t, count in enumerate(visited_over_time):
            if count == last_count:
                if stall_start == 0:
                    stall_start = t
            else:
                if stall_start > 0 and t - stall_start >= 10:
                    stall_periods.append((stall_start, t, last_count))
                stall_start = 0
                last_count = count

        if stall_periods:
            print(f"\n  Stall periods (no discovery for 10+ ticks):")
            for start, end, count in stall_periods:
                print(f"    Ticks {start}-{end} ({end-start} ticks) - stuck at {count} rooms")

        # Calculate overall discovery rate
        if tick > 0:
            rate = final_visited / tick
            print(f"\n  Average discovery rate: {rate:.2f} rooms/tick")

    return {
        'seed': seed,
        'fire_origin': fire_origin,
        'total_ticks': tick,
        'final_phase': phase_history[-1] if phase_history else 'unknown',
        'rooms_visited': final_visited,
        'total_rooms': total_rooms,
        'completion_rate': final_visited / total_rooms if total_rooms > 0 else 0,
        'position_history': position_history,
        'action_history': action_history,
        'visited_over_time': visited_over_time,
        'phase_history': phase_history
    }


def main():
    """Debug problematic seeds from benchmark."""
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'

    # Load configuration
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Problem seeds identified from benchmark
    problem_seeds = [
        (50, 'room_10'),   # Stuck in sweep
        (51, 'room_15'),   # Stuck in sweep
        (60, 'room_10'),   # Stuck in sweep
    ]

    print("=" * 80)
    print("DEBUGGING STUCK TRIALS")
    print("=" * 80)
    print(f"\nThis script will debug {len(problem_seeds)} problematic trials")
    print(f"Each trial will run for up to 200 ticks with detailed logging\n")

    results = []

    for seed, fire_origin in problem_seeds:
        result = debug_single_trial(
            config=config,
            num_firefighters=2,  # Using 2 firefighters like visualization demo
            fire_origin=fire_origin,
            seed=42 + seed,  # Offset by 42 like benchmark
            max_ticks=200
        )
        results.append(result)
        print("\n")

    # Summary
    print("=" * 80)
    print("SUMMARY OF ALL PROBLEMATIC TRIALS")
    print("=" * 80)

    for result in results:
        print(f"\nSeed {result['seed']}:")
        print(f"  Final phase: {result['final_phase']}")
        print(f"  Rooms visited: {result['rooms_visited']}/{result['total_rooms']} ({result['completion_rate']*100:.1f}%)")
        print(f"  Total ticks: {result['total_ticks']}")


if __name__ == '__main__':
    main()
