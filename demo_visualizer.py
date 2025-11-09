"""
Demo script for the Emergency Evacuation Visualizer
Shows how to use both manual and auto modes.
"""

import json
from simulator import Simulation
from visualizer import EvacuationVisualizer


class SimpleGreedyModel:
    """
    Simple greedy AI model for demonstration.
    Firefighters move to nearest unvisited room, pick up occupants, return to exit.
    """

    def get_actions(self, state):
        """Generate actions based on current state"""
        actions = {}

        for ff_id, ff_state in state['firefighters'].items():
            ff_actions = []
            current_pos = ff_state['position']

            # Get adjacency from graph
            neighbors = self._get_neighbors(current_pos, state)

            # Strategy: If escorting, go to exit. Otherwise, go to rooms.
            if ff_state['escorting_count'] > 0:
                # Check if already at exit - if so, drop off immediately
                vertex = state['graph']['vertices'][current_pos]
                if vertex['type'] in ['exit', 'window_exit']:
                    ff_actions.append({'type': 'drop_off'})
                else:
                    # Find path to exit and move
                    move_target = self._find_exit_direction(current_pos, neighbors, state)
                    if move_target:
                        ff_actions.append({'type': 'move', 'target': move_target})

            else:
                # Check current room for occupants
                if current_pos in state['discovered_occupants']:
                    if state['discovered_occupants'][current_pos] > 0:
                        ff_actions.append({'type': 'pick_up', 'count': ff_state['capacity']})

                # Move to unvisited room
                visited = set(ff_state['visited_vertices'])
                move_target = None

                # Prefer unvisited rooms
                for neighbor in neighbors:
                    if neighbor not in visited:
                        vertex = state['graph']['vertices'][neighbor]
                        if vertex['type'] == 'room' and not vertex['is_burned']:
                            move_target = neighbor
                            break

                # Otherwise move to any unvisited vertex
                if not move_target:
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            move_target = neighbor
                            break

                if move_target:
                    ff_actions.append({'type': 'move', 'target': move_target})

            actions[ff_id] = ff_actions

        return actions

    def _get_neighbors(self, vertex_id, state):
        """Get neighboring vertices"""
        neighbors = []
        for edge_id, edge_data in state['graph']['edges'].items():
            if not edge_data['exists']:
                continue

            if edge_data['vertex_a'] == vertex_id:
                neighbors.append(edge_data['vertex_b'])
            elif edge_data['vertex_b'] == vertex_id:
                neighbors.append(edge_data['vertex_a'])

        return neighbors

    def _find_exit_direction(self, current_pos, neighbors, state):
        """Find neighbor that leads toward exit"""
        for neighbor in neighbors:
            vertex = state['graph']['vertices'][neighbor]
            if vertex['type'] in ['exit', 'window_exit']:
                return neighbor
            elif vertex['type'] == 'hallway':
                return neighbor
        return neighbors[0] if neighbors else None


def demo_manual_mode():
    """Run visualizer in manual control mode"""
    print("="*60)
    print("MANUAL CONTROL MODE DEMO")
    print("="*60)
    print("\nControls:")
    print("  1. Click on a firefighter (orange circle) to select it")
    print("     - If multiple firefighters at same spot, click again to cycle through them")
    print("     - Look for 'x2' or 'x3' badge showing how many are at that location")
    print("  2. Click on adjacent rooms to QUEUE movement")
    print("  3. Click 'Pick Up (5)' to QUEUE pickup action")
    print("  4. Click 'Drop Off' to QUEUE drop-off action")
    print("  5. Click 'Step' to EXECUTE queued actions and advance time by 1 tick")
    print("\nNew Features:")
    print("  - Fog of war: Unvisited rooms show '?' instead of occupant count")
    print("  - Time ONLY advances when you click 'Step'")
    print("  - Actions are queued and shown in the status bar")
    print("  - Reduced smoke death rate - more time to rescue people!")
    print("\nTips:")
    print("  - Numbers in blue circles show occupant count (only for visited rooms)")
    print("  - '?' means you haven't visited that room yet")
    print("  - Yellow 'x2' badge means multiple firefighters at that spot - click to cycle")
    print("  - Smoke darkens over time (gray overlay with percentage)")
    print("  - Red circles are burned rooms")
    print("  - Dashed lines are blocked corridors")
    print("="*60 + "\n")

    with open('config_example.json', 'r') as f:
        config = json.load(f)

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=config.get('fire_params', {}).get('origin', 'office_bottom_center'),
        seed=42
    )

    viz = EvacuationVisualizer(manual_mode=True)
    viz.run(sim)


def demo_auto_mode():
    """Run visualizer with simple AI model"""
    print("="*60)
    print("AUTO MODE DEMO (Simple Greedy AI)")
    print("="*60)
    print("\nThe AI will automatically:")
    print("  1. Move to nearest unvisited rooms")
    print("  2. Pick up occupants")
    print("  3. Return to exits to drop them off")
    print("\nControls:")
    print("  - Play/Pause to start/stop")
    print("  - Speed +/- to adjust simulation speed")
    print("  - Step for single tick advancement")
    print("\nWatch the stats at the bottom to see performance!")
    print("="*60 + "\n")

    with open('config_example.json', 'r') as f:
        config = json.load(f)

    sim = Simulation(
        config=config,
        num_firefighters=2,
        fire_origin=config.get('fire_params', {}).get('origin', 'office_bottom_center'),
        seed=42
    )

    model = SimpleGreedyModel()
    viz = EvacuationVisualizer(manual_mode=False)
    viz.paused = False  # Start running
    viz.run(sim, model)


def demo_comparison():
    """
    Run two simulations side by side for comparison.
    (This would require split-screen implementation - placeholder for now)
    """
    print("Comparison mode not yet implemented.")
    print("Run manual mode, note your score, then run auto mode to compare!")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Emergency Evacuation Visualizer Demo")
        print("\nUsage:")
        print("  python3 demo_visualizer.py manual    # Manual control mode")
        print("  python3 demo_visualizer.py auto      # Auto mode with AI")
        print("  python3 demo_visualizer.py compare   # Comparison mode")
        print()
        sys.exit(0)

    mode = sys.argv[1].lower()

    if mode == 'manual':
        demo_manual_mode()
    elif mode == 'auto':
        demo_auto_mode()
    elif mode == 'compare':
        demo_comparison()
    else:
        print(f"Unknown mode: {mode}")
        print("Use: manual, auto, or compare")
