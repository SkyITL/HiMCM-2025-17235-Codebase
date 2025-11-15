#!/usr/bin/env python3
"""
Debug stuck trials in detail - show what's happening when they get stuck.
"""

import json
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel


def debug_trial(seed, fire_origin, max_ticks=500):
    """Debug a single trial and show detailed status."""
    config_file = '/Users/skyliu/Downloads/mall1withoccupants.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    print(f"\n{'='*80}")
    print(f"DEBUGGING SEED {seed} (fire: {fire_origin})")
    print('='*80)

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=fire_origin,
        seed=seed
    )

    model = OptimalRescueModel(fire_priority_weight=0.0)

    last_replan_count = 0
    last_phase = 'exploration'
    stuck_count = 0
    last_positions = {}

    for tick in range(max_ticks):
        state = sim.read()
        actions = model.get_actions(state)

        # Detect phase changes
        if model.phase != last_phase:
            print(f"\n🔄 Tick {tick}: Phase changed to {model.phase}")
            last_phase = model.phase

        # Detect replans
        if model.replan_count > last_replan_count:
            stats = sim.get_stats()
            print(f"\n🔥 Tick {tick}: REPLAN #{model.replan_count} | Remaining: {stats['remaining']}")

            for ff_id, ff_data in state['firefighters'].items():
                ff_actions = actions.get(ff_id, [])
                action_str = ', '.join([a['type'] for a in ff_actions]) if ff_actions else 'NONE'
                print(f"   {ff_id}: {ff_data['position'][-30:]:30s} | [{action_str}]")

            last_replan_count = model.replan_count

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
                print(f"\n⚠️  Tick {tick}: STUCK FOR 20 TICKS")
                print(f"   Phase: {model.phase} | Remaining: {stats['remaining']}")

                for ff_id, ff_data in state['firefighters'].items():
                    ff_actions = actions.get(ff_id, [])
                    action_str = ', '.join([a['type'] for a in ff_actions]) if ff_actions else 'NONE'
                    queue_len = 0
                    if ff_id in model.coordinator.ff_plans:
                        current_idx = model.coordinator.ff_current_idx.get(ff_id, 0)
                        queue_len = len(model.coordinator.ff_plans[ff_id]) - current_idx

                    print(f"   {ff_id}: {ff_data['position'][-30:]:30s} | [{action_str:20s}] | queue={queue_len}")

                # Check unvisited rooms if in sweep
                if model.phase == 'exploration' and model.sweep_coordinator and model.sweep_initialized:
                    all_rooms = {
                        v_id for v_id, v_data in state['graph']['vertices'].items()
                        if v_data['type'] == 'room'
                    }
                    visited = model.sweep_coordinator.globally_visited
                    unvisited = all_rooms - visited
                    if unvisited:
                        print(f"   Unvisited rooms ({len(unvisited)}): {sorted(list(unvisited))[:5]}...")

                break  # Stop after detecting stuck
        else:
            stuck_count = 0

        sim.update(actions)

        stats = sim.get_stats()
        if stats['remaining'] == 0:
            print(f"\n✓ Tick {tick}: COMPLETED")
            print(f"   Rescued: {stats['rescued']} | Dead: {stats['dead']} | Replans: {model.replan_count}")
            return True

    stats = sim.get_stats()
    print(f"\n✗ Tick {tick}: TIMEOUT or STUCK")
    print(f"   Phase: {model.phase}")
    print(f"   Remaining: {stats['remaining']} | Rescued: {stats['rescued']} | Dead: {stats['dead']}")
    print(f"   Replans: {model.replan_count}")
    return False


def main():
    # Test both types of failures
    print("Testing failed trials...")

    # Sweep stuck (0 replans)
    debug_trial(6, 'room_2', max_ticks=300)

    # Rescue stuck (moderate replans)
    debug_trial(3, 'room_10', max_ticks=500)
    debug_trial(11, 'room_2', max_ticks=500)


if __name__ == '__main__':
    main()
