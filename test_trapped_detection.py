#!/usr/bin/env python3
"""
Test trapped firefighter detection and room explosion handling.
"""

import json
import sys
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


def main():
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Test with 2 firefighters on one of the previously failing seeds
    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin='room_10',
        seed=42
    )

    model = OptimalRescueModel(fire_priority_weight=0.0)

    print("Testing trapped firefighter detection and room explosion handling")
    print("=" * 80)

    max_ticks = 1000
    for tick in range(max_ticks):
        state = sim.read()

        # Get actions
        actions = model.get_actions(state)

        # Update simulation
        results = sim.update(actions)

        # Print phase transitions
        if model.phase == 'optimal_rescue' and tick > 0 and hasattr(model, 'phase_switched'):
            if model.phase_switched and tick < 200:
                stats = sim.get_stats()
                print(f"\nTick {tick}: Phase transition to rescue")
                print(f"  Remaining occupants: {stats['remaining']}")
                model.phase_switched = False  # Reset flag

        # Print replanning events
        if hasattr(model, 'replan_count') and model.replan_count > 0:
            # Only print if replan count increased
            if not hasattr(main, 'last_replan_count'):
                main.last_replan_count = 0

            if model.replan_count > main.last_replan_count:
                print(f"\nTick {tick}: Replanning event #{model.replan_count}")
                main.last_replan_count = model.replan_count

        # Check completion
        stats = sim.get_stats()
        if stats['remaining'] == 0:
            print(f"\n✓ Simulation complete at tick {tick}")
            print(f"  Rescued: {stats['rescued']}")
            print(f"  Dead: {stats['dead']}")
            print(f"  Total replans: {model.replan_count}")
            return

        # Check timeout
        if tick >= max_ticks - 1:
            print(f"\n⚠️  Timeout at {max_ticks} ticks")
            print(f"  Remaining: {stats['remaining']}")
            print(f"  Rescued: {stats['rescued']}")
            print(f"  Dead: {stats['dead']}")

            # Check if firefighters are stuck
            for ff_id, ff_state in state['firefighters'].items():
                ff_actions = actions.get(ff_id, [])
                print(f"  {ff_id} at {ff_state['position']}: {len(ff_actions)} actions")
                if not ff_actions and model.phase == 'optimal_rescue':
                    # Check if trapped
                    trapped = model._detect_trapped_firefighters(state)
                    if ff_id in trapped:
                        print(f"    → TRAPPED! Cannot reach targets")
            return


if __name__ == '__main__':
    main()
