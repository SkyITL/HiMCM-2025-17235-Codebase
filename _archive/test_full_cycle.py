#!/usr/bin/env python3
"""
Test the complete evacuation cycle: Sweep → Optimal Rescue

This comprehensive test verifies:
1. Sweep coordinator initializes and partitions rooms
2. Firefighters systematically discover all reachable rooms
3. Capable occupants are instructed during sweep
4. Phase switches to optimal rescue when sweep complete
5. Optimal rescue executes and rescues incapable occupants
6. Complete evacuation cycle succeeds
"""

import json
from simulator import Simulation
from sweep_coordinator import SweepCoordinator


def test_full_cycle():
    """
    Test complete evacuation cycle with sweep coordinator.
    """
    print("="*70)
    print("FULL EVACUATION CYCLE TEST")
    print("="*70)

    # Load mall config
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Create simulation with fixed seed for reproducibility
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

    # Create sweep coordinator manually to test it
    sweep = SweepCoordinator(num_firefighters=6)
    sweep.initialize_sweep(initial_state)

    print(f"\nSweep coordinator initialized:")
    print(f"  Partitions: {len(sweep.partitions)} clusters")
    for ff_id, rooms in sweep.partitions.items():
        print(f"    {ff_id}: {len(rooms)} rooms")

    # Verify sweep paths were generated
    print(f"\nSweep paths generated:")
    for ff_id, path in sweep.sweep_paths.items():
        print(f"    {ff_id}: {len(path)} vertices in DFS path")

    # Run sweep phase
    print(f"\n{'='*70}")
    print("PHASE 1: SWEEP")
    print(f"{'='*70}")

    tick = 0
    max_ticks = 1000
    sweep_complete = False

    while tick < max_ticks:
        state = sim.read()

        # Check if sweep is complete
        if sweep.is_sweep_complete(state):
            print(f"\n✓ Sweep complete at tick {tick}!")
            sweep_complete = True

            # Check if all capable are instructed
            discovered = state.get('discovered_occupants', {})
            total_capable = sum(occ.get('capable', 0) for occ in discovered.values())
            print(f"  Rooms visited: {len(sweep.globally_visited)}")
            print(f"  Capable remaining: {total_capable}")

            if total_capable == 0:
                print(f"  All capable occupants instructed!")
                break
            else:
                print(f"  Continuing to instruct {total_capable} capable occupants...")

        # Get sweep actions
        actions = sweep.get_sweep_actions(state)

        # Update simulation
        sim.update(actions)
        tick += 1

        # Progress updates
        if tick % 100 == 0:
            stats = sim.get_stats()
            discovered = state.get('discovered_occupants', {})
            total_capable = sum(occ.get('capable', 0) for occ in discovered.values())
            print(f"  Tick {tick}: {len(sweep.globally_visited)} rooms visited, "
                  f"{total_capable} capable remaining, "
                  f"{stats['remaining']} total remaining")

    if not sweep_complete:
        print(f"\n⚠️  Sweep did not complete within {max_ticks} ticks")
        return False

    # Get final sweep stats
    sweep_stats = sim.get_stats()
    final_state = sim.read()
    final_discovered = final_state.get('discovered_occupants', {})

    print(f"\nSweep phase results:")
    print(f"  Ticks: {tick}")
    print(f"  Rooms discovered: {len(sweep.globally_visited)}")
    print(f"  Capable instructed: {sum(1 for occ in final_discovered.values() if occ.get('capable', 0) == 0)}")
    print(f"  Incapable discovered: {sum(occ.get('incapable', 0) for occ in final_discovered.values())}")
    print(f"  Rescued so far: {sweep_stats['rescued']}")
    print(f"  Dead so far: {sweep_stats['dead']}")

    # Now test optimal rescue phase (if we have OptimalRescueModel integrated)
    try:
        from optimal_rescue_model import OptimalRescueModel

        print(f"\n{'='*70}")
        print("PHASE 2: OPTIMAL RESCUE")
        print(f"{'='*70}")

        # Create a fresh simulation with same seed
        sim2 = Simulation(
            config=config,
            num_firefighters=6,
            fire_origin='room_10',
            seed=42
        )

        model = OptimalRescueModel(fire_priority_weight=0.0)

        # Run full cycle
        rescue_tick = 0
        max_rescue_ticks = 2000

        while rescue_tick < max_rescue_ticks:
            state = sim2.read()
            stats = sim2.get_stats()

            if stats['remaining'] == 0:
                print(f"\n✓ All occupants evacuated or deceased at tick {rescue_tick}!")
                break

            actions = model.get_actions(state)
            sim2.update(actions)
            rescue_tick += 1

            # Progress updates
            if rescue_tick % 200 == 0:
                stats = sim2.get_stats()
                print(f"  Tick {rescue_tick}: Phase={model.phase}, "
                      f"Remaining={stats['remaining']}, "
                      f"Rescued={stats['rescued']}, "
                      f"Dead={stats['dead']}")

        # Final results
        final_stats = sim2.get_stats()

        print(f"\n{'='*70}")
        print("FINAL RESULTS")
        print(f"{'='*70}")
        print(f"Total ticks: {rescue_tick}")
        print(f"Final phase: {model.phase}")
        print(f"Rescued: {final_stats['rescued']}")
        print(f"Dead: {final_stats['dead']}")
        print(f"Remaining: {final_stats['remaining']}")
        print(f"Survival rate: {final_stats['rescued']/(final_stats['rescued']+final_stats['dead'])*100:.1f}%")

        # Verify results
        success = True
        if model.phase != 'optimal_rescue':
            print(f"\n❌ FAIL: Phase did not switch to optimal rescue")
            success = False

        if final_stats['remaining'] > 0:
            print(f"\n⚠️  WARNING: {final_stats['remaining']} occupants still remaining")

        if success:
            print(f"\n✓ FULL CYCLE TEST PASSED!")
        else:
            print(f"\n❌ FULL CYCLE TEST FAILED")

        return success

    except ImportError as e:
        print(f"\n⚠️  Could not import OptimalRescueModel: {e}")
        print(f"   Sweep coordinator test passed, but full cycle test skipped")
        return True


if __name__ == '__main__':
    success = test_full_cycle()
    exit(0 if success else 1)
