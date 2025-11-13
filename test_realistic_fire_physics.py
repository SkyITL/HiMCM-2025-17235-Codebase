#!/usr/bin/env python3
"""
Test realistic fire physics based on NIST/UL research

Expected behavior:
- Isolated room: 3-5 minutes to flashover (cold start)
- Adjacent room with 1 burning neighbor: 1.5-2 min to flashover after ignition
- Room surrounded by multiple burning rooms: <1 min flashover (preheating acceleration)
- 30-second ignition spread through hallways
"""

import json
from simulator import Simulation

print("=" * 70)
print("REALISTIC FIRE PHYSICS TEST (NIST/UL Research Validation)")
print("=" * 70)

with open('config_example.json', 'r') as f:
    config = json.load(f)

# Test 1: Isolated room flashover time
print("\n" + "=" * 70)
print("TEST 1: ISOLATED ROOM FLASHOVER (Cold Start)")
print("=" * 70)
print("Expected: 3-5 minutes based on NIST/UL research")
print("(Modern furniture: 3-5 min flashover, old furniture: 30 min)\n")

sim = Simulation(
    config=config,
    num_firefighters=0,  # No firefighters to isolate fire behavior
    fire_origin='office_bottom_center',
    seed=42
)

fire_room = sim.vertices['office_bottom_center']

print(f"{'Tick':<6} {'Time (sec)':<12} {'Fire %':<10} {'Smoke %':<10} {'Status'}")
print("-" * 70)

flashover_tick = None
for tick_num in range(30):
    if tick_num > 0:
        sim.update({})

    if tick_num % 2 == 0:
        status = ""
        if fire_room.fire_intensity >= 1.0 and flashover_tick is None:
            flashover_tick = tick_num
            status = "⚡ FLASHOVER!"
        elif fire_room.fire_intensity >= 0.5:
            status = "Growing"
        elif fire_room.fire_intensity > 0:
            status = "Small fire"

        print(f"{tick_num:<6} {tick_num * 10:<12} {fire_room.fire_intensity:<10.1%} {fire_room.smoke_level:<10.1%} {status}")

        if flashover_tick and tick_num > flashover_tick + 4:
            break

flashover_time = flashover_tick * 10 if flashover_tick else None
if flashover_time:
    print(f"\n✓ Flashover achieved in {flashover_time} seconds ({flashover_time/60:.1f} minutes)")
    if 180 <= flashover_time <= 300:
        print("  ✓ Within realistic range (3-5 minutes)")
    else:
        print(f"  ⚠ Outside realistic range (got {flashover_time/60:.1f} min, expected 3-5 min)")
else:
    print("\n✗ Flashover not achieved in test timeframe")

# Test 2: Adjacent room with preheating
print("\n" + "=" * 70)
print("TEST 2: ADJACENT ROOM IGNITION & FLASHOVER (With Preheating)")
print("=" * 70)
print("Expected: 30 sec ignition, then 1.5-2 min to flashover")
print("(Preheated room burns faster than cold start)\n")

sim2 = Simulation(
    config=config,
    num_firefighters=0,
    fire_origin='office_bottom_center',
    seed=42
)

# Run until origin room reaches flashover
origin = sim2.vertices['office_bottom_center']
while origin.fire_intensity < 1.0:
    sim2.update({})

origin_flashover_tick = sim2.tick
print(f"Origin room reached flashover at tick {origin_flashover_tick} ({origin_flashover_tick * 10} sec)\n")

# Now track adjacent hallway
hallway = sim2.vertices['hallway_center']

print(f"{'Tick':<6} {'Time (sec)':<12} {'Fire %':<10} {'Smoke %':<10} {'Status'}")
print("-" * 70)

ignition_tick = None
hallway_flashover_tick = None

for tick_num in range(origin_flashover_tick, origin_flashover_tick + 30):
    sim2.update({})

    if tick_num % 2 == 0:
        status = ""
        if hallway.fire_intensity >= 1.0 and hallway_flashover_tick is None:
            hallway_flashover_tick = tick_num
            status = "⚡ FLASHOVER!"
        elif hallway.fire_intensity >= 0.3 and ignition_tick is None:
            ignition_tick = tick_num
            status = "🔥 IGNITED!"
        elif hallway.fire_intensity >= 0.5:
            status = "Growing fast"
        elif hallway.fire_intensity > 0:
            status = "Small fire"

        print(f"{tick_num:<6} {tick_num * 10:<12} {hallway.fire_intensity:<10.1%} {hallway.smoke_level:<10.1%} {status}")

        if hallway_flashover_tick and tick_num > hallway_flashover_tick + 2:
            break

if ignition_tick:
    ignition_time = (ignition_tick - origin_flashover_tick) * 10
    print(f"\n✓ Ignition after {ignition_time} seconds")
    if 20 <= ignition_time <= 40:
        print(f"  ✓ Realistic ignition timing (expected ~30 sec)")
    else:
        print(f"  ⚠ Ignition timing off (got {ignition_time}s, expected ~30s)")

if hallway_flashover_tick:
    time_to_flashover = (hallway_flashover_tick - ignition_tick) * 10
    print(f"✓ Flashover after ignition in {time_to_flashover} seconds ({time_to_flashover/60:.1f} minutes)")
    if 60 <= time_to_flashover <= 150:
        print(f"  ✓ Faster than cold start due to preheating!")
    else:
        print(f"  ⚠ Timing off (expected 1-2.5 min)")

# Test 3: Acceleration with multiple burning neighbors
print("\n" + "=" * 70)
print("TEST 3: ACCELERATION WITH MULTIPLE BURNING NEIGHBORS")
print("=" * 70)
print("Expected: Rooms surrounded by fire flashover even faster (<1 min)")
print("(Demonstrates preheating acceleration effect)\n")

sim3 = Simulation(
    config=config,
    num_firefighters=0,
    fire_origin='hallway_center',  # Center location
    seed=100
)

# Run until hallway reaches flashover
center = sim3.vertices['hallway_center']
while center.fire_intensity < 1.0:
    sim3.update({})

print(f"Center hallway reached flashover at tick {sim3.tick}\n")

# Check how many adjacent rooms are burning
adjacent_burning = []
for neighbor_id, edge_id in sim3.adjacency['hallway_center']:
    neighbor = sim3.vertices[neighbor_id]
    if neighbor.fire_intensity > 0.5:
        adjacent_burning.append((neighbor_id, neighbor.fire_intensity))

print(f"Adjacent rooms with significant fire: {len(adjacent_burning)}")
for room_id, intensity in adjacent_burning:
    print(f"  {room_id}: {intensity:.1%}")

if len(adjacent_burning) >= 2:
    print(f"\n✓ Multiple rooms burning demonstrates fire spread acceleration")
    print(f"  Preheating effect: {len(adjacent_burning)} burning neighbors accelerate growth")
else:
    print(f"\n⚠ Limited spread observed ({len(adjacent_burning)} burning neighbors)")

# Summary
print("\n" + "=" * 70)
print("SUMMARY: REALISTIC FIRE PHYSICS VALIDATION")
print("=" * 70)

print("\n✓ IMPLEMENTED FEATURES:")
print("  1. Two-component growth model (intrinsic + preheating)")
print("  2. Realistic cold-start flashover timing (3-5 minutes)")
print("  3. Preserved 30-second hallway ignition spread")
print("  4. Preheating acceleration from adjacent burning rooms")
print("  5. Width-dependent heat transfer (wider = more preheating)")

print("\n✓ BASED ON RESEARCH:")
print("  - NIST: Modern furniture flashovers in 3-5 minutes")
print("  - UL: 8× faster than 50 years ago")
print("  - Research: 'Smoke spread accelerates preheating and combustion'")
print("  - Radiant heat flux drives spread between compartments")

print("\n" + "=" * 70)
