#!/usr/bin/env python3
"""
Test script to verify corridor occupant display
"""

import json
from simulator import Simulation

# Run a quick simulation and check corridor occupants
with open('config_example.json', 'r') as f:
    config = json.load(f)

sim = Simulation(
    config=config,
    num_firefighters=2,
    fire_origin='office_bottom_center',
    seed=42
)

# Move firefighters to rooms and instruct people
print("Initial state:")
for vertex_id, vertex in sim.vertices.items():
    if vertex.type == 'room' and (vertex.capable_count > 0 or vertex.incapable_count > 0):
        print(f"  {vertex_id}: C={vertex.capable_count}, I={vertex.incapable_count}")

# Move ff_0 to a room with people
ff_id = 'ff_0'
sim.update({ff_id: [{'type': 'move', 'target': 'hallway_left'}]})
sim.update({ff_id: [{'type': 'move', 'target': 'office_top_left'}]})

# Instruct people
print(f"\nInstructing people at office_top_left...")
sim.update({ff_id: [{'type': 'instruct'}]})

print("\nAfter instructing - checking corridors:")
for vertex_id, vertex in sim.vertices.items():
    if vertex.type in ['hallway', 'stairwell'] and vertex.instructed_capable_count > 0:
        print(f"  {vertex_id}: →{vertex.instructed_capable_count} people in transit")

# Run a few more ticks to see people move
for i in range(3):
    sim.update({})
    print(f"\nTick {sim.tick} - corridors with people:")
    for vertex_id, vertex in sim.vertices.items():
        if vertex.type in ['hallway', 'stairwell'] and vertex.instructed_capable_count > 0:
            print(f"  {vertex_id}: →{vertex.instructed_capable_count}")

print(f"\nRescued so far: {sim.rescued_count}")
print("\n✓ Corridor display test complete!")
print("Run 'python3 demo_visualizer.py auto' to see the visual representation")
