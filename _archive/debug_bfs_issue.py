#!/usr/bin/env python3
"""
Debug why bfs_next_step returns None when _bfs_distance shows room is reachable.
"""

import json
import sys
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel
from pathfinding import bfs_next_step


def main():
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin='room_10',
        seed=50
    )

    model = OptimalRescueModel(fire_priority_weight=0.0)

    # Run to tick 60 where it gets stuck
    for tick in range(61):
        state = sim.read()
        old_stdout = sys.stdout
        sys.stdout = open('/dev/null', 'w')
        actions = model.get_actions(state)
        sys.stdout = old_stdout
        sim.update(actions)

    # Now at tick 60, check pathfinding
    state = sim.read()
    graph = state['graph']

    print("Tick 60 - Pathfinding Debug")
    print("=" * 80)

    for ff_id, ff_data in state['firefighters'].items():
        ff_pos = ff_data['position']
        print(f"\n{ff_id} at {ff_pos}:")

        # Check unvisited rooms
        all_rooms = {
            v_id for v_id, v_data in graph['vertices'].items()
            if v_data['type'] == 'room'
        }
        visited = model.sweep_coordinator.globally_visited
        unvisited = all_rooms - visited

        print(f"  Unvisited rooms: {sorted(list(unvisited))}")

        # Test bfs_next_step for each unvisited room
        for room in sorted(list(unvisited))[:3]:  # Check first 3
            dist = model.sweep_coordinator._bfs_distance(ff_pos, room, graph)
            next_step = bfs_next_step(ff_pos, room, graph)

            print(f"\n  Target: {room}")
            print(f"    _bfs_distance: {dist}")
            print(f"    bfs_next_step: {next_step}")

            if dist < float('inf') and next_step is None:
                print(f"    ⚠️  BUG: Room is reachable but bfs_next_step returns None!")

if __name__ == '__main__':
    main()
