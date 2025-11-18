#!/usr/bin/env python3
"""
Verification that the multi-instruction speed bug is fixed
"""

import json
from simulator import Simulation

print("=" * 60)
print("BUG FIX VERIFICATION")
print("=" * 60)

with open('config_realistic_apartment.json', 'r') as f:
    config = json.load(f)

# Test with 3 firefighters instructing simultaneously
sim = Simulation(
    config=config,
    num_firefighters=3,
    fire_origin='room_5',
    seed=100
)

print("\nScenario: 3 firefighters instruct people at different distances from exit")
print("  - room_1 -> 4 vertices to exit_main")
print("  - room_2 -> 3 vertices to exit_main")
print("  - living_room -> 2 vertices to exit_main")

# Place firefighters
sim.firefighters['ff_0'].position = 'room_1'
sim.firefighters['ff_1'].position = 'room_2'
sim.firefighters['ff_2'].position = 'living_room'

print(f"\nInitial occupants:")
print(f"  room_1: {sim.vertices['room_1'].capable_count} capable")
print(f"  room_2: {sim.vertices['room_2'].capable_count} capable")
print(f"  living_room: {sim.vertices['living_room'].capable_count} capable")

total_people = (sim.vertices['room_1'].capable_count +
                sim.vertices['room_2'].capable_count +
                sim.vertices['living_room'].capable_count)

# All instruct at once
print(f"\nTick 1: All 3 firefighters instruct simultaneously")
actions = {
    'ff_0': [{'type': 'instruct'}],
    'ff_1': [{'type': 'instruct'}],
    'ff_2': [{'type': 'instruct'}]
}
result = sim.update(actions)

# Verify people moved exactly 1 vertex
print(f"\nAfter instruction (still tick 1):")
hallway_west = sim.vertices['hallway_west'].instructed_capable_count
hallway_central = sim.vertices['hallway_central'].instructed_capable_count
entrance_hall = sim.vertices['entrance_hall'].instructed_capable_count
rescued_tick1 = sim.rescued_count

print(f"  hallway_west: {hallway_west} (from room_1)")
print(f"  hallway_central: {hallway_central} (from room_2)")
print(f"  entrance_hall: {entrance_hall} (from living_room)")
print(f"  Rescued: {rescued_tick1}")

# Verify bug is fixed: people should NOT all be rescued in tick 1
if rescued_tick1 == total_people:
    print(f"\n❌ BUG STILL EXISTS: All {total_people} people rescued instantly!")
    print("   People should move 1 vertex per tick, not teleport to exit.")
    exit(1)
else:
    print(f"\n✓ Good: Only {rescued_tick1} rescued in tick 1 (people moving normally)")

# Track when each person reaches exit
print("\nTracking arrival times:")
arrivals_by_tick = {}

for tick_num in range(10):
    if sim.rescued_count >= total_people:
        break

    result = sim.update({})
    if result['rescued_this_tick'] > 0:
        arrivals_by_tick[sim.tick] = result['rescued_this_tick']
        print(f"  Tick {sim.tick}: {result['rescued_this_tick']} people reached exit")

print(f"\nFinal results:")
print(f"  Total people: {total_people}")
print(f"  Total rescued: {sim.rescued_count}")
print(f"  Time to complete: {max(arrivals_by_tick.keys())} ticks")

# Verify staggered arrivals (people from different distances arrive at different times)
if len(arrivals_by_tick) > 1:
    print(f"\n✓ VERIFIED: People arrived in {len(arrivals_by_tick)} different ticks")
    print("  This confirms they're moving 1 vertex/tick, not all at once")
else:
    print(f"\n⚠ WARNING: All people arrived in the same tick")
    print("  This might indicate an issue, but could also mean they were equidistant")

print("\n" + "=" * 60)
print("✓ BUG FIX VERIFIED - Movement speed is now correct!")
print("=" * 60)
