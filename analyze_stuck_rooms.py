#!/usr/bin/env python3
"""
Analyze which rooms still have occupants when firefighters get stuck.
"""

import json
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


def analyze_seed(seed, fire_origin, max_ticks=500):
    """Analyze what rooms have occupants when stuck."""
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    print(f"\n{'='*80}")
    print(f"ANALYZING SEED {seed} (fire: {fire_origin})")
    print('='*80)

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=fire_origin,
        seed=seed
    )

    model = OptimalRescueModel(fire_priority_weight=0.0)

    last_positions = {}
    stuck_count = 0

    for tick in range(max_ticks):
        state = sim.read()
        actions = model.get_actions(state)

        # Detect stuck (no movement)
        all_stuck = True
        for ff_id, ff_data in state['firefighters'].items():
            current_pos = ff_data['position']
            if ff_id in last_positions and last_positions[ff_id] != current_pos:
                all_stuck = False
            last_positions[ff_id] = current_pos

        if all_stuck and tick > 10:
            stuck_count += 1
            if stuck_count == 20:  # Report after 20 ticks stuck
                stats = sim.get_stats()
                print(f"\n⚠️  STUCK at tick {tick}")
                print(f"   Phase: {model.phase}")
                print(f"   Remaining: {stats['remaining']}")
                print(f"   Rescued: {stats['rescued']}")
                print(f"   Dead: {stats['dead']}")
                print()

                # Show firefighter status
                for ff_id, ff_data in state['firefighters'].items():
                    ff_actions = actions.get(ff_id, [])
                    action_str = ', '.join([a['type'] for a in ff_actions]) if ff_actions else 'NONE'

                    queue_len = 0
                    if ff_id in model.coordinator.ff_plans:
                        current_idx = model.coordinator.ff_current_idx.get(ff_id, 0)
                        queue_len = len(model.coordinator.ff_plans[ff_id]) - current_idx

                    print(f"   {ff_id}: pos={ff_data['position'][-30:]:30s} | queue={queue_len} | actions=[{action_str}]")

                print()
                print("Analyzing rooms with occupants:")

                # Find all rooms with occupants
                rooms_with_occupants = []
                for v_id, v_data in state['graph']['vertices'].items():
                    if v_data['type'] == 'room':
                        num_occupants = len(v_data.get('occupants', []))
                        if num_occupants > 0:
                            vertex_exists = v_data.get('exists', True)
                            rooms_with_occupants.append({
                                'room': v_id,
                                'count': num_occupants,
                                'exists': vertex_exists
                            })

                if rooms_with_occupants:
                    print(f"\n   Found {len(rooms_with_occupants)} rooms with occupants:")
                    for room_info in sorted(rooms_with_occupants, key=lambda x: x['room']):
                        exists_str = "EXISTS" if room_info['exists'] else "EXPLODED"
                        print(f"      {room_info['room']}: {room_info['count']} occupants [{exists_str}]")

                # Check if these rooms are reachable
                print()
                print("Checking reachability from firefighter positions:")
                from pathfinding import bfs_next_step

                for ff_id, ff_data in state['firefighters'].items():
                    ff_pos = ff_data['position']
                    print(f"\n   {ff_id} at {ff_pos}:")

                    for room_info in rooms_with_occupants:
                        if not room_info['exists']:
                            print(f"      {room_info['room']}: UNREACHABLE (room exploded)")
                            continue

                        next_step = bfs_next_step(ff_pos, room_info['room'], state['graph'])
                        if next_step:
                            print(f"      {room_info['room']}: REACHABLE")
                        else:
                            print(f"      {room_info['room']}: UNREACHABLE (no path)")

                # Check what's in the coordinator
                print()
                print("Coordinator status:")
                if hasattr(model, 'coordinator') and model.coordinator:
                    print(f"   Items in coordinator:")
                    for ff_id in state['firefighters'].keys():
                        if ff_id in model.coordinator.ff_plans:
                            plans = model.coordinator.ff_plans[ff_id]
                            current_idx = model.coordinator.ff_current_idx.get(ff_id, 0)
                            remaining = len(plans) - current_idx
                            print(f"      {ff_id}: {remaining} items remaining (current_idx={current_idx}, total={len(plans)})")

                            # Show remaining items
                            if remaining > 0:
                                for i in range(current_idx, len(plans)):
                                    item = plans[i]
                                    print(f"         Item {i}: vector={item.vector}, rescued={item.rescued_so_far}")

                return False
        else:
            stuck_count = 0

        sim.update(actions)

        stats = sim.get_stats()
        if stats['remaining'] == 0:
            print(f"\n✓ Completed at tick {tick}")
            return True

    print(f"\n✗ Timeout at {max_ticks} ticks")
    return False


def main():
    # Test seed 6 which gets stuck
    analyze_seed(6, 'room_2', max_ticks=500)


if __name__ == '__main__':
    main()
