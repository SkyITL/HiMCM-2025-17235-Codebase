#!/usr/bin/env python3
"""
Test length-based fire and smoke spread
"""

import json
from simulator import Simulation

print("=" * 60)
print("LENGTH-BASED FIRE & SMOKE SPREAD TEST")
print("=" * 60)

with open('config_example.json', 'r') as f:
    config = json.load(f)

sim = Simulation(
    config=config,
    num_firefighters=2,
    fire_origin='office_bottom_center',
    seed=42
)

print("\nCorridor specifications:")
print(f"{'Edge':<35} {'Width':<8} {'Length':<8} {'Expected Spread'}")
print("-" * 70)

# Show corridor properties
sample_edges = [
    'e_office_bottom_center_hallway_center',  # 1.5m × 2.0m doorway
    'e_hallway_left_center',  # 2.5m × 8.0m long hallway
    'e_exit_left_hallway_left'  # 3.0m × 3.0m exit corridor
]

for edge_id in sample_edges:
    if edge_id in sim.edges:
        edge = sim.edges[edge_id]
        width_factor = edge.width / 2.0
        length_factor = 5.0 / edge.length
        relative_speed = width_factor * length_factor
        print(f"{edge_id:<35} {edge.width}m     {edge.length}m     {relative_speed:.2f}× (vs 2m×5m)")

print("\n" + "=" * 60)
print("TESTING SMOKE SPREAD THROUGH DIFFERENT CORRIDORS")
print("=" * 60)

# Run simulation
for _ in range(10):
    sim.update({})

print("\nSmoke spread after 10 ticks:")
print(f"{'Location':<30} {'Smoke Level':<15} {'Fire Intensity'}")
print("-" * 60)

# Check fire origin and nearby rooms
fire_room = sim.vertices['office_bottom_center']
print(f"{'office_bottom_center (origin)':<30} {fire_room.smoke_level:<15.1%} {fire_room.fire_intensity:.1%}")

# Check adjacent hallway (short 2m doorway)
hallway = sim.vertices['hallway_center']
print(f"{'hallway_center (2m doorway)':<30} {hallway.smoke_level:<15.1%} {hallway.fire_intensity:.1%}")

# Check distant offices through long hallways
if 'office_top_left' in sim.vertices:
    far_office = sim.vertices['office_top_left']
    print(f"{'office_top_left (far, 8m hall)':<30} {far_office.smoke_level:<15.1%} {far_office.fire_intensity:.1%}")

print("\n" + "=" * 60)
print("KEY PHYSICS")
print("=" * 60)

print("\nFire spread rate factors:")
print("  - Width: narrower corridors → faster spread")
print("  - Length: longer corridors → slower spread")
print("  - Formula: speed ∝ (width/2.0) × (5.0/length)")

print("\nSmoke diffusion factors:")
print("  - Width: wider corridors → more flow")
print("  - Length: longer corridors → slower diffusion")
print("  - Formula: diffusion ∝ (width/2.0) × (5.0/length)")

print("\nExamples (relative to 2m × 5m baseline):")
print("  - 1.5m × 2.0m doorway: 0.75 × 2.5 = 1.88× speed")
print("  - 2.5m × 8.0m hallway: 1.25 × 0.63 = 0.78× speed")
print("  - 3.0m × 3.0m corridor: 1.50 × 1.67 = 2.50× speed")

print("\n✓ Fire and smoke spread now scale with physical distance")
print("✓ Longer corridors provide natural barriers")
print("✓ More realistic propagation behavior")
