#!/usr/bin/env python3
"""
Debug seed 50 in detail - track what firefighters are doing when stuck.
"""

import json
import sys
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


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

    print("Seed 50 Debug - First 150 ticks")
    print("=" * 80)

    for tick in range(150):
        state = sim.read()

        # Suppress model output
        old_stdout = sys.stdout
        sys.stdout = open('/dev/null', 'w')
        actions = model.get_actions(state)
        sys.stdout = old_stdout

        # Track firefighter positions and actions
        if tick % 10 == 0 or tick < 20:
            print(f"\nTick {tick}:")
            for ff_id, ff_data in state['firefighters'].items():
                ff_pos = ff_data['position']
                ff_action = actions.get(ff_id, [])
                action_str = ', '.join([f"{a['type']}" + (f"→{a.get('target', '')[-10:]}" if a['type'] == 'move' else '') for a in ff_action])
                print(f"  {ff_id}: pos={ff_pos[-20:]:20s} | actions=[{action_str}]")

            if model.sweep_coordinator and model.sweep_initialized:
                visited = len(model.sweep_coordinator.globally_visited)
                print(f"  Rooms visited: {visited}/22")

        sim.update(actions)

        # Check if stuck (no actions)
        if tick > 50:
            all_empty = all(len(acts) == 0 for acts in actions.values())
            if all_empty:
                print(f"\n⚠️  STUCK at tick {tick} - all firefighters returning empty actions!")

                # Check unvisited rooms
                all_rooms = {
                    v_id for v_id, v_data in state['graph']['vertices'].items()
                    if v_data['type'] == 'room'
                }
                visited = model.sweep_coordinator.globally_visited if model.sweep_coordinator else set()
                unvisited = all_rooms - visited

                print(f"   Unvisited rooms ({len(unvisited)}): {sorted(list(unvisited))}")

                # Check reachability from each firefighter
                for ff_id, ff_data in state['firefighters'].items():
                    ff_pos = ff_data['position']
                    print(f"\n   {ff_id} at {ff_pos}:")

                    for room in sorted(list(unvisited))[:5]:  # Check first 5
                        dist = model.sweep_coordinator._bfs_distance(ff_pos, room, state['graph'])
                        print(f"      {room}: distance={dist}")

                break

    print("\nDone")


if __name__ == '__main__':
    main()
