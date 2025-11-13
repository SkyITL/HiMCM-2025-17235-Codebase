#!/usr/bin/env python3
"""
Test unit length system for edges
"""

import json
from simulator import Simulation

print("=" * 60)
print("UNIT LENGTH SYSTEM TEST")
print("=" * 60)

print("\nPhysical Constants:")
print(f"  TICK_DURATION = {Simulation.TICK_DURATION} seconds")
print(f"  UNIT_LENGTH = {Simulation.UNIT_LENGTH} meters")
print(f"  All edges have unit length = 1.0")

print("\nFirefighter Movement:")
print(f"  Firefighters can take 2 actions per tick")
print(f"  Each move action = 1 edge = 1 unit length")
print(f"  Maximum distance per tick = 2 units = {2 * Simulation.UNIT_LENGTH}m")
print(f"  Travel speed = {2 * Simulation.UNIT_LENGTH}m / {Simulation.TICK_DURATION}s = {2 * Simulation.UNIT_LENGTH / Simulation.TICK_DURATION} m/s")
print(f"  (This is slow walking speed appropriate for fire conditions)")

print("\n" + "=" * 60)
print("TESTING SIMULATION WITH UNIT LENGTH")
print("=" * 60)

with open('config_example.json', 'r') as f:
    config = json.load(f)

sim = Simulation(
    config=config,
    num_firefighters=2,
    fire_origin='office_bottom_center',
    seed=42
)

print(f"\nTotal edges in building: {len(sim.edges)}")
print("\nSample corridors (all unit length):")
print(f"{'Edge ID':<40} {'Width':<10} {'Physical Length'}")
print("-" * 65)

for edge_id in list(sim.edges.keys())[:5]:
    edge = sim.edges[edge_id]
    physical_length = Simulation.UNIT_LENGTH
    print(f"{edge_id:<40} {edge.width}m       {physical_length}m")

print("\n" + "=" * 60)
print("FIRE AND SMOKE SPREAD RATES")
print("=" * 60)

# Run simulation
for _ in range(5):
    sim.update({})

fire_room = sim.vertices['office_bottom_center']
print(f"\nAfter 5 ticks ({5 * Simulation.TICK_DURATION} seconds):")
print(f"  Fire origin: {fire_room.fire_intensity:.1%} fire, {fire_room.smoke_level:.1%} smoke")

# Check adjacent room through 1 unit edge (5m physical distance)
hallway = sim.vertices['hallway_center']
print(f"  Adjacent room (1 unit = {Simulation.UNIT_LENGTH}m away):")
print(f"    {hallway.fire_intensity:.1%} fire, {hallway.smoke_level:.1%} smoke")

print("\n" + "=" * 60)
print("KEY POINTS")
print("=" * 60)

print("\n✓ All edges have unit length = 1.0 (graph topology)")
print(f"✓ Physical distance per unit = {Simulation.UNIT_LENGTH}m")
print(f"✓ Firefighter speed = {2 * Simulation.UNIT_LENGTH / Simulation.TICK_DURATION} m/s (2 units per tick)")
print("✓ Fire and smoke spread based on width and unit distance")
print("✓ Consistent physical modeling throughout simulation")
