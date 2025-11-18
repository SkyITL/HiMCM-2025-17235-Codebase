#!/usr/bin/env python3
"""Debug why _plan_to_actions returns empty list."""

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

# Run tick 0 to trigger phase transition
state = sim.read()
actions = model.get_actions(state)
results = sim.update(actions)

# Now on tick 1, inspect the coordinator's plan
print("\n" + "="*70)
print("INSPECTING COORDINATOR PLANS")
print("="*70)

state = sim.read()

for ff_id in ['ff_0', 'ff_1']:
    ff_state = state['firefighters'][ff_id]
    plan = model.coordinator._get_current_plan(ff_id)

    print(f"\n{ff_id}:")
    print(f"  Position: {ff_state['position']}")
    print(f"  Carrying: {ff_state['carrying_incapable']}/{ff_state['max_carry_capacity']}")

    if plan:
        print(f"  Plan exists: YES")
        print(f"  Vector: {plan.vector}")
        print(f"  Visit sequence: {plan.visit_sequence}")
        print(f"  Full path: {plan.full_path}")
        print(f"  Entry exit: {plan.entry_exit}")
        print(f"  Drop exit: {plan.drop_exit}")
        print(f"  Current path idx: {plan.current_path_idx}")
        print(f"  Rescued so far: {plan.rescued_so_far}")

        # Test conditions
        current_pos = ff_state['position']
        print(f"\n  Condition checks:")
        print(f"    At pickup location? {plan.at_pickup_location(current_pos)}")
        print(f"    At drop exit? {current_pos == plan.drop_exit}")
        print(f"    Current target: {plan.get_current_target()}")
        print(f"    Target != current_pos? {plan.get_current_target() != current_pos}")

        # Manually run _plan_to_actions logic
        print(f"\n  Manual action generation:")
        target = plan.get_current_target()
        print(f"    target = {target}")
        print(f"    current_pos = {current_pos}")

        if target and target != current_pos:
            print(f"    -> Should generate MOVE to {target}")
        elif target == current_pos:
            print(f"    -> Target equals current pos, no move generated")
        else:
            print(f"    -> No target available")
    else:
        print(f"  Plan exists: NO")
