#!/usr/bin/env python3
"""
Detailed tracking of instructed people movement
"""

import json
from simulator import Simulation

print("=" * 60)
print("DETAILED MOVEMENT TRACKING")
print("=" * 60)

with open('config_realistic_apartment.json', 'r') as f:
    config = json.load(f)

# Use 3 firefighters instructing different rooms
sim = Simulation(
    config=config,
    num_firefighters=3,
    fire_origin='room_5',
    seed=100
)

print("\nInitial setup:")
print("Placing firefighters in different rooms...")

# Place firefighters at rooms far from exit
sim.firefighters['ff_0'].position = 'room_1'  # North wing
sim.firefighters['ff_1'].position = 'room_2'  # North wing
sim.firefighters['ff_2'].position = 'living_room'  # East wing

print(f"  ff_0 at room_1 ({sim.vertices['room_1'].capable_count} capable)")
print(f"  ff_1 at room_2 ({sim.vertices['room_2'].capable_count} capable)")
print(f"  ff_2 at living_room ({sim.vertices['living_room'].capable_count} capable)")

# All instruct at the same time
print("\nTick 1: All 3 firefighters instruct simultaneously")
actions = {
    'ff_0': [{'type': 'instruct'}],
    'ff_1': [{'type': 'instruct'}],
    'ff_2': [{'type': 'instruct'}]
}
result = sim.update(actions)

print("\nAction results:")
for ff_id, ff_result in result['action_results'].items():
    print(f"  {ff_id}: {ff_result}")

# Track instructed people locations
def show_instructed_locations(sim):
    print(f"\nInstructed people locations (tick {sim.tick}):")
    total = 0
    for v_id, v in sim.vertices.items():
        if v.instructed_capable_count > 0:
            print(f"  {v_id}: {v.instructed_capable_count} people")
            total += v.instructed_capable_count
    print(f"  Total instructed: {total}")
    print(f"  Total rescued: {sim.rescued_count}")
    return total

total = show_instructed_locations(sim)

# Now run tick by tick and watch movement
print("\n" + "=" * 60)
print("MOVEMENT BY TICK")
print("=" * 60)

for tick_num in range(10):
    if total == 0:
        break

    print(f"\n--- Running tick {sim.tick + 1} ---")
    result = sim.update({})

    if result['rescued_this_tick'] > 0:
        print(f"  ✓ Rescued {result['rescued_this_tick']} people this tick!")

    # Show movement events
    if 'events' in result and result['events']:
        print(f"  Events: {result['events']}")

    total = show_instructed_locations(sim)

print("\n" + "=" * 60)
print("ANALYZING RESULTS")
print("=" * 60)

# Count movements per tick
# In tick 1, people were instructed and moved immediately
# Let's check how many vertices they crossed per tick

print("\nExpected behavior:")
print("  - Instructed people should move 1 vertex per tick")
print("  - Max flow on edges should limit how many can move together")
print("  - Having 3 groups instructed shouldn't make individuals move faster")

print(f"\nActual results:")
print(f"  Total rescued: {sim.rescued_count}")
print(f"  Ticks to complete: {sim.tick}")

# The key insight: we instructed 3 groups simultaneously at tick 1
# If they all move at normal speed (1 vertex/tick), they should all
# arrive at exit at roughly the same time
# But if there's a bug, they might interfere with each other's movement
# or move faster than expected
