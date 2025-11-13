#!/usr/bin/env python3
"""
Visualizer for testgraph.json
"""

import json
from simulator import Simulation
from visualizer import EvacuationVisualizer


class SimpleGreedyModel:
    """
    Simple greedy AI model using instruct/carry mechanics.
    Firefighters move to rooms, instruct capable people, and carry incapable people to exits.
    """

    def get_actions(self, state):
        """Generate actions based on current state (2 actions per firefighter)"""
        actions = {}

        for ff_id, ff_state in state['firefighters'].items():
            ff_actions = []

            # Generate first action
            action1 = self._get_single_action(ff_state, state)
            if action1:
                ff_actions.append(action1)

                # Simulate the first action's effect on state
                simulated_state = self._simulate_action(ff_state, action1, state)

                # Generate second action based on simulated state
                action2 = self._get_single_action(simulated_state, state)
                if action2:
                    ff_actions.append(action2)

            actions[ff_id] = ff_actions

        return actions

    def _get_single_action(self, ff_state, state):
        """Generate a single action for a firefighter"""
        current_pos = ff_state['position']
        vertex = state['graph']['vertices'][current_pos]
        carrying = ff_state['carrying_incapable']

        # Get neighbors
        neighbors = self._get_neighbors(current_pos, state)

        # Get occupants at current position
        occupants = state['discovered_occupants'].get(current_pos, {'capable': 0, 'incapable': 0, 'instructed': 0})

        # Priority 1: If carrying someone and at exit, drop off
        if carrying > 0 and vertex['type'] in ['exit', 'window_exit']:
            return {'type': 'drop_off'}

        # Priority 2: If carrying someone, move toward exit
        if carrying > 0:
            path_to_exit = self._bfs_to_exit(current_pos, state)
            if path_to_exit and len(path_to_exit) > 1:
                next_vertex = path_to_exit[1]
                return {'type': 'move', 'target': next_vertex}

        # Priority 3: If current vertex has capable people, instruct them
        if occupants['capable'] > 0:
            return {'type': 'instruct'}

        # Priority 4: If current vertex has incapable people, pick one up
        if occupants['incapable'] > 0:
            return {'type': 'pick_up_incapable'}

        # Priority 5: Check if any neighbor has occupants that need help
        for neighbor in neighbors:
            neighbor_occupants = state['discovered_occupants'].get(neighbor, {'capable': 0, 'incapable': 0, 'instructed': 0})
            if neighbor_occupants['capable'] > 0 or neighbor_occupants['incapable'] > 0:
                # Move to that vertex to help next turn
                return {'type': 'move', 'target': neighbor}

        # Priority 6: If no nearby occupants, move toward unvisited rooms
        visited = set(ff_state['visited_vertices'])
        nearest_room = self._find_nearest_unvisited_room(current_pos, visited, state)
        if nearest_room:
            path = self._bfs_path(current_pos, nearest_room, state)
            if path and len(path) > 1:
                return {'type': 'move', 'target': path[1]}

        # Priority 7: If all rooms visited, stay put or explore
        if neighbors:
            return {'type': 'move', 'target': neighbors[0]}

        return None

    def _simulate_action(self, ff_state, action, state):
        """Simulate the effect of an action on firefighter state"""
        simulated_state = ff_state.copy()

        if action['type'] == 'move':
            simulated_state['position'] = action['target']
        elif action['type'] == 'pick_up_incapable':
            simulated_state['carrying_incapable'] = ff_state['carrying_incapable'] + 1
        elif action['type'] == 'drop_off':
            simulated_state['carrying_incapable'] = 0

        return simulated_state

    def _get_neighbors(self, vertex_id, state):
        """Get neighboring vertices"""
        neighbors = []
        for edge_id, edge in state['graph']['edges'].items():
            if edge['vertex_a'] == vertex_id:
                neighbors.append(edge['vertex_b'])
            elif edge['vertex_b'] == vertex_id:
                neighbors.append(edge['vertex_a'])
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

    def _bfs_path(self, start, goal, state):
        """BFS to find shortest path between two vertices"""
        from collections import deque

        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == goal:
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


def visualize_testgraph():
    """Run visualizer with testgraph.json"""
    print("="*60)
    print("TESTGRAPH VISUALIZATION")
    print("="*60)

    # Load testgraph
    with open('/Users/skyliu/Downloads/testgraph.json', 'r') as f:
        graph_data = json.load(f)

    # Create config with occupancy and fire parameters
    config = {
        "description": "Visualization of testgraph",
        "vertices": graph_data["vertices"],
        "edges": graph_data["edges"],
        "occupancy_probabilities": {},
        "fire_params": {
            "origin": None,
            "initial_smoke_level": 0.3
        }
    }

    # Add occupancy probabilities for rooms
    for vertex in config["vertices"]:
        if vertex["type"] == "room":
            config["occupancy_probabilities"][vertex["id"]] = {
                "capable": 0.05,
                "incapable": 0.005
            }

    # Find a room to set as fire origin
    room_vertices = [v for v in config["vertices"] if v["type"] == "room"]
    if room_vertices:
        config["fire_params"]["origin"] = room_vertices[0]["id"]
        print(f"Fire origin: {config['fire_params']['origin']}")

    print(f"Graph: {len(config['vertices'])} vertices, {len(config['edges'])} edges")
    print("\nControls:")
    print("  - Play/Pause to start/stop")
    print("  - Speed +/- to adjust simulation speed")
    print("  - Step for single tick advancement")
    print("="*60 + "\n")

    # Create simulation
    sim = Simulation(
        config=config,
        num_firefighters=3,
        fire_origin=config['fire_params']['origin'],
        seed=42
    )

    # Run with AI model
    model = SimpleGreedyModel()
    viz = EvacuationVisualizer(manual_mode=False)
    viz.paused = False  # Start running
    viz.run(sim, model)


if __name__ == '__main__':
    visualize_testgraph()
