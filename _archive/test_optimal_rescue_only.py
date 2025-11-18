#!/usr/bin/env python3
"""
Test script for optimal rescue algorithm visualization - Phase 2 only.

This script bypasses Phase 1 (exploration) and jumps directly to Phase 2
(optimal rescue) by:
1. Setting all rooms as visited
2. Setting all occupants to incapable (no capable people)
3. Giving the model perfect information from the start

This allows focused testing of the optimal rescue algorithm without
waiting for exploration phase.
"""

import json
from simulator import Simulation
from optimal_rescue_model import OptimalRescueModel
from visualizer import EvacuationVisualizer


class LoggingModelWrapper:
    """
    Wraps model to add detailed logging of all decisions and actions.

    This helps debug why firefighters may not be responding.
    """

    def __init__(self, inner_model):
        self.inner_model = inner_model
        self.tick_count = 0

    def get_actions(self, state):
        """Generate actions with detailed logging."""
        # Full logging only for first tick in Phase 2 (before incrementing tick)
        if self.inner_model.phase == 'optimal_rescue' and self.tick_count == 0:
            print(f"\n{'='*70}")
            print(f"TICK {self.tick_count} - PHASE 2 START (DETAILED)")
            print(f"{'='*70}")

            # Log firefighter states
            print("\nFirefighter States:")
            for ff_id, ff_state in state['firefighters'].items():
                print(f"  {ff_id}: pos={ff_state['position']}, "
                      f"carrying={ff_state['carrying_incapable']}/{ff_state['max_carry_capacity']}")

            # Log discovered occupants
            discovered = state['discovered_occupants']
            total_incapable = sum(occ['incapable'] for occ in discovered.values())
            print(f"\nTotal incapable: {total_incapable}")

            # Log item assignments (from ff_plans)
            ff_plans = self.inner_model.coordinator.ff_plans
            print("\nChosen Item Assignments:")
            for ff_id, plans in ff_plans.items():
                print(f"\n  {ff_id}: {len(plans)} items assigned")
                total_time = 0
                total_people = 0
                for idx, plan in enumerate(plans):
                    item = plan.item
                    people = sum(item['vector'].values())
                    total_people += people
                    total_time += item['time']

                    # Format vector nicely
                    vector_str = ', '.join([f"{room}:{count}" for room, count in item['vector'].items()])

                    print(f"    {idx+1}. Rescue {people} from [{vector_str}]")
                    print(f"       Route: {item['entry_exit']} → {' → '.join(item['visit_sequence'])} → {item['drop_exit']}")
                    print(f"       Time: {item['time']:.1f}s, Value: {item['value']:.3f}")

                print(f"  {ff_id} total: {total_people} people, ~{total_time:.0f}s estimated")

            # Calculate total assignment metrics
            all_items = [item for plans in ff_plans.values() for plan in plans for item in [plan.item]]
            total_assigned = sum(sum(item['vector'].values()) for item in all_items)
            print(f"\n  Grand total: {total_assigned} people assigned for rescue")
            print("="*70)

        # Compact logging for subsequent ticks
        elif self.inner_model.phase == 'optimal_rescue':
            print(f"\nTick {self.tick_count}:", end=" ")
            # Show firefighter positions briefly
            for ff_id, ff_state in state['firefighters'].items():
                print(f"{ff_id}@{ff_state['position']}(carry={ff_state['carrying_incapable']})", end=" ")

        # Get actions from inner model
        actions = self.inner_model.get_actions(state)

        # Increment tick counter AFTER getting actions
        self.tick_count += 1

        # Log actions generated (compact)
        if self.inner_model.phase == 'optimal_rescue':
            print("\n  Actions:", end=" ")
            for ff_id, action_list in actions.items():
                if action_list:
                    action_strs = [f"{a['type'].replace('pick_up_incapable', 'pickup').replace('drop_off', 'drop')}" +
                                  (f"({a.get('count', '')})" if 'count' in a else f"→{a.get('target', '')}")
                                  for a in action_list]
                    print(f"{ff_id}:[{', '.join(action_strs)}]", end=" ")

        return actions

    @property
    def phase(self):
        """Expose phase for visualization."""
        return self.inner_model.phase


def setup_rescue_only_scenario(config_path: str, incapable_per_room: int = 2):
    """
    Load and modify config for rescue-only testing.

    Args:
        config_path: Path to JSON configuration
        incapable_per_room: Base number of incapable people per room (will vary)

    Returns:
        Modified config dict
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Modify occupancy: only incapable people, VARIED distribution
    rooms = [v for v in config['vertices'] if v['type'] == 'room']

    print(f"Setting up {len(rooms)} rooms with varied incapable counts...")

    config['occupancy_probabilities'] = {}

    # Create varied occupancy (not all multiples of 3)
    import random
    random.seed(42)  # Deterministic variation

    total_incapable = 0
    for idx, room in enumerate(rooms):
        room_id = room['id']

        # Vary between incapable_per_room-1 to incapable_per_room+2
        # This creates mix: 2, 3, 4, 5, etc.
        variation = random.randint(-1, 2)
        count = max(1, incapable_per_room + variation)  # At least 1

        config['occupancy_probabilities'][room_id] = {
            'capable': {'min': 0, 'max': 0},  # NO capable people
            'incapable': {'min': count, 'max': count}
        }

        total_incapable += count
        print(f"  {room_id}: {count} incapable")

    print(f"Total incapable across all rooms: {total_incapable}")

    return config


class RescueOnlyModel:
    """
    Wrapper that forces immediate Phase 2 activation with perfect information.

    This bypasses exploration by:
    - Marking all rooms as visited
    - Forcing phase transition immediately
    """

    def __init__(self, k_capacity=None, use_lp=False):
        self.inner_model = OptimalRescueModel(k_capacity, use_lp)
        self.first_call = True

    def get_actions(self, state):
        """
        Get actions, forcing Phase 2 on first call.
        """
        if self.first_call:
            print("\n" + "="*70)
            print("FORCING PHASE 2 - Skipping Exploration")
            print("="*70)

            # Mark all rooms as visited for all firefighters
            all_rooms = [
                v_id for v_id, v_data in state['graph']['vertices'].items()
                if v_data['type'] == 'room'
            ]

            # Modify state to make all rooms discovered
            for ff_id in state['firefighters']:
                state['firefighters'][ff_id]['visited_vertices'] = all_rooms.copy()

            # Add all rooms to discovered_occupants with their actual counts
            # (Normally only visible after visiting, but we're giving perfect info)
            if not state['discovered_occupants']:
                print("Injecting perfect occupant information...")
                # We need to get this from the actual simulation
                # The model will discover it automatically when we mark rooms as visited

            self.first_call = False

        return self.inner_model.get_actions(state)


def run_rescue_only_test(
    config_path: str,
    incapable_per_room: int = 3,
    use_lp: bool = False,
    visualize: bool = True
):
    """
    Run rescue-only test with visualization.

    Args:
        config_path: Path to base configuration
        incapable_per_room: Number of incapable people per room
        use_lp: Use LP solver vs greedy
        visualize: Show pygame visualization
    """
    print("="*70)
    print(f"Optimal Rescue Phase 2 Test (Incapable={incapable_per_room} per room)")
    print("="*70)

    # Setup scenario
    config = setup_rescue_only_scenario(config_path, incapable_per_room)

    # Extract parameters
    ff_params = config.get('firefighter_params', {})
    num_firefighters = ff_params.get('num_firefighters', 2)

    fire_params = config.get('fire_params', {})
    fire_origin = fire_params.get('origin', 'room_1')

    print(f"\nConfiguration:")
    print(f"  Fire origin: {fire_origin}")
    print(f"  Firefighters: {num_firefighters}")
    print(f"  Incapable per room: {incapable_per_room}")
    print(f"  Rooms: {len([v for v in config['vertices'] if v['type'] == 'room'])}")

    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=num_firefighters,
        fire_origin=fire_origin,
        seed=42
    )

    # CRITICAL: Mark all rooms as visited for all firefighters
    # This gives perfect information from the start
    all_rooms = [v_id for v_id, v in sim.vertices.items() if v.type == 'room']

    for ff in sim.firefighters.values():
        ff.visited_vertices.update(all_rooms)

    print(f"  All {len(all_rooms)} rooms marked as visited (perfect information)")

    # Create model
    model = OptimalRescueModel(use_lp=use_lp)

    # Get initial stats
    initial_stats = sim.get_stats()
    total_incapable = sum(
        v.incapable_count for v in sim.vertices.values() if v.type == 'room'
    )

    print(f"\nInitial State:")
    print(f"  Total incapable: {total_incapable}")
    print(f"  Capable: 0 (all set to incapable)")
    print(f"  Firefighters: {num_firefighters} (k=3 capacity each)")

    if visualize:
        print("\nStarting visualization...")
        print("Controls:")
        print("  SPACE: Pause/Resume")
        print("  RIGHT ARROW: Step forward (when paused)")
        print("  LEFT ARROW: Step backward (when paused)")
        print("  R: Reset")
        print("  Q/ESC: Quit")
        print("\nWatch for Phase 2 transition in first few ticks!")

        # Create wrapper model with logging
        logged_model = LoggingModelWrapper(model)

        viz = EvacuationVisualizer(width=1400, height=900, manual_mode=False)
        viz.paused = False  # Auto-run
        viz.run(sim, logged_model)
    else:
        # Run headless
        print("\nRunning simulation (headless)...")
        max_ticks = 1000

        for tick in range(max_ticks):
            state = sim.read()
            actions = model.get_actions(state)
            results = sim.update(actions)

            stats = sim.get_stats()

            if stats['remaining'] == 0:
                print(f"  All occupants evacuated or deceased at tick {tick}")
                break

            if tick % 50 == 0:
                print(f"  Tick {tick}: {stats['rescued']} rescued, {stats['dead']} dead, {stats['remaining']} remaining")
                print(f"    Model phase: {model.phase}")

    # Print final statistics
    print("\n" + "="*70)
    print("FINAL STATISTICS")
    print("="*70)

    final_stats = sim.get_stats()
    print(f"Total ticks: {final_stats['tick']}")
    print(f"Total time: {final_stats['time_minutes']:.2f} minutes")
    print(f"Rescued: {final_stats['rescued']}")
    print(f"Dead: {final_stats['dead']}")
    print(f"Remaining: {final_stats['remaining']}")

    if final_stats['rescued'] + final_stats['dead'] > 0:
        survival_rate = final_stats['rescued'] / (final_stats['rescued'] + final_stats['dead']) * 100
        print(f"Survival rate: {survival_rate:.1f}%")

    print("\n" + "="*70)

    return final_stats


def main():
    """Main entry point."""
    import sys

    # Default config
    config_path = '/Users/skyliu/Downloads/mall1withoccupants.json'

    # Parse arguments
    use_lp = '--lp' in sys.argv
    no_viz = '--no-viz' in sys.argv
    visualize = not no_viz

    # Incapable per room
    incapable_per_room = 3
    for arg in sys.argv:
        if arg.startswith('--incapable='):
            incapable_per_room = int(arg.split('=')[1])

    # Config file
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        config_path = sys.argv[1]

    print("""
╔════════════════════════════════════════════════════════════════════╗
║          OPTIMAL RESCUE ALGORITHM - PHASE 2 ONLY TEST             ║
╚════════════════════════════════════════════════════════════════════╝

This test skips exploration (Phase 1) and jumps directly to optimal
rescue (Phase 2) by:
  • Setting ALL occupants to incapable (no capable people)
  • Giving model perfect information (all rooms pre-discovered)
  • Forcing phase transition on first tick

This allows focused visualization of the optimal rescue algorithm.
""")

    stats = run_rescue_only_test(
        config_path,
        incapable_per_room=incapable_per_room,
        use_lp=use_lp,
        visualize=visualize
    )

    print("\nTest complete!")


if __name__ == '__main__':
    main()
