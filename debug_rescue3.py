#!/usr/bin/env python3
"""Debug tick 4 specifically - why no drop off?"""

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

# Run to tick 4
for tick in range(5):
    state = sim.read()
    actions = model.get_actions(state)
    results = sim.update(actions)

# Now at tick 4, inspect ff_0
print("\n" + "="*70)
print("TICK 4 - FF_0 STATE")
print("="*70)

state = sim.read()
ff_state = state['firefighters']['ff_0']
plan = model.coordinator._get_current_plan('ff_0')

print(f"Position: {ff_state['position']}")
print(f"Carrying: {ff_state['carrying_incapable']}/{ff_state['max_carry_capacity']}")
print(f"\nPlan details:")
print(f"  Drop exit: {plan.drop_exit}")
print(f"  Current path idx: {plan.current_path_idx}")
print(f"  Full path: {plan.full_path}")
print(f"  Full path length: {len(plan.full_path)}")

print(f"\nCondition checks:")
print(f"  current_pos == plan.drop_exit: {ff_state['position']} == {plan.drop_exit} = {ff_state['position'] == plan.drop_exit}")
print(f"  carrying > 0: {ff_state['carrying_incapable']} > 0 = {ff_state['carrying_incapable'] > 0}")
print(f"  at_pickup_location: {plan.at_pickup_location(ff_state['position'])}")

print(f"\nPredicted action:")
if plan.at_pickup_location(ff_state['position']):
    print("  -> PICKUP (Case 1)")
elif ff_state['position'] == plan.drop_exit and ff_state['carrying_incapable'] > 0:
    print("  -> DROP OFF (Case 2)")
else:
    print("  -> MOVE (Case 3)")
