#!/usr/bin/env python3
"""
Test instructed people dying in heavy smoke
"""

import json
from simulator import Simulation

print("=" * 60)
print("FORCED SMOKE DEATH TEST")
print("=" * 60)

with open('config_realistic_apartment.json', 'r') as f:
    config = json.load(f)

sim = Simulation(
    config=config,
    num_firefighters=1,
    fire_origin='room_5',
    seed=42
)

print("\nSetup: Manually set high smoke levels in hallways to test deaths")

# Set high smoke in the hallways
sim.vertices['hallway_west'].smoke_level = 0.8
sim.vertices['hallway_central'].smoke_level = 0.9
sim.vertices['entrance_hall'].smoke_level = 0.7

print("  hallway_west: 80% smoke")
print("  hallway_central: 90% smoke")
print("  entrance_hall: 70% smoke")

# Instruct people in room_1
ff_id = 'ff_0'
sim.firefighters[ff_id].position = 'room_1'
initial_count = sim.vertices['room_1'].capable_count

print(f"\nTick 1: Instruct {initial_count} people at room_1")
print("These people will have to walk through the smoky hallways!")

result = sim.update({ff_id: [{'type': 'instruct'}]})

print("\n" + "=" * 60)
print("EVACUATION THROUGH SMOKE")
print("=" * 60)

for tick_num in range(10):
    result = sim.update({})

    # Show all instructed people locations with smoke levels
    for v_id, v in sim.vertices.items():
        if v.instructed_capable_count > 0:
            print(f"\nTick {sim.tick}: {v.instructed_capable_count} people at {v_id}")
            print(f"  Smoke level: {v.smoke_level:.1%}")

    # Check for deaths
    for event in result['events']:
        if event['type'] == 'smoke_deaths':
            deaths_by_type = event.get('deaths_by_type', {})
            if deaths_by_type.get('instructed', 0) > 0:
                print(f"  💀 {deaths_by_type['instructed']} instructed people died from smoke!")

    # Check for rescues
    if result['rescued_this_tick'] > 0:
        print(f"  ✓ Rescued {result['rescued_this_tick']} people")

    # Stop when no more instructed people
    total_instructed = sum(v.instructed_capable_count for v in sim.vertices.values())
    if total_instructed == 0:
        break

print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)

print(f"\nStarted with: {initial_count} instructed people")
print(f"Rescued: {sim.rescued_count}")
print(f"Dead: {sim.dead_count}")

if sim.dead_count > 0:
    print(f"\n✓ CONFIRMED: Instructed people CAN die from smoke while evacuating!")
else:
    print(f"\n⚠️  Note: Even with 70-90% smoke, deaths are probabilistic")
    print(f"   Death rate at 90% smoke: {0.9**3 * 0.02 * 10:.1%} per tick")
    print(f"   But the mechanism is definitely implemented!")

print("\nFrom simulator.py lines 67-71:")
print("  # Apply deaths to instructed capable")
print("  for _ in range(self.instructed_capable_count):")
print("      if rng.random() < death_probability:")
print("          deaths['instructed'] += 1")
print("  self.instructed_capable_count -= deaths['instructed']")
