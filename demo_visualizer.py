"""
Demo script for the Emergency Evacuation Visualizer
Shows how to use both manual and auto modes.
"""

import json
from simulator import Simulation
from visualizer import EvacuationVisualizer


class SimpleGreedyModel:
    """
    Simple greedy AI model using push-based mechanics.
    Firefighters move to rooms, discover occupants, and push them toward exits.
    """

    def get_actions(self, state):
        """Generate actions based on current state"""
        actions = {}

        for ff_id, ff_state in state['firefighters'].items():
            ff_actions = []
            current_pos = ff_state['position']
            vertex = state['graph']['vertices'][current_pos]

            # Get neighbors
            neighbors = self._get_neighbors(current_pos, state)

            # Priority 1: If current vertex has occupants, push them toward exit
            if current_pos in state['discovered_occupants'] and state['discovered_occupants'][current_pos] > 0:
                path_to_exit = self._bfs_to_exit(current_pos, state)
                if path_to_exit and len(path_to_exit) > 1:
                    next_vertex = path_to_exit[1]
                    ff_actions.append({'type': 'push', 'target': next_vertex, 'count': 999})

            # Priority 2: Check if any neighbor has occupants that need pushing
            has_nearby_occupants = False
            for neighbor in neighbors:
                if neighbor in state['discovered_occupants'] and state['discovered_occupants'][neighbor] > 0:
                    # Move to that vertex to push occupants next turn
                    ff_actions.append({'type': 'move', 'target': neighbor})
                    has_nearby_occupants = True
                    break

            # Priority 3: If no nearby occupants, move toward unvisited rooms
            if not has_nearby_occupants and not ff_actions:
                visited = set(ff_state['visited_vertices'])
                target_room = self._find_nearest_unvisited_room(current_pos, visited, state)

                if target_room:
                    path = self._bfs_path(current_pos, target_room, state)
                    if path and len(path) > 1:
                        next_vertex = path[1]
                        ff_actions.append({'type': 'move', 'target': next_vertex})
                else:
                    # All rooms visited - move to any unvisited vertex
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            ff_actions.append({'type': 'move', 'target': neighbor})
                            break

            actions[ff_id] = ff_actions

        return actions

    def _get_neighbors(self, vertex_id, state):
        """Get neighboring vertices that are accessible"""
        neighbors = []
        for edge_id, edge_data in state['graph']['edges'].items():
            if not edge_data['exists']:
                continue

            if edge_data['vertex_a'] == vertex_id:
                neighbors.append(edge_data['vertex_b'])
            elif edge_data['vertex_b'] == vertex_id:
                neighbors.append(edge_data['vertex_a'])

        return neighbors

    def _bfs_to_exit(self, start, state):
        """BFS to find shortest path to any exit"""
        from collections import deque

        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            current = path[-1]

            vertex = state['graph']['vertices'][current]
            if vertex['type'] in ['exit', 'window_exit']:
                return path

            for neighbor in self._get_neighbors(current, state):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        return None

    def _bfs_path(self, start, end, state):
        """BFS to find shortest path from start to end"""
        from collections import deque

        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == end:
                return path

            for neighbor in self._get_neighbors(current, state):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        return None

    def _find_nearest_unvisited_room(self, start, visited, state):
        """BFS to find nearest unvisited room"""
        from collections import deque

        queue = deque([start])
        seen = {start}

        while queue:
            current = queue.popleft()
            vertex = state['graph']['vertices'][current]

            # Found unvisited room
            if current not in visited and vertex['type'] == 'room' and not vertex['is_burned']:
                return current

            for neighbor in self._get_neighbors(current, state):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

        return None


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
