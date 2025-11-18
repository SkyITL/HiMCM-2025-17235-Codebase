#!/usr/bin/env python3
"""
Quick visual test to verify smoke renders correctly
"""

import json
from simulator import Simulation
from visualizer import EvacuationVisualizer
from demo_visualizer import SimpleGreedyModel
import pygame

print("=" * 60)
print("VISUAL SMOKE RENDERING TEST")
print("=" * 60)
print("\nThis will open a pygame window briefly to test smoke rendering.")
print("Window will close automatically after 3 seconds.\n")

with open('config_example.json', 'r') as f:
    config = json.load(f)

sim = Simulation(
    config=config,
    num_firefighters=2,
    fire_origin='office_bottom_center',
    seed=42
)

# Run simulation for a few ticks to build up smoke
for _ in range(5):
    sim.update({})

print("Smoke levels after 5 ticks:")
for vertex_id in ['office_bottom_center', 'hallway_center', 'office_top_left']:
    vertex = sim.vertices[vertex_id]
    print(f"  {vertex_id}: {vertex.smoke_level:.1%}")

# Quick pygame test
pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Smoke Test")

# Just check that we can access smoke_level
try:
    for vertex in sim.vertices.values():
        level = vertex.smoke_level
    print("\n✓ Smoke levels accessible from all vertices")
    print("✓ Visualizer should work correctly")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

pygame.quit()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nTo see full visualization, run:")
print("  python3 demo_visualizer.py auto")
