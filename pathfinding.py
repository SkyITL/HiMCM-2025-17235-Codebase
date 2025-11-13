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
    only_existing_edges: bool = True
) -> Dict[str, Tuple[float, List[str]]]:
    """
    Dijkstra's algorithm from single source to all vertices.

    Args:
        graph: State graph from sim.read()
        start: Starting vertex ID
        only_existing_edges: If True, skip burned edges

    Returns:
        {vertex_id: (distance, path)}
        where path = [start, ..., vertex_id]

    IMPORTANT: distance[start][start] = 0 (can rescue multiple from same room)
    """
    vertices = graph['vertices']
    edges = graph['edges']

    # Build adjacency list
    adjacency = {}
    for v_id in vertices:
        adjacency[v_id] = []

    for edge_id, edge_data in edges.items():
        if only_existing_edges and not edge_data['exists']:
            continue  # Skip burned edges

        va = edge_data['vertex_a']
        vb = edge_data['vertex_b']
        weight = 1.0  # Each edge has unit weight (1 meter, 1 tick to traverse)

        adjacency[va].append((vb, weight))
        adjacency[vb].append((va, weight))

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
        for neighbor, weight in adjacency.get(current, []):
            if neighbor in visited:
                continue

            new_dist = current_dist + weight

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
    rooms_only: bool = True
) -> Dict[str, Dict[str, Tuple[float, List[str]]]]:
    """
    Compute shortest paths between all pairs of vertices.

    Args:
        graph: State graph from sim.read()
        rooms_only: If True, only compute for room vertices (optimization)

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
        all_pairs[source] = dijkstra_single_source(graph, source)

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
    distance_matrix: Dict[str, Dict[str, Tuple[float, List[str]]]],
    room_priorities: Dict[str, int]
) -> Dict:
    """
    Compute complete item details for a given vector and visiting sequence.

    Args:
        vector: {room_id: count} - how many to rescue from each room
        visit_sequence: [room1, room2, ...] - order to visit rooms
        entry_exit: Exit to start from
        drop_exit: Exit to drop off at
        distance_matrix: Precomputed shortest paths
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
    # Build full path by stitching shortest paths
    full_path = [entry_exit]
    total_distance = 0.0
    current = entry_exit

    for room in visit_sequence:
        if current == room:
            # Same room - distance is 0, path doesn't change
            continue

        dist, path = distance_matrix[current][room]
        total_distance += dist
        full_path.extend(path[1:])  # Skip current (already in path)
        current = room

    # Add path to drop exit
    if current != drop_exit:
        dist, path = distance_matrix[current][drop_exit]
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
