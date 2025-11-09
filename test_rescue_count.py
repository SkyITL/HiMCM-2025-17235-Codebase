"""
Test to verify that rescued count is working correctly
"""

import json
from simulator import Simulation


def test_rescue_count():
    """Test that people dropped at exits are properly counted as rescued"""
    print("="*60)
    print("Testing Rescue Count Mechanism")
    print("="*60)

    # Load config
    with open('config_example.json', 'r') as f:
        config = json.load(f)

    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=config['fire_params']['origin'],
        seed=42
    )

    initial_stats = sim.get_stats()
    print(f"\nInitial state:")
    print(f"  Total occupants: {initial_stats['total_initial']}")
    print(f"  Rescued: {initial_stats['rescued']}")
    print(f"  Dead: {initial_stats['dead']}")
    print(f"  Remaining: {initial_stats['remaining']}")

    # Get first firefighter
    ff_id = list(sim.firefighters.keys())[0]
    ff = sim.firefighters[ff_id]

    print(f"\n{ff_id} is at: {ff.position}")

    # Move to a room with occupants
    print("\nMoving to hallway_left...")
    actions = {ff_id: [{'type': 'move', 'target': 'hallway_left'}]}
    results = sim.update(actions)
    print(f"  Result: {results['action_results'][ff_id]}")

    print("\nMoving to office_bottom_left...")
    actions = {ff_id: [{'type': 'move', 'target': 'office_bottom_left'}]}
    results = sim.update(actions)
    print(f"  Result: {results['action_results'][ff_id]}")

    # Check room occupancy
    state = sim.read()
    room_occupants = state['discovered_occupants'].get('office_bottom_left', 0)
    print(f"\nRoom has {room_occupants} occupants")

    if room_occupants > 0:
        # Pick up people
        print(f"\nPicking up 5 people...")
        actions = {ff_id: [{'type': 'pick_up', 'count': 5}]}
        results = sim.update(actions)
        print(f"  Result: {results['action_results'][ff_id]}")
        print(f"  Now escorting: {sim.firefighters[ff_id].escorting_count}")

        # Move back to exit
        print("\nMoving back to hallway_left...")
        actions = {ff_id: [{'type': 'move', 'target': 'hallway_left'}]}
        results = sim.update(actions)

        print("\nMoving to exit_left...")
        actions = {ff_id: [{'type': 'move', 'target': 'exit_left'}]}
        results = sim.update(actions)
        print(f"  Now at: {sim.firefighters[ff_id].position}")

        # Drop off at exit
        print(f"\nDropping off {sim.firefighters[ff_id].escorting_count} people at exit...")
        before_rescued = sim.rescued_count
        before_escorting = sim.firefighters[ff_id].escorting_count

        actions = {ff_id: [{'type': 'drop_off'}]}
        results = sim.update(actions)

        after_rescued = sim.rescued_count
        after_escorting = sim.firefighters[ff_id].escorting_count

        print(f"\n  Action results: {results['action_results'][ff_id]}")
        print(f"  Rescued this tick: {results['rescued_this_tick']}")
        print(f"  Before drop_off:")
        print(f"    Total rescued: {before_rescued}")
        print(f"    Escorting: {before_escorting}")
        print(f"  After drop_off:")
        print(f"    Total rescued: {after_rescued}")
        print(f"    Escorting: {after_escorting}")

        if after_rescued > before_rescued:
            print(f"\n✓ SUCCESS! Rescued count increased by {after_rescued - before_rescued}")
        else:
            print(f"\n✗ FAILED! Rescued count did not increase!")
            print(f"  This is the bug we need to fix.")

    # Final stats
    final_stats = sim.get_stats()
    print(f"\nFinal state:")
    print(f"  Total occupants: {final_stats['total_initial']}")
    print(f"  Rescued: {final_stats['rescued']}")
    print(f"  Dead: {final_stats['dead']}")
    print(f"  Remaining: {final_stats['remaining']}")
    print(f"  Accounting: {final_stats['rescued']} + {final_stats['dead']} + {final_stats['remaining']} = {final_stats['rescued'] + final_stats['dead'] + final_stats['remaining']} (should be {final_stats['total_initial']})")


if __name__ == '__main__':
    test_rescue_count()
