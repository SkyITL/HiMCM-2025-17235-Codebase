#!/usr/bin/env python3
"""
Debug seed 0 which has 16 replans but times out.
"""

import json
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
        seed=0
    )

    model = OptimalRescueModel(fire_priority_weight=0.0)

    print("Debugging seed 0 - High replanning case")
    print("=" * 80)

    last_replan_count = 0
    for tick in range(1000):
        state = sim.read()
        actions = model.get_actions(state)

        # Detect replan events
        if model.replan_count > last_replan_count:
            stats = sim.get_stats()
            print(f"\nTick {tick}: REPLAN #{model.replan_count}")
            print(f"  Remaining: {stats['remaining']}")
            print(f"  Rescued: {stats['rescued']}")
            print(f"  Dead: {stats['dead']}")

            # Show firefighter status
            for ff_id, ff_state in state['firefighters'].items():
                ff_actions = actions.get(ff_id, [])
                action_str = ', '.join([f"{a['type']}" for a in ff_actions])
                queue_len = len(model.coordinator.ff_plans.get(ff_id, []))
                current_idx = model.coordinator.ff_current_idx.get(ff_id, 0)
                remaining_items = queue_len - current_idx
                print(f"    {ff_id}: pos={ff_state['position'][-20:]:20s} | actions=[{action_str:20s}] | queue={remaining_items}")

            last_replan_count = model.replan_count

        sim.update(actions)

        stats = sim.get_stats()
        if stats['remaining'] == 0:
            print(f"\n✓ Complete at tick {tick}")
            print(f"  Total replans: {model.replan_count}")
            return

    print(f"\n✗ Timeout at 1000 ticks")
    print(f"  Total replans: {model.replan_count}")
    print(f"  Remaining: {stats['remaining']}")
    print(f"  Rescued: {stats['rescued']}")


if __name__ == '__main__':
    main()
