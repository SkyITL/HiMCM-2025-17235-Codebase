#!/usr/bin/env python3
"""Quick debug script to see what's happening in first few ticks."""

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

# Run a few ticks with detailed logging
for tick in range(5):
    print(f"\n{'='*70}")
    print(f"TICK {tick}")
    print('='*70)

    state = sim.read()

    # Log phase
    print(f"Phase: {model.phase}")
    print(f"Phase switched: {model.phase_switched}")

    # Log firefighter positions
    for ff_id, ff_state in state['firefighters'].items():
        print(f"  {ff_id}: pos={ff_state['position']}, carrying={ff_state['carrying_incapable']}/{ff_state['max_carry_capacity']}")

    # Log discovered occupants
    discovered = state['discovered_occupants']
    total_incapable = sum(occ['incapable'] for occ in discovered.values())
    print(f"Discovered incapable: {total_incapable}")

    # If in Phase 2, log coordinator
    if model.phase == 'optimal_rescue':
        status = model.coordinator.get_status()
        print("\nCoordinator status:")
        for ff_id, s in status.items():
            print(f"  {ff_id}: {s}")

    # Get actions
    actions = model.get_actions(state)

    print(f"\nActions generated:")
    for ff_id, action_list in actions.items():
        print(f"  {ff_id}: {action_list}")

    # Update
    results = sim.update(actions)
    print(f"\nUpdate results:")
    for ff_id, result_list in results.items():
        print(f"  {ff_id}: {result_list}")
