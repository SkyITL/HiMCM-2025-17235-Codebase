#!/usr/bin/env python3
"""Debug graph structure and Dijkstra paths."""

import json
from simulator import Simulation
import pathfinding

# Load config
with open('/Users/skyliu/Downloads/mall1withoccupants.json', 'r') as f:
    config = json.load(f)

# Create sim
sim = Simulation(config=config, num_firefighters=2, fire_origin='room_14', seed=42)
state = sim.read()

graph = state['graph']

# Check edges near exit_2
print("="*70)
print("EDGES CONNECTED TO exit_2")
print("="*70)

exit_2_edges = []
for edge_id, edge_data in graph['edges'].items():
    if edge_data['vertex_a'] == 'exit_2' or edge_data['vertex_b'] == 'exit_2':
        print(f"{edge_id}: {edge_data['vertex_a']} <-> {edge_data['vertex_b']} (exists={edge_data['exists']})")
        exit_2_edges.append((edge_data['vertex_a'], edge_data['vertex_b']))

# Check edges near intersection_19
print("\n" + "="*70)
print("EDGES CONNECTED TO intersection_19")
print("="*70)

for edge_id, edge_data in graph['edges'].items():
    if edge_data['vertex_a'] == 'intersection_19' or edge_data['vertex_b'] == 'intersection_19':
        print(f"{edge_id}: {edge_data['vertex_a']} <-> {edge_data['vertex_b']} (exists={edge_data['exists']})")

# Now test Dijkstra from exit_2
print("\n" + "="*70)
print("DIJKSTRA FROM exit_2")
print("="*70)

distances = pathfinding.dijkstra_single_source(graph, 'exit_2')

# Check path to intersection_19
if 'intersection_19' in distances:
    dist, path = distances['intersection_19']
    print(f"\nexit_2 -> intersection_19:")
    print(f"  Distance: {dist}")
    print(f"  Path: {path}")
else:
    print(f"\nintersection_19 NOT REACHABLE from exit_2")

# Check path to room_15
if 'room_15' in distances:
    dist, path = distances['room_15']
    print(f"\nexit_2 -> room_15:")
    print(f"  Distance: {dist}")
    print(f"  Path: {path}")
else:
    print(f"\nroom_15 NOT REACHABLE from exit_2")

# List all reachable vertices from exit_2
print(f"\n" + "="*70)
print(f"ALL REACHABLE FROM exit_2 (total: {len(distances)})")
print("="*70)
for v_id, (dist, path) in list(distances.items())[:10]:
    print(f"  {v_id}: dist={dist}, path_length={len(path)}")
