#!/usr/bin/env python3
"""
Pathfinding and routing algorithms for optimal rescue.

Provides:
- Dijkstra's algorithm for all-pairs shortest paths
- Item detail computation (complete paths with E² exit optimization)
- BFS for single-destination pathfinding
"""

import heapq
from typing import Dict, List, Tuple, Optional
from itertools import permutations


def dijkstra_single_source(
    graph: Dict,
    start: str,
    only_existing_edges: bool = True,
    carrying_penalty: float = 1.0
) -> Dict[str, Tuple[float, List[str]]]:
    """
    Dijkstra's algorithm from single source to all vertices.

    Uses node weights (sqrt(2*area) for diagonal traversal) and edge weights.
    Applies carrying penalty to total movement cost.

    Args:
        graph: State graph from sim.read()
        start: Starting vertex ID
        only_existing_edges: If True, skip burned edges
        carrying_penalty: Multiplier for movement cost (1.0 unloaded, 2.0 carrying)

    Returns:
        {vertex_id: (distance, path)}
        where path = [start, ..., vertex_id]

    IMPORTANT: distance[start][start] = 0 (can rescue multiple from same room)
    """
    vertices = graph['vertices']
    edges = graph['edges']

    # Build adjacency list with edge weights only (node weights added during traversal)
    adjacency = {}
    for v_id in vertices:
        adjacency[v_id] = []

    for edge_id, edge_data in edges.items():
        if only_existing_edges and not edge_data['exists']:
            continue  # Skip burned edges

        va = edge_data['vertex_a']
        vb = edge_data['vertex_b']
        edge_weight = 1.0  # Each edge has unit weight (1 meter)

        adjacency[va].append((vb, edge_weight))
        adjacency[vb].append((va, edge_weight))

    # Dijkstra's algorithm with heap
    distances = {v_id: float('inf') for v_id in vertices}
    distances[start] = 0.0

    predecessors = {v_id: None for v_id in vertices}

    # Priority queue: (distance, vertex_id)
    pq = [(0.0, start)]
    visited = set()

    while pq:
        current_dist, current = heapq.heappop(pq)

        if current in visited:
            continue

        visited.add(current)

        # Explore neighbors
        for neighbor, edge_weight in adjacency.get(current, []):
            if neighbor in visited:
                continue

            # Calculate total cost to move from current to neighbor
            # Cost = (node_weight_of_current + edge_weight) * carrying_penalty

            # Node weight: diagonal traversal time = sqrt(2 * area)
            current_node_data = vertices[current]
            current_area = current_node_data.get('area', 100.0)
            node_weight = (2.0 * current_area) ** 0.5

            # Total movement cost
            movement_cost = (node_weight + edge_weight) * carrying_penalty

            # New distance to neighbor
            new_dist = current_dist + movement_cost

            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                predecessors[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))

    # Reconstruct paths
    result = {}
    for v_id in vertices:
        if distances[v_id] == float('inf'):
            continue  # Unreachable

        # Build path by following predecessors
        path = []
        current = v_id
        while current is not None:
            path.append(current)
            current = predecessors[current]

        path.reverse()
        result[v_id] = (distances[v_id], path)

    return result


def dijkstra_all_pairs(
    graph: Dict,
    rooms_only: bool = True,
    carrying_penalty: float = 1.0
) -> Dict[str, Dict[str, Tuple[float, List[str]]]]:
    """
    Compute shortest paths between all pairs of vertices.

    Args:
        graph: State graph from sim.read()
        rooms_only: If True, only compute for room vertices (optimization)
        carrying_penalty: Multiplier for movement cost (1.0 unloaded, 2.0 carrying)

    Returns:
        {start_id: {goal_id: (distance, path)}}

    Time complexity: O(V × E log V) where V = number of vertices

    IMPORTANT: distance[i][i] = 0, path[i][i] = [i]
    This is critical for items that rescue multiple people from same room.
    """
    vertices = graph['vertices']

    # Filter to rooms if requested
    if rooms_only:
        sources = [v_id for v_id, v_data in vertices.items()
                  if v_data['type'] == 'room']
    else:
        sources = list(vertices.keys())

    all_pairs = {}

    for source in sources:
        all_pairs[source] = dijkstra_single_source(graph, source, carrying_penalty=carrying_penalty)

        # CRITICAL: Ensure self-distance is 0
        # This allows rescuing multiple people from the same room
        all_pairs[source][source] = (0.0, [source])

    return all_pairs


def bfs_next_step(
    current: str,
    goal: str,
    graph: Dict
) -> Optional[str]:
    """
    Find next adjacent vertex toward goal using BFS.
    Avoids burned edges.

    Args:
        current: Current vertex ID
        goal: Target vertex ID
        graph: State graph from sim.read()

    Returns:
        Next vertex ID to move to, or None if unreachable
    """
    if current == goal:
        return None  # Already at goal

    # BFS to find path
    vertices = graph['vertices']
    edges = graph['edges']

    # Build adjacency
    adjacency = {}
    for v_id in vertices:
        adjacency[v_id] = []

    for edge_data in edges.values():
        if not edge_data['exists']:
            continue  # Skip burned

        va = edge_data['vertex_a']
        vb = edge_data['vertex_b']
        adjacency[va].append(vb)
        adjacency[vb].append(va)

    # BFS
    queue = [current]
    visited = {current}
    predecessors = {current: None}

    found = False
    while queue:
        node = queue.pop(0)

        if node == goal:
            found = True
            break

        for neighbor in adjacency.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                predecessors[neighbor] = node
                queue.append(neighbor)

    if not found:
        return None  # Unreachable

    # Backtrack to find next step from current
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = predecessors[node]

    path.reverse()  # [current, ..., goal]

    if len(path) < 2:
        return None

    return path[1]  # Next step after current


def compute_optimal_item_for_vector(
    vector: Dict[str, int],
    visit_sequence: List[str],
    entry_exit: str,
    drop_exit: str,
    distance_unloaded: Dict[str, Dict[str, Tuple[float, List[str]]]],
    distance_loaded: Dict[str, Dict[str, Tuple[float, List[str]]]],
    room_priorities: Dict[str, int]
) -> Dict:
    """
    Compute complete item details for a given vector and visiting sequence.

    Uses incremental carrying logic:
    - Segments before picking up people use unloaded distances
    - Segments after picking up people use loaded distances

    Args:
        vector: {room_id: count} - how many to rescue from each room
        visit_sequence: [room1, room2, ...] - order to visit rooms
        entry_exit: Exit to start from
        drop_exit: Exit to drop off at
        distance_unloaded: Precomputed shortest paths (carrying_penalty=1.0)
        distance_loaded: Precomputed shortest paths (carrying_penalty=2.0)
        room_priorities: {room_id: priority} for value calculation

    Returns:
        {
            'vector': vector,
            'visit_sequence': visit_sequence,
            'entry_exit': entry_exit,
            'drop_exit': drop_exit,
            'full_path': [entry, ...rooms..., drop],
            'time': total_time,
            'value': priority_weighted_value / time,
            'people_rescued': sum(vector.values())
        }
    """
    # Build full path with incremental carrying load
    full_path = [entry_exit]
    total_distance = 0.0
    current = entry_exit
    current_carrying = 0

    for room in visit_sequence:
        if current == room:
            # Same room - distance is 0, path doesn't change
            # But still pick up people
            current_carrying += vector[room]
            continue

        # Choose distance matrix based on carrying state
        if current_carrying > 0:
            dist, path = distance_loaded[current][room]
        else:
            dist, path = distance_unloaded[current][room]

        total_distance += dist
        full_path.extend(path[1:])  # Skip current (already in path)
        current = room

        # Pick up people at this room
        current_carrying += vector[room]

    # Add path to drop exit (always carrying people at this point)
    if current != drop_exit:
        dist, path = distance_loaded[current][drop_exit]
        total_distance += dist
        full_path.extend(path[1:])

    # Calculate time (assume 1 tick per unit distance)
    time = total_distance

    # Calculate priority-weighted value
    total_priority_value = sum(
        vector[room] * room_priorities.get(room, 1)
        for room in vector
    )

    # Value density: priority-weighted rescues per unit time
    value_density = total_priority_value / max(time, 0.1)  # Avoid division by zero

    return {
        'vector': vector,
        'visit_sequence': visit_sequence,
        'entry_exit': entry_exit,
        'drop_exit': drop_exit,
        'full_path': full_path,
        'time': time,
        'value': value_density,
        'people_rescued': sum(vector.values())
    }


def find_exits(graph: Dict) -> List[str]:
    """
    Find all exit vertices in the graph.

    Args:
        graph: State graph from sim.read()

    Returns:
        List of exit vertex IDs
    """
    vertices = graph['vertices']
    exits = [v_id for v_id, v_data in vertices.items()
             if v_data['type'] in ['exit', 'window_exit']]
    return exits


def get_rooms_with_incapable(state: Dict) -> List[str]:
    """
    Get list of rooms that have incapable occupants.

    Args:
        state: Full state from sim.read()

    Returns:
        List of room IDs with incapable_count > 0
    """
    discovered = state['discovered_occupants']
    rooms = [room_id for room_id, occupants in discovered.items()
             if occupants['incapable'] > 0]
    return rooms
