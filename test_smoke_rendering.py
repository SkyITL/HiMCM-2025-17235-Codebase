#!/usr/bin/env python3
"""
Test smoke rendering
"""

import json
from simulator import Simulation

print("Testing smoke rendering...")

with open('config_example.json', 'r') as f:
    config = json.load(f)

sim = Simulation(
    config=config,
    num_firefighters=2,
    fire_origin='office_bottom_center',
    seed=42
)

# Run a few ticks
for _ in range(5):
    sim.update({})

# Check smoke properties
print("\nChecking vertex smoke properties:")
for vertex_id in ['office_bottom_center', 'hallway_center', 'office_top_left']:
    vertex = sim.vertices[vertex_id]
    print(f"\n{vertex_id}:")
    print(f"  smoke_amount: {vertex.smoke_amount:.2f} m³")
    print(f"  volume: {vertex.volume:.2f} m³")
    print(f"  smoke_level (property): {vertex.smoke_level:.2%}")

    # Test if property works
    try:
        level = vertex.smoke_level
        if level > 0.05:
            print(f"  ✓ Would render smoke overlay")
    except Exception as e:
        print(f"  ❌ ERROR accessing smoke_level: {e}")

print("\n✓ Test complete")
