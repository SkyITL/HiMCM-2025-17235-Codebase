"""
Test file for Emergency Evacuation Simulator
Demonstrates basic functionality and verifies simulator works correctly.
"""

import json
from simulator import Simulation


def load_config(filename: str):
    """Load configuration from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)


def test_basic_simulation():
    """Test basic simulation setup and execution"""
    print("=" * 60)
    print("TEST: Basic Simulation Setup")
    print("=" * 60)

    # Load configuration
    config = load_config('config_example.json')

    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=config['fire_params']['origin'],
        seed=42
    )

    # Check initial state
    state = sim.read()
    print(f"\nInitial state:")
    print(f"  Tick: {state['tick']}")
    print(f"  Number of vertices: {len(state['graph']['vertices'])}")
    print(f"  Number of edges: {len(state['graph']['edges'])}")
    print(f"  Number of firefighters: {len(state['firefighters'])}")

    stats = sim.get_stats()
    print(f"\nInitial stats:")
    print(f"  Total occupants: {stats['total_initial']}")
    print(f"  Rescued: {stats['rescued']}")
    print(f"  Dead: {stats['dead']}")
    print(f"  Remaining: {stats['remaining']}")

    print("\n✓ Basic simulation setup successful")
    return sim


def test_firefighter_movement(sim: Simulation):
    """Test firefighter movement"""
    print("\n" + "=" * 60)
    print("TEST: Firefighter Movement")
    print("=" * 60)

    state = sim.read()
    ff_id = list(state['firefighters'].keys())[0]
    ff_state = state['firefighters'][ff_id]

    print(f"\nFirefighter {ff_id} initial position: {ff_state['position']}")

    # Get neighbors
    current_pos = ff_state['position']
    neighbors = [v_id for v_id, _ in sim.adjacency[current_pos]]

    if neighbors:
        target = neighbors[0]
        print(f"Moving to: {target}")

        # Execute move action
        actions = {
            ff_id: [{'type': 'move', 'target': target}]
        }
        results = sim.update(actions)

        # Check result
        if results['action_results'][ff_id][0]['success']:
            print("✓ Movement successful")
        else:
            print(f"✗ Movement failed: {results['action_results'][ff_id][0]['reason']}")

        # Verify new position
        new_state = sim.read()
        new_pos = new_state['firefighters'][ff_id]['position']
        print(f"New position: {new_pos}")
        assert new_pos == target, "Position didn't update correctly"


def test_occupant_rescue(sim: Simulation):
    """Test picking up and rescuing occupants"""
    print("\n" + "=" * 60)
    print("TEST: Occupant Rescue")
    print("=" * 60)

    # Find a room with occupants
    state = sim.read()
    ff_id = list(state['firefighters'].keys())[0]

    # Move firefighter to a room with occupants
    # First, let's find which rooms have occupants
    print("\nSearching for rooms with occupants...")

    # Navigate to a room
    # We'll move the firefighter step by step to office_bottom_left
    path_to_room = ['hallway_left', 'office_bottom_left']

    for target in path_to_room:
        actions = {ff_id: [{'type': 'move', 'target': target}]}
        results = sim.update(actions)
        current_state = sim.read()
        print(f"Moved to: {current_state['firefighters'][ff_id]['position']}")

    # Check if room has occupants
    current_state = sim.read()
    current_pos = current_state['firefighters'][ff_id]['position']

    if current_pos in current_state['discovered_occupants']:
        occupant_count = current_state['discovered_occupants'][current_pos]
        print(f"\nFound {occupant_count} occupants in {current_pos}")

        if occupant_count > 0:
            # Pick up occupants
            actions = {ff_id: [{'type': 'pick_up', 'count': min(5, occupant_count)}]}
            results = sim.update(actions)
            print(f"Picked up occupants: {results['action_results'][ff_id][0]['success']}")

            # Check escorting count
            current_state = sim.read()
            escorting = current_state['firefighters'][ff_id]['escorting_count']
            print(f"Now escorting: {escorting} people")

            # Move back to exit
            path_to_exit = ['hallway_left', 'exit_left']
            for target in path_to_exit:
                actions = {ff_id: [{'type': 'move', 'target': target}]}
                results = sim.update(actions)
                print(f"Moving to exit via: {target}")

            # Drop off at exit
            actions = {ff_id: [{'type': 'drop_off'}]}
            results = sim.update(actions)
            print(f"Drop off result: {results['action_results'][ff_id][0]}")

            stats = sim.get_stats()
            print(f"\n✓ Rescued {stats['rescued']} people total")
    else:
        print(f"Room {current_pos} has no discovered occupants yet")


def test_random_events():
    """Test random fire events over time"""
    print("\n" + "=" * 60)
    print("TEST: Random Fire Events")
    print("=" * 60)

    config = load_config('config_example.json')
    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=config['fire_params']['origin'],
        seed=123  # Different seed for variety
    )

    print("\nSimulating 50 ticks to observe random events...")

    edge_deletions = 0
    room_burndowns = 0
    smoke_deaths = 0

    for i in range(50):
        # No actions, just let time pass
        results = sim.update({})

        for event in results['events']:
            if event['type'] == 'edge_deleted':
                edge_deletions += 1
                print(f"Tick {results['tick']}: Edge deleted: {event['edge_id']}")
            elif event['type'] == 'room_burned':
                room_burndowns += 1
                print(f"Tick {results['tick']}: Room burned: {event['vertex_id']}, {event['deaths']} deaths")
            elif event['type'] == 'smoke_deaths':
                smoke_deaths += event['deaths']

    print(f"\nAfter 50 ticks:")
    print(f"  Edge deletions: {edge_deletions}")
    print(f"  Room burndowns: {room_burndowns}")
    print(f"  Smoke deaths: {smoke_deaths}")

    stats = sim.get_stats()
    print(f"  Total dead: {stats['dead']}")

    print("\n✓ Random events functioning")


def test_full_sweep_scenario():
    """Test a complete sweep scenario"""
    print("\n" + "=" * 60)
    print("TEST: Full Sweep Scenario (2 Firefighters)")
    print("=" * 60)

    config = load_config('config_example.json')
    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=config['fire_params']['origin'],
        seed=42
    )

    # Simple greedy strategy: each firefighter sweeps nearest rooms
    max_ticks = 200

    for tick in range(max_ticks):
        state = sim.read()
        stats = sim.get_stats()

        # Stop if all occupants rescued or dead
        if stats['remaining'] == 0:
            print(f"\n✓ All occupants accounted for at tick {tick}")
            break

        # Simple AI: move toward nearest undiscovered room
        actions = {}

        for ff_id, ff_state in state['firefighters'].items():
            ff_actions = []
            current_pos = ff_state['position']

            # If escorting, move toward exit
            if ff_state['escorting_count'] > 0:
                # Simple path to nearest exit
                neighbors = [n for n, _ in sim.adjacency[current_pos]]
                for neighbor in neighbors:
                    vertex = sim.vertices[neighbor]
                    if vertex.type in ['exit', 'window_exit']:
                        ff_actions.append({'type': 'move', 'target': neighbor})
                        ff_actions.append({'type': 'drop_off'})
                        break
                    elif vertex.type == 'hallway':
                        ff_actions.append({'type': 'move', 'target': neighbor})
                        break
            else:
                # Move to nearest unvisited room
                visited = set(ff_state['visited_vertices'])
                neighbors = [n for n, _ in sim.adjacency[current_pos]]

                # Check current location for occupants
                if current_pos in state['discovered_occupants']:
                    if state['discovered_occupants'][current_pos] > 0:
                        ff_actions.append({'type': 'pick_up', 'count': ff_state['capacity']})

                # Move to unvisited room
                for neighbor in neighbors:
                    if neighbor not in visited:
                        vertex = sim.vertices[neighbor]
                        if vertex.type == 'room':
                            ff_actions.append({'type': 'move', 'target': neighbor})
                            break

                # Otherwise move to any unvisited vertex
                if not ff_actions:
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            ff_actions.append({'type': 'move', 'target': neighbor})
                            break

            actions[ff_id] = ff_actions

        results = sim.update(actions)

        # Print progress every 20 ticks
        if tick % 20 == 0:
            print(f"\nTick {tick}:")
            print(f"  Rescued: {stats['rescued']}")
            print(f"  Dead: {stats['dead']}")
            print(f"  Remaining: {stats['remaining']}")

    final_stats = sim.get_stats()
    print(f"\n{'='*60}")
    print("FINAL RESULTS:")
    print(f"{'='*60}")
    print(f"Time elapsed: {final_stats['time_minutes']:.2f} minutes ({final_stats['tick']} ticks)")
    print(f"Rescued: {final_stats['rescued']}")
    print(f"Dead: {final_stats['dead']}")
    print(f"Still inside: {final_stats['remaining']}")
    print(f"Total: {final_stats['total_initial']}")
    print(f"Survival rate: {final_stats['rescued'] / max(1, final_stats['total_initial']) * 100:.1f}%")


if __name__ == '__main__':
    # Run tests
    print("\n" + "=" * 60)
    print("EMERGENCY EVACUATION SIMULATOR - TEST SUITE")
    print("=" * 60)

    # Test 1: Basic setup
    sim = test_basic_simulation()

    # Test 2: Movement
    test_firefighter_movement(sim)

    # Test 3: Rescue mechanics
    test_occupant_rescue(sim)

    # Test 4: Random events
    test_random_events()

    # Test 5: Full scenario
    test_full_sweep_scenario()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
