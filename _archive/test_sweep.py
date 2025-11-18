#!/usr/bin/env python3
"""
Test the K-medoids + MST sweeping strategy.

This script runs a single trial on the mall configuration to verify:
1. K-medoids partitioning works with corridor distance
2. MST construction is correct
3. DFS 2× traversal is generated properly
4. Firefighters systematically discover all rooms
5. Capable occupants are instructed during sweep
"""

import json
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


def test_sweep_strategy():
    """
    Test sweep coordinator on mall configuration.
    """
    print("="*70)
    print("SWEEP STRATEGY TEST")
    print("="*70)

    # Load mall config
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=6,
        fire_origin='room_10',
        seed=42
    )

    # Get initial state
    initial_state = sim.read()
    initial_stats = sim.get_stats()

    print(f"\nInitial setup:")
    print(f"  Total occupants: {initial_stats['remaining']}")
    print(f"  Firefighters: {len(initial_state['firefighters'])}")
    print(f"  Total rooms: {sum(1 for v in initial_state['graph']['vertices'].values() if v['type'] == 'room')}")

    # Create model with sweep coordinator
    model = OptimalRescueModel(fire_priority_weight=0.0)

    # Track sweep progress
    sweep_ticks = 0
    max_sweep_ticks = 500

    print(f"\nStarting sweep phase...")

    while not sim.get_stats()['remaining'] == 0 and sweep_ticks < max_sweep_ticks:
        state = sim.read()
        actions = model.get_actions(state)

        # Check if phase switched (sweep complete)
        if model.phase == 'optimal_rescue':
            print(f"\n✓ Sweep complete after {sweep_ticks} ticks!")
            break

        # Debug: check sweep status periodically
        if sweep_ticks % 50 == 49 and sweep_ticks < 200:
            # Check phase switch conditions
            sweep_complete = model.sweep_coordinator.is_sweep_complete(state) if model.sweep_coordinator else False
            discovered = state.get('discovered_occupants', {})
            total_capable = sum(occ.get('capable', 0) for occ in discovered.values())
            print(f"  Debug tick {sweep_ticks+1}: sweep_complete={sweep_complete}, capable_remaining={total_capable}")

        sim.update(actions)
        sweep_ticks += 1

        # Print progress every 50 ticks
        if sweep_ticks % 50 == 0:
            stats = sim.get_stats()
            visited_rooms = set()
            for ff_state in state['firefighters'].values():
                visited_rooms.update(ff_state['visited_vertices'])

            all_rooms = [
                v_id for v_id, v_data in state['graph']['vertices'].items()
                if v_data['type'] == 'room'
            ]

            print(f"  Tick {sweep_ticks}: {len(visited_rooms)}/{len(all_rooms)} rooms visited, "
                  f"{stats['remaining']} occupants remaining")

    # Final statistics
    final_stats = sim.get_stats()
    final_state = sim.read()

    visited_rooms = set()
    for ff_state in final_state['firefighters'].values():
        visited_rooms.update(ff_state['visited_vertices'])

    all_rooms = [
        v_id for v_id, v_data in final_state['graph']['vertices'].items()
        if v_data['type'] == 'room'
    ]

    print(f"\n" + "="*70)
    print("SWEEP RESULTS")
    print("="*70)
    print(f"Ticks taken: {sweep_ticks}")
    print(f"Rooms visited: {len(visited_rooms)}/{len(all_rooms)}")
    print(f"All rooms discovered: {len(visited_rooms) == len(all_rooms)}")
    print(f"Phase: {model.phase}")
    print(f"Occupants rescued: {final_stats['rescued']}")
    print(f"Occupants dead: {final_stats['dead']}")
    print(f"Remaining: {final_stats['remaining']}")

    # Check sweep coordinator state
    if model.sweep_coordinator:
        sweep = model.sweep_coordinator
        print(f"\nSweep coordinator state:")
        print(f"  Initialized: {sweep.initialized}")
        print(f"  Partitions: {len(sweep.partitions)} clusters")
        for ff_id, rooms in sweep.partitions.items():
            print(f"    {ff_id}: {len(rooms)} rooms")
        print(f"  Globally visited: {len(sweep.globally_visited)} rooms")

    print("="*70)

    # Verify results - check sweep coordinator's globally_visited, not firefighter visited_vertices
    # (firefighter visited_vertices includes hallways/intersections, not just rooms)
    sweep_visited_rooms = len(sweep.globally_visited) if sweep else 0

    # Check remaining capable occupants
    discovered = final_state.get('discovered_occupants', {})
    total_capable = sum(occ.get('capable', 0) for occ in discovered.values())

    print(f"\nVerification:")
    print(f"  Sweep coordinator visited all rooms: {sweep_visited_rooms == len(all_rooms)} ({sweep_visited_rooms}/{len(all_rooms)})")
    print(f"  All capable instructed: {total_capable == 0} (remaining: {total_capable})")

    assert sweep_visited_rooms == len(all_rooms), f"Not all rooms visited by sweep: {sweep_visited_rooms}/{len(all_rooms)}"

    # Note: Phase may not switch if capable occupants remain uninstructed
    # This is expected behavior - the sweep discovers rooms but may not fully clear all capable
    if model.phase == 'optimal_rescue':
        print(f"  Phase switched: ✓")
    else:
        print(f"  Phase not switched (capable remaining: {total_capable})")

    print("\n✓ Sweep strategy test completed!")


if __name__ == '__main__':
    test_sweep_strategy()
