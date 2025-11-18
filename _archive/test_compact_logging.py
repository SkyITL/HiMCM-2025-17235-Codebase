#!/usr/bin/env python3
"""Quick test to show compact logging for just first 30 ticks."""

import json
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel
import sys
sys.path.insert(0, '/Users/skyliu/HiMCM2025')
from test_optimal_rescue_only import setup_rescue_only_scenario, LoggingModelWrapper

# Load and setup config
config = setup_rescue_only_scenario('/Users/skyliu/Downloads/mall1withoccupants.json', incapable_per_room=3)

# Create simulation
sim = Simulation(config=config, num_firefighters=2, fire_origin='room_14', seed=42)

# Mark all rooms as visited (perfect information)
all_rooms = [v_id for v_id, v in sim.vertices.items() if v.type == 'room']
for ff in sim.firefighters.values():
    ff.visited_vertices.update(all_rooms)

# Create model with logging wrapper
model = OptimalRescueModel(use_lp=False)
logged_model = LoggingModelWrapper(model)

print("\n" + "="*70)
print("RUNNING FIRST 30 TICKS WITH COMPACT LOGGING")
print("="*70)

# Run 30 ticks
for tick in range(30):
    state = sim.read()
    actions = logged_model.get_actions(state)
    results = sim.update(actions)

print("\n" + "="*70)
print("SIMULATION STOPPED AT TICK 30")
print("="*70)

stats = sim.get_stats()
print(f"Rescued: {stats['rescued']}, Dead: {stats['dead']}, Remaining: {stats['remaining']}")
