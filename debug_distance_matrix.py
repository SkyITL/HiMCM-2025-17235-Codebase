#!/usr/bin/env python3
"""Debug distance matrix contents during optimization."""

import json
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel

# Load config
with open('/Users/skyliu/Downloads/mall1withoccupants.json', 'r') as f:
    config = json.load(f)

# Setup rescue-only scenario
rooms = [v for v in config['vertices'] if v['type'] == 'room']
config['occupancy_probabilities'] = {}
for room in rooms:
    config['occupancy_probabilities'][room['id']] = {
        'capable': {'min': 0, 'max': 0},
        'incapable': {'min': 3, 'max': 3}
    }

# Create sim
sim = Simulation(config=config, num_firefighters=2, fire_origin='room_14', seed=42)

# Mark all rooms as visited
all_rooms = [v_id for v_id, v in sim.vertices.items() if v.type == 'room']
for ff in sim.firefighters.values():
    ff.visited_vertices.update(all_rooms)

# Create model
model = OptimalRescueModel(use_lp=False)

# Trigger phase transition (this runs preprocessing)
state = sim.read()

# Manually call preprocessing to inspect
model.optimizer.preprocess_distances(state)

print("\n" + "="*70)
print("DISTANCE MATRIX INSPECTION")
print("="*70)

# Check what's in distance_matrix
print(f"\nKeys in distance_matrix: {list(model.optimizer.distance_matrix.keys())[:10]}...")
print(f"Total keys: {len(model.optimizer.distance_matrix)}")

# Check if exit_2 is in the matrix
if 'exit_2' in model.optimizer.distance_matrix:
    print(f"\nexit_2 IS in distance_matrix")
    exit_2_dists = model.optimizer.distance_matrix['exit_2']
    print(f"  exit_2 can reach {len(exit_2_dists)} vertices")

    # Check specific vertices
    if 'intersection_19' in exit_2_dists:
        dist, path = exit_2_dists['intersection_19']
        print(f"  exit_2 -> intersection_19: dist={dist}, path={path}")
    else:
        print(f"  intersection_19 NOT in exit_2 distances")

    if 'room_15' in exit_2_dists:
        dist, path = exit_2_dists['room_15']
        print(f"  exit_2 -> room_15: dist={dist}, path={path}")
    else:
        print(f"  room_15 NOT in exit_2 distances")
else:
    print(f"\nexit_2 NOT in distance_matrix!")

# Check if room_15 -> exit_2 exists
if 'room_15' in model.optimizer.distance_matrix:
    print(f"\nroom_15 IS in distance_matrix")
    room_15_dists = model.optimizer.distance_matrix['room_15']
    if 'exit_2' in room_15_dists:
        dist, path = room_15_dists['exit_2']
        print(f"  room_15 -> exit_2: dist={dist}, path={path}")
    else:
        print(f"  exit_2 NOT reachable from room_15")
