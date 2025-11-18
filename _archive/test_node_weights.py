#!/usr/bin/env python3
"""Quick test to verify node weights and carrying penalty."""

import json
from simulator import Simulation

# Load config
config_path = '/Users/skyliu/Downloads/mall1withoccupants.json'
with open(config_path, 'r') as f:
    config = json.load(f)

# Create simple scenario
sim = Simulation(config=config, num_firefighters=1, fire_origin='room_1', seed=42)

# Get state
state = sim.read()

# Check a few room areas
print("Room areas:")
for room_id in ['room_1', 'room_10', 'room_17']:
    area = state['graph']['vertices'][room_id]['area']
    node_weight = (2.0 * area) ** 0.5
    print(f"  {room_id}: area={area:.1f}m², node_weight={node_weight:.2f}")

# Test movement cost
ff = sim.firefighters['ff_0']
print(f"\nFirefighter at: {ff.position}")
print(f"Carrying: {ff.carrying_incapable}")

# Simulate movement action (from exit to adjacent vertex)
# Move to first adjacent vertex
neighbors = [n for n, _ in sim.adjacency[ff.position]]
if neighbors:
    target = neighbors[0]
    print(f"\nMoving from {ff.position} to {target}...")
    
    action = {'type': 'move', 'target': target}
    success, msg, cost = sim._execute_action(ff, action)
    
    print(f"  Success: {success}")
    print(f"  Movement cost (unloaded): {cost:.2f}")
    
    # Now try carrying someone
    ff.carrying_incapable = 2
    ff.position = neighbors[0] if len(neighbors) > 1 else ff.position  # Reset position
    
    if len(neighbors) > 1:
        target2 = neighbors[1]
        action2 = {'type': 'move', 'target': target2}
        success2, msg2, cost2 = sim._execute_action(ff, action2)
        
        print(f"\nMoving while carrying {ff.carrying_incapable} people:")
        print(f"  Movement cost (loaded): {cost2:.2f}")
        print(f"  Penalty ratio: {cost2/cost:.2f}x (should be ~2.0x)")

print("\nTest complete!")
