#!/usr/bin/env python3
"""
Test script for the new two-type occupant system
"""

import json
from simulator import Simulation

def test_initialization():
    """Test that simulator initializes with new occupant types"""
    print("=" * 60)
    print("TEST 1: Initialization")
    print("=" * 60)

    with open('config_example.json', 'r') as f:
        config = json.load(f)

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin='office_bottom_center',
        seed=42
    )

    # Check that vertices have the new fields
    print("\nChecking vertices have new occupant fields...")
    for vertex_id, vertex in sim.vertices.items():
        if vertex.type == 'room':
            print(f"{vertex_id}: capable={vertex.capable_count}, incapable={vertex.incapable_count}, instructed={vertex.instructed_capable_count}")
            assert hasattr(vertex, 'capable_count'), f"{vertex_id} missing capable_count"
            assert hasattr(vertex, 'incapable_count'), f"{vertex_id} missing incapable_count"
            assert hasattr(vertex, 'instructed_capable_count'), f"{vertex_id} missing instructed_capable_count"

    # Check firefighters have carrying field
    print("\nChecking firefighters have carrying field...")
    for ff_id, ff in sim.firefighters.items():
        print(f"{ff_id}: carrying_incapable={ff.carrying_incapable}")
        assert hasattr(ff, 'carrying_incapable'), f"{ff_id} missing carrying_incapable"

    print("\n✓ Initialization test passed!")
    return sim

def test_actions(sim):
    """Test new actions: instruct, pick_up_incapable, drop_off"""
    print("\n" + "=" * 60)
    print("TEST 2: Actions")
    print("=" * 60)

    # Find a room with occupants
    target_room = None
    for vertex_id, vertex in sim.vertices.items():
        if vertex.type == 'room' and (vertex.capable_count > 0 or vertex.incapable_count > 0):
            target_room = vertex_id
            print(f"\nFound room with occupants: {vertex_id}")
            print(f"  capable={vertex.capable_count}, incapable={vertex.incapable_count}")
            break

    if not target_room:
        print("No rooms with occupants found for testing")
        return

    # Move firefighter to that room
    ff_id = 'ff_0'
    ff = sim.firefighters[ff_id]
    print(f"\nMoving {ff_id} from {ff.position} to {target_room}...")

    # Find path to target room
    from collections import deque
    queue = deque([[ff.position]])
    visited = {ff.position}
    path = None

    while queue and not path:
        current_path = queue.popleft()
        current = current_path[-1]

        if current == target_room:
            path = current_path
            break

        for neighbor, _ in sim.adjacency[current]:
            if neighbor not in visited and sim.edges[_].exists:
                visited.add(neighbor)
                queue.append(current_path + [neighbor])

    if not path:
        print(f"No path found to {target_room}")
        return

    # Move along path
    for i in range(1, len(path)):
        actions = {ff_id: [{'type': 'move', 'target': path[i]}]}
        sim.update(actions)
        print(f"  Moved to {path[i]}")

    # Test instruct action
    vertex = sim.vertices[target_room]
    if vertex.capable_count > 0:
        capable_before = vertex.capable_count
        print(f"\nTesting instruct action...")
        print(f"  Before: capable={capable_before}, instructed={vertex.instructed_capable_count}")
        actions = {ff_id: [{'type': 'instruct'}]}
        result = sim.update(actions)
        print(f"  After: capable={vertex.capable_count}, instructed={vertex.instructed_capable_count}")
        assert vertex.capable_count == 0, "Instruct should move all capable to instructed"

        # Instructed people move immediately in the same tick, so check nearby vertices
        total_instructed = sum(v.instructed_capable_count for v in sim.vertices.values())
        print(f"  Total instructed people in building: {total_instructed}")
        assert total_instructed > 0 or result['rescued_this_tick'] > 0, "Should have instructed people somewhere or rescued"
        print("  ✓ Instruct action works! (People moved toward exit)")

    # Test pick_up action
    if vertex.incapable_count > 0:
        print(f"\nTesting pick_up_incapable action...")
        print(f"  Before: incapable={vertex.incapable_count}, carrying={ff.carrying_incapable}")
        actions = {ff_id: [{'type': 'pick_up_incapable'}]}
        result = sim.update(actions)
        print(f"  After: incapable={vertex.incapable_count}, carrying={ff.carrying_incapable}")
        assert ff.carrying_incapable == 1, "Should be carrying 1 person"
        print("  ✓ Pick up action works!")

        # Test drop_off action at exit
        print(f"\nTesting drop_off action...")
        # Find nearest exit
        for exit_id, exit_vertex in sim.vertices.items():
            if exit_vertex.type == 'exit':
                # Move to exit
                queue = deque([[ff.position]])
                visited = {ff.position}
                path = None

                while queue and not path:
                    current_path = queue.popleft()
                    current = current_path[-1]

                    if current == exit_id:
                        path = current_path
                        break

                    for neighbor, _ in sim.adjacency[current]:
                        if neighbor not in visited and sim.edges[_].exists:
                            visited.add(neighbor)
                            queue.append(current_path + [neighbor])

                if path:
                    for i in range(1, len(path)):
                        actions = {ff_id: [{'type': 'move', 'target': path[i]}]}
                        sim.update(actions)

                    rescued_before = sim.rescued_count
                    actions = {ff_id: [{'type': 'drop_off'}]}
                    result = sim.update(actions)
                    print(f"  Before: rescued={rescued_before}, carrying={1}")
                    print(f"  After: rescued={sim.rescued_count}, carrying={ff.carrying_incapable}")
                    assert ff.carrying_incapable == 0, "Should not be carrying after drop off"
                    assert sim.rescued_count == rescued_before + 1, "Should have rescued 1 person"
                    print("  ✓ Drop off action works!")
                    break

    print("\n✓ Actions test passed!")

def test_instructed_movement(sim):
    """Test that instructed people move autonomously"""
    print("\n" + "=" * 60)
    print("TEST 3: Instructed People Movement")
    print("=" * 60)

    # Find a room with instructed people
    target_room = None
    for vertex_id, vertex in sim.vertices.items():
        if vertex.instructed_capable_count > 0:
            target_room = vertex_id
            print(f"\nFound room with instructed people: {vertex_id}")
            print(f"  instructed={vertex.instructed_capable_count}")
            break

    if not target_room:
        print("No rooms with instructed people found")
        return

    # Run a few ticks and watch them move
    print("\nRunning 5 ticks to observe movement...")
    for i in range(5):
        result = sim.update({})
        print(f"  Tick {sim.tick}: ", end="")

        # Count instructed people in each location
        instructed_locations = {}
        for vertex_id, vertex in sim.vertices.items():
            if vertex.instructed_capable_count > 0:
                instructed_locations[vertex_id] = vertex.instructed_capable_count

        print(f"Instructed people at: {instructed_locations}, Rescued: {sim.rescued_count}")

    print("\n✓ Instructed movement test completed!")

def test_read_state():
    """Test that read() returns correct format"""
    print("\n" + "=" * 60)
    print("TEST 4: Read State Format")
    print("=" * 60)

    with open('config_example.json', 'r') as f:
        config = json.load(f)

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin='office_bottom_center',
        seed=42
    )

    state = sim.read()

    print("\nChecking state format...")

    # Check firefighter state
    for ff_id, ff_state in state['firefighters'].items():
        print(f"{ff_id}: {ff_state}")
        assert 'carrying_incapable' in ff_state, f"{ff_id} missing carrying_incapable in state"

    # Check discovered_occupants format
    print("\nDiscovered occupants:")
    for vertex_id, occupants in state['discovered_occupants'].items():
        if occupants['capable'] > 0 or occupants['incapable'] > 0 or occupants['instructed'] > 0:
            print(f"{vertex_id}: {occupants}")
        assert isinstance(occupants, dict), f"{vertex_id} occupants should be dict"
        assert 'capable' in occupants, f"{vertex_id} missing capable"
        assert 'incapable' in occupants, f"{vertex_id} missing incapable"
        assert 'instructed' in occupants, f"{vertex_id} missing instructed"

    print("\n✓ Read state format test passed!")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("TESTING NEW TWO-TYPE OCCUPANT SYSTEM")
    print("=" * 60)

    try:
        sim = test_initialization()
        test_actions(sim)
        test_instructed_movement(sim)
        test_read_state()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
