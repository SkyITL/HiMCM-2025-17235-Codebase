#!/usr/bin/env python3
"""
Test for the multi-firefighter instruction bug
"""

import json
from simulator import Simulation

print("=" * 60)
print("TESTING MULTI-FIREFIGHTER INSTRUCTION BUG")
print("=" * 60)

with open('config_realistic_apartment.json', 'r') as f:
    config = json.load(f)

sim = Simulation(
    config=config,
    num_firefighters=3,
    fire_origin='room_5',
    seed=42
)

# Find a room with people
target_room = None
for vertex_id, vertex in sim.vertices.items():
    if vertex.type == 'room' and vertex.capable_count > 0:
        target_room = vertex_id
        initial_capable = vertex.capable_count
        print(f"\nTarget room: {target_room}")
        print(f"Initial capable people: {initial_capable}")
        break

if not target_room:
    print("No rooms with capable people found")
    exit(1)

# Move all 3 firefighters to the same room
print("\n" + "=" * 60)
print("SCENARIO 1: All 3 firefighters instruct at same time")
print("=" * 60)

for ff_id in ['ff_0', 'ff_1', 'ff_2']:
    ff = sim.firefighters[ff_id]
    print(f"\nMoving {ff_id} from {ff.position} to {target_room}...")

    # Correct path for room_1: exit_main -> entrance_hall -> hallway_central -> hallway_west -> room_1
    path = ['entrance_hall', 'hallway_central', 'hallway_west', target_room]

    for next_pos in path:
        if ff.position != next_pos:
            actions = {ff_id: [{'type': 'move', 'target': next_pos}]}
            sim.update(actions)
            print(f"  {ff_id} moved to {sim.firefighters[ff_id].position}")

# Check all firefighters are there
print("\nFirefighter positions:")
for ff_id in ['ff_0', 'ff_1', 'ff_2']:
    print(f"  {ff_id}: {sim.firefighters[ff_id].position}")

# Check room state before instruction
vertex = sim.vertices[target_room]
print(f"\n{target_room} before instruction:")
print(f"  Capable: {vertex.capable_count}")
print(f"  Instructed: {vertex.instructed_capable_count}")

# All 3 firefighters instruct at the same time
print("\nAll 3 firefighters instructing simultaneously...")
actions = {
    'ff_0': [{'type': 'instruct'}],
    'ff_1': [{'type': 'instruct'}],
    'ff_2': [{'type': 'instruct'}]
}
result = sim.update(actions)

print(f"\nAction results:")
for ff_id, ff_result in result['action_results'].items():
    print(f"  {ff_id}: {ff_result}")

# Check room state after instruction
print(f"\n{target_room} after instruction:")
print(f"  Capable: {vertex.capable_count}")
print(f"  Instructed: {vertex.instructed_capable_count}")

# Check all vertices for instructed people
print("\nAll vertices with instructed people:")
total_instructed = 0
for v_id, v in sim.vertices.items():
    if v.instructed_capable_count > 0:
        print(f"  {v_id}: {v.instructed_capable_count}")
        total_instructed += v.instructed_capable_count

print(f"\nTotal instructed people: {total_instructed}")
print(f"Expected: {initial_capable}")

if total_instructed > initial_capable:
    print(f"\n❌ BUG DETECTED: {total_instructed - initial_capable} extra people created!")
else:
    print(f"\n✓ No duplication bug detected")

# Test movement speed
print("\n" + "=" * 60)
print("SCENARIO 2: Testing movement speed")
print("=" * 60)

print("\nRunning 3 ticks to observe movement...")
for i in range(3):
    result = sim.update({})
    print(f"\nTick {sim.tick}:")
    print(f"  Rescued this tick: {result['rescued_this_tick']}")
    print(f"  Total rescued: {sim.rescued_count}")

    # Show where instructed people are
    for v_id, v in sim.vertices.items():
        if v.instructed_capable_count > 0:
            print(f"  {v_id}: {v.instructed_capable_count} instructed people")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
