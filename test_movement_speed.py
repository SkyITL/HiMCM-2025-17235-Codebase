#!/usr/bin/env python3
"""
Test if instructed people movement speed is affected by number of instructing firefighters
"""

import json
from simulator import Simulation

print("=" * 60)
print("TESTING INSTRUCTED PEOPLE MOVEMENT SPEED")
print("=" * 60)

# Scenario 1: 1 firefighter instructing people in 3 rooms sequentially
print("\n" + "=" * 60)
print("SCENARIO 1: 1 firefighter, sequential instruction")
print("=" * 60)

with open('config_realistic_apartment.json', 'r') as f:
    config = json.load(f)

sim1 = Simulation(
    config=config,
    num_firefighters=1,
    fire_origin='room_5',
    seed=100
)

print("\nInitial occupants:")
for vertex_id, vertex in sim1.vertices.items():
    if vertex.type == 'room' and vertex.capable_count > 0:
        print(f"  {vertex_id}: {vertex.capable_count} capable")

# Manually place firefighter and instruct
ff_id = 'ff_0'

# Instruct people in room_1
sim1.firefighters[ff_id].position = 'room_1'
sim1.update({ff_id: [{'type': 'instruct'}]})
print(f"\nTick {sim1.tick}: Instructed people in room_1")

# Instruct people in room_2
sim1.firefighters[ff_id].position = 'room_2'
sim1.update({ff_id: [{'type': 'instruct'}]})
print(f"Tick {sim1.tick}: Instructed people in room_2")

# Instruct people in room_3
sim1.firefighters[ff_id].position = 'room_3'
sim1.update({ff_id: [{'type': 'instruct'}]})
print(f"Tick {sim1.tick}: Instructed people in room_3")

print(f"\nAll instructions complete at tick {sim1.tick}")

# Run simulation until all rescued or 20 ticks
start_tick = sim1.tick
for i in range(20):
    result = sim1.update({})
    if result['rescued_this_tick'] > 0:
        print(f"Tick {sim1.tick}: Rescued {result['rescued_this_tick']}, total {sim1.rescued_count}")

    # Check if all instructed people are rescued
    total_instructed = sum(v.instructed_capable_count for v in sim1.vertices.values())
    if total_instructed == 0:
        break

end_tick = sim1.tick
print(f"\nScenario 1 complete:")
print(f"  Start: tick {start_tick}")
print(f"  End: tick {end_tick}")
print(f"  Duration: {end_tick - start_tick} ticks")
print(f"  Rescued: {sim1.rescued_count}")

# Scenario 2: 3 firefighters instructing people in 3 rooms simultaneously
print("\n" + "=" * 60)
print("SCENARIO 2: 3 firefighters, parallel instruction")
print("=" * 60)

sim2 = Simulation(
    config=config,
    num_firefighters=3,
    fire_origin='room_5',
    seed=100
)

print("\nInitial occupants:")
for vertex_id, vertex in sim2.vertices.items():
    if vertex.type == 'room' and vertex.capable_count > 0:
        print(f"  {vertex_id}: {vertex.capable_count} capable")

# Place all 3 firefighters and instruct at the same tick
sim2.firefighters['ff_0'].position = 'room_1'
sim2.firefighters['ff_1'].position = 'room_2'
sim2.firefighters['ff_2'].position = 'room_3'

actions = {
    'ff_0': [{'type': 'instruct'}],
    'ff_1': [{'type': 'instruct'}],
    'ff_2': [{'type': 'instruct'}]
}
sim2.update(actions)
print(f"\nTick {sim2.tick}: All 3 firefighters instructed simultaneously")

# Run simulation until all rescued or 20 ticks
start_tick = sim2.tick
for i in range(20):
    result = sim2.update({})
    if result['rescued_this_tick'] > 0:
        print(f"Tick {sim2.tick}: Rescued {result['rescued_this_tick']}, total {sim2.rescued_count}")

    # Check if all instructed people are rescued
    total_instructed = sum(v.instructed_capable_count for v in sim2.vertices.values())
    if total_instructed == 0:
        break

end_tick = sim2.tick
print(f"\nScenario 2 complete:")
print(f"  Start: tick {start_tick}")
print(f"  End: tick {end_tick}")
print(f"  Duration: {end_tick - start_tick} ticks")
print(f"  Rescued: {sim2.rescued_count}")

# Compare
print("\n" + "=" * 60)
print("COMPARISON")
print("=" * 60)
scenario1_duration = end_tick - start_tick
# For scenario 2, need to recalculate from the original values
sim2_start = 1  # They all instructed at tick 1
sim2_end = end_tick
scenario2_duration = sim2_end - sim2_start

print(f"\nScenario 1 (sequential): {scenario1_duration} ticks from first instruction to completion")
print(f"Scenario 2 (parallel): {scenario2_duration} ticks from instructions to completion")

if scenario2_duration < scenario1_duration - 2:
    print(f"\n❌ POTENTIAL BUG: Parallel instruction completed {scenario1_duration - scenario2_duration} ticks faster!")
    print("This suggests instructed people may be moving too fast when multiple groups are instructed.")
else:
    print(f"\n✓ Movement speed seems consistent (difference: {abs(scenario1_duration - scenario2_duration)} ticks)")
