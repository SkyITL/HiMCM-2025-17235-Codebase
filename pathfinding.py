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

    Uses zero node weights (all vertices) and unit edge weights (1.0 meter).
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
            # Cost = (node_weight_current + edge_weight) * carrying_penalty
            # We charge for: traversing FROM current to edge + edge traversal
            # Entering target vertex is free (you're at the door immediately)

            # Node weight for current: all vertices have zero weight
            # Only edges have weight (1 meter each)
            current_node_weight = 0.0

            # Total movement cost: exit current + edge (entering target is free)
            movement_cost = (current_node_weight + edge_weight) * carrying_penalty

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
    distance_matrix: Dict[str, Dict[str, Tuple[float, List[str]]]],
    room_priorities: Dict[str, int],
    k_capacity: int = 3,
    under_capacity_penalty: float = 0.1,
    fire_distances: Dict[str, float] = None,
    fire_priority_weight: float = 0.0
) -> Dict:
    """
    Compute complete item details for a given vector and visiting sequence.

    Uses incremental carrying logic:
    - Segments with carrying_count=0 use base distance (1× cost)
    - Segments with carrying_count>0 use 2× distance (carrying penalty)

    IMPORTANT: Carrying penalty is NOT applied to the entry→first_room segment
    because we haven't picked anyone up yet!

    Args:
        vector: {room_id: count} - how many to rescue from each room
        visit_sequence: [room1, room2, ...] - order to visit rooms
        entry_exit: Exit to start from
        drop_exit: Exit to drop off at
        distance_matrix: Precomputed shortest paths (pure geometric distances)
        room_priorities: {room_id: priority} for value calculation
        k_capacity: Maximum capacity (default 3)
        under_capacity_penalty: Penalty multiplier per person under k (default 0.1)
        fire_distances: {room_id: distance_to_fire} for proximity weighting (optional)
        fire_priority_weight: Multiplier for fire proximity (0.0 = disabled, higher = stronger)

    Returns:
        {
            'vector': vector,
            'visit_sequence': visit_sequence,
            'entry_exit': entry_exit,
            'drop_exit': drop_exit,
            'full_path': [entry, ...rooms..., drop],
            'time': total_time,
            'value': priority_weighted_value / time (with under-capacity penalty),
            'people_rescued': sum(vector.values()),
            'penalty_applied': penalty factor if < k, else 1.0
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

        # Check if path exists in distance matrix
        if current not in distance_matrix or room not in distance_matrix[current]:
            # Room is unreachable (likely due to burned edges)
            # Return None to signal invalid item
            return None

        # Get base geometric distance
        dist, path = distance_matrix[current][room]

        # Apply carrying penalty ONLY if currently carrying people
        if current_carrying > 0:
            dist *= 2.0  # Carrying penalty (halved speed)

        total_distance += dist
        full_path.extend(path[1:])  # Skip current (already in path)
        current = room

        # Pick up people at this room
        current_carrying += vector[room]

    # Add path to drop exit (always carrying people at this point)
    if current != drop_exit:
        # Check if path to exit exists
        if current not in distance_matrix or drop_exit not in distance_matrix[current]:
            # Exit unreachable from final room
            return None

        dist, path = distance_matrix[current][drop_exit]
        # Apply carrying penalty (we're always carrying at this point)
        dist *= 2.0
        total_distance += dist
        full_path.extend(path[1:])

    # Calculate time (assume 1 tick per unit distance)
    time = total_distance

    # Calculate priority-weighted value with optional fire proximity boost
    total_priority_value = 0.0
    for room in vector:
        people_count = vector[room]
        base_priority = room_priorities.get(room, 1)

        # Apply fire proximity multiplier if enabled
        if fire_distances and fire_priority_weight > 0.0:
            fire_dist = fire_distances.get(room, float('inf'))
            # Closer to fire = higher multiplier
            # Formula: priority × (1 + weight / (1 + distance))
            # At distance=0: multiplier = 1 + weight
            # At distance=∞: multiplier = 1
            proximity_boost = 1.0 + (fire_priority_weight / (1.0 + fire_dist))
            effective_priority = base_priority * proximity_boost
        else:
            effective_priority = base_priority

        total_priority_value += people_count * effective_priority

    # Value density: priority-weighted rescues per unit time
    value_density = total_priority_value / max(time, 0.1)  # Avoid division by zero

    # Apply under-capacity penalty
    people_rescued = sum(vector.values())
    penalty_factor = 1.0

    if people_rescued < k_capacity:
        shortage = k_capacity - people_rescued
        penalty_factor = 1.0 + (shortage * under_capacity_penalty)
        value_density = value_density / penalty_factor

    return {
        'vector': vector,
        'visit_sequence': visit_sequence,
        'entry_exit': entry_exit,
        'drop_exit': drop_exit,
        'full_path': full_path,
        'time': time,
        'value': value_density,
        'people_rescued': people_rescued,
        'penalty_applied': penalty_factor
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


def bfs_path_with_edges(
    start: str,
    goal: str,
    graph: Dict
) -> Tuple[Optional[List[str]], set]:
    """
    BFS pathfinding that returns both the path and edge IDs used.

    Args:
        start: Starting vertex ID
        goal: Target vertex ID
        graph: State graph from sim.read()

    Returns:
        (path, edge_ids) where:
        - path: List of vertex IDs from start to goal, or None if unreachable
        - edge_ids: Set of edge IDs used in the path
    """
    vertices = graph['vertices']
    edges = graph['edges']

    # Build adjacency with edge tracking
    adjacency = {}  # {vertex_id: [(neighbor, edge_id), ...]}
    for v_id in vertices:
        adjacency[v_id] = []

    for edge_id, edge_data in edges.items():
        if not edge_data['exists']:
            continue  # Skip burned edges

        va = edge_data['vertex_a']
        vb = edge_data['vertex_b']
        adjacency[va].append((vb, edge_id))
        adjacency[vb].append((va, edge_id))

    # BFS
    queue = [start]
    visited = {start}
    predecessors = {start: (None, None)}  # {vertex: (prev_vertex, edge_id)}

    found = False
    while queue:
        node = queue.pop(0)

        if node == goal:
            found = True
            break

        for neighbor, edge_id in adjacency.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                predecessors[neighbor] = (node, edge_id)
                queue.append(neighbor)

    if not found:
        return None, set()

    # Backtrack to build path and collect edge IDs
    path = []
    edge_ids = set()
    current = goal

    while current is not None:
        path.append(current)
        prev, edge_id = predecessors[current]
        if edge_id is not None:
            edge_ids.add(edge_id)
        current = prev

    path.reverse()
    return path, edge_ids


def find_unaltered_prefix(
    current_pos: str,
    visit_sequence: List[str],
    rescued_so_far: Dict[str, int],
    vector: Dict[str, int],
    burned_edges: set,
    graph: Dict
) -> Tuple[List[str], List[str]]:
    """
    Find which rooms in visit_sequence can be visited without using burned edges.

    Only returns the unaltered prefix - stops at first room whose path
    uses a burned edge.

    Args:
        current_pos: Firefighter's current position
        visit_sequence: Planned rooms to visit in order
        rescued_so_far: {room_id: count} already picked up
        vector: {room_id: count} total planned to rescue
        burned_edges: Set of edge IDs that have burned
        graph: Current graph state

    Returns:
        (unaltered_rooms, affected_rooms) where:
        - unaltered_rooms: Prefix of rooms with unaffected paths
        - affected_rooms: Suffix starting from first affected room
    """
    unaltered = []
    current = current_pos

    for room in visit_sequence:
        # Skip if already fully rescued from this room
        if rescued_so_far.get(room, 0) >= vector.get(room, 0):
            continue

        # BFS from current to room with edge tracking
        path, edges_used = bfs_path_with_edges(current, room, graph)

        if not path:
            # No path exists - this and all remaining rooms are affected
            affected = [r for r in visit_sequence[len(unaltered):]
                       if rescued_so_far.get(r, 0) < vector.get(r, 0)]
            return unaltered, affected

        # Check if path uses any burned edge
        if edges_used & burned_edges:  # Set intersection
            # Path affected - stop here
            affected = [r for r in visit_sequence[len(unaltered):]
                       if rescued_so_far.get(r, 0) < vector.get(r, 0)]
            return unaltered, affected

        # This room is unaltered
        unaltered.append(room)
        current = room

    # All rooms unaltered
    return unaltered, []


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
