#!/usr/bin/env python3
"""Test carrying penalty doubling."""

import json
from simulator import Simulation

config_path = '/Users/skyliu/Downloads/mall1withoccupants.json'
with open(config_path, 'r') as f:
    config = json.load(f)

sim = Simulation(config=config, num_firefighters=1, fire_origin='room_1', seed=42)
ff = sim.firefighters['ff_0']

# Find a path to test
neighbors = [n for n, _ in sim.adjacency[ff.position]]
if len(neighbors) >= 2:
    # Test movement unloaded
    target1 = neighbors[0]
    action1 = {'type': 'move', 'target': target1}
    success1, _, cost_unloaded = sim._execute_action(ff, action1)
    
    print(f"Movement from {neighbors[0]} (area={sim.vertices[neighbors[0]].area:.1f}m²)")
    print(f"  Unloaded cost: {cost_unloaded:.2f}")
    
    # Reset and test with carrying
    ff.position = neighbors[0]  # Back to start
    ff.carrying_incapable = 2
    
    target2 = neighbors[1] if len(neighbors) > 1 else neighbors[0]
    # Move back
    ff.position = 'exit_1'
    action2 = {'type': 'move', 'target': neighbors[0]}
    success2, _, cost_loaded = sim._execute_action(ff, action2)
    
    print(f"  Loaded cost (carrying {ff.carrying_incapable}): {cost_loaded:.2f}")
    print(f"  Ratio: {cost_loaded/cost_unloaded:.2f}x")
    print(f"  Expected: 2.00x (halved speed)")
    
    if abs(cost_loaded/cost_unloaded - 2.0) < 0.01:
        print("\n✓ Carrying penalty working correctly!")
    else:
        print("\n✗ Carrying penalty not doubling cost")

print("\nTest complete!")
