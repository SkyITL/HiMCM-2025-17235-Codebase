#!/usr/bin/env python3
"""
Sweep Coordinator: K-medoids + MST sweeping strategy

This module implements a systematic building sweep using:
1. K-medoids partitioning with corridor distance
2. Complete graph construction (all-pairs shortest paths)
3. MST construction using Prim's algorithm
4. DFS 2× traversal path generation
"""

import random
from typing import Dict, List, Set, Tuple
from pathfinding import bfs_next_step, dijkstra_single_source, bfs_path_with_edges


class SweepCoordinator:
    """
    Coordinates systematic building sweep using K-medoids + MST.

    Algorithm:
    - Partition rooms into K clusters (K = num firefighters) using K-medoids
    - Build complete graph for each cluster (all-pairs corridor distances)
    - Construct MST on each complete graph using Prim's algorithm
    - Generate DFS 2× traversal paths for each firefighter
    - Instruct capable occupants during sweep
    """

    def __init__(self, num_firefighters: int, seed: int = None):
        """
        Initialize sweep coordinator.

        Args:
            num_firefighters: Number of firefighters (K for K-medoids)
            seed: Random seed for deterministic k-medoids clustering (None for random)
        """
        self.num_firefighters = num_firefighters
        self.seed = seed
        self.partitions = {}  # {ff_id: [room_ids]}
        self.sweep_paths = {}  # {ff_id: [vertex_ids]}
        self.ff_to_exit = {}  # {ff_id: exit_id}
        self.globally_visited = set()
        self.current_path_index = {}  # {ff_id: int}
        self.initialized = False
        self.last_graph_hash = None  # Track graph changes for replanning
        self.replan_count = 0
        self.ticks_since_progress = 0  # Track stalled progress
        self.last_visited_count = 0

    def initialize_sweep(self, state: Dict):
        """
        One-time setup at simulation start.

        Args:
            state: Current simulation state
        """
        if self.initialized:
            return

        # Extract graph structure
        graph = state['graph']
        vertices = graph['vertices']
        edges = graph['edges']

        # Find all rooms and exits
        rooms = [
            v_id for v_id, v_data in vertices.items()
            if v_data['type'] == 'room'
        ]
        exits = [
            v_id for v_id, v_data in vertices.items()
            if v_data['type'] == 'exit'
        ]

        if len(rooms) == 0:
            return

        # K-medoids partitioning with corridor distance
        clusters = self._k_medoids_partition(rooms, self.num_firefighters, graph)

        # Assign clusters to firefighters
        firefighters = list(state['firefighters'].keys())
        for i, (medoid, cluster_rooms) in enumerate(clusters.items()):
            if i >= len(firefighters):
                break

            ff_id = firefighters[i]
            self.partitions[ff_id] = cluster_rooms

            # Assign nearest exit to this firefighter
            ff_pos = state['firefighters'][ff_id]['position']
            nearest_exit = min(exits, key=lambda e: self._bfs_distance(ff_pos, e, graph))
            self.ff_to_exit[ff_id] = nearest_exit

            # Build complete graph for this cluster
            complete_graph = self._build_complete_graph(cluster_rooms, graph)

            # Construct MST using Prim's algorithm
            mst = self._build_mst_prim(complete_graph, cluster_rooms)

            # Generate DFS 2× traversal path
            # Start from room closest to firefighter's current position
            start_room = min(cluster_rooms, key=lambda r: self._bfs_distance(ff_pos, r, graph))
            dfs_path = self._dfs_traversal_2x(mst, start_room)

            self.sweep_paths[ff_id] = dfs_path
            self.current_path_index[ff_id] = 0

        self.initialized = True

    def get_sweep_actions(self, state: Dict) -> Dict[str, List[Dict]]:
        """
        Generate sweep actions for all firefighters.

        Args:
            state: Current simulation state

        Returns:
            {ff_id: [action_dicts]}
        """
        graph = state['graph']

        # Check if graph has changed (edges burned) and trigger replan
        current_hash = self._hash_graph(graph)
        if self.last_graph_hash is not None and current_hash != self.last_graph_hash:
            print(f"\n🔥 Graph changed during sweep - replanning! (replan #{self.replan_count + 1})")
            self._replan_sweep(state)
            self.replan_count += 1

        self.last_graph_hash = current_hash

        actions = {}
        vertices = graph['vertices']
        discovered = state.get('discovered_occupants', {})

        for ff_id, ff_data in state['firefighters'].items():
            ff_actions = []
            ff_pos = ff_data['position']

            # Check if firefighter has a sweep path
            if ff_id not in self.sweep_paths:
                actions[ff_id] = []
                continue

            # Follow pre-computed sweep path
            path = self.sweep_paths[ff_id]
            path_idx = self.current_path_index.get(ff_id, 0)

            # Each firefighter gets 2 actions per tick (hardcoded for now)
            for action_slot in range(2):
                # First, check if current position has capable occupants to instruct
                current_vertex = vertices.get(ff_pos, {})
                if current_vertex.get('type') == 'room':
                    self.globally_visited.add(ff_pos)

                    if ff_pos in discovered and discovered[ff_pos].get('capable', 0) > 0:
                        # Instruct capable occupants at current position
                        ff_actions.append({'type': 'instruct'})
                        continue  # Use this action slot for instruction

                # If path is complete, find nearest room with capable occupants OR unvisited rooms
                if path_idx >= len(path):
                    # Priority 1: Find rooms with capable occupants that need instruction
                    rooms_with_capable = [
                        room_id for room_id, occ_data in discovered.items()
                        if occ_data.get('capable', 0) > 0
                    ]

                    if rooms_with_capable:
                        # Move to nearest room with capable occupants
                        nearest_room = min(
                            rooms_with_capable,
                            key=lambda r: self._bfs_distance(ff_pos, r, graph)
                        )

                        next_step = bfs_next_step(ff_pos, nearest_room, graph)
                        if next_step:
                            ff_actions.append({
                                'type': 'move',
                                'target': next_step
                            })
                            ff_pos = next_step
                        continue

                    # Priority 2: Find unvisited rooms
                    all_rooms = {
                        v_id for v_id, v_data in vertices.items()
                        if v_data['type'] == 'room'
                    }
                    unvisited_rooms = all_rooms - self.globally_visited

                    if unvisited_rooms:
                        # Sort unvisited rooms by distance
                        room_distances = [
                            (r, self._bfs_distance(ff_pos, r, graph))
                            for r in unvisited_rooms
                        ]
                        sorted_unvisited = sorted(room_distances, key=lambda x: x[1])

                        moved = False
                        for target_room, dist in sorted_unvisited:
                            # Skip if unreachable
                            if dist == float('inf'):
                                continue

                            next_step = bfs_next_step(ff_pos, target_room, graph)
                            if next_step:
                                ff_actions.append({
                                    'type': 'move',
                                    'target': next_step
                                })
                                ff_pos = next_step
                                moved = True
                                break

                        if moved:
                            continue

                    # Priority 3: Return to assigned exit if not already there
                    assigned_exit = self.ff_to_exit.get(ff_id)
                    if assigned_exit and ff_pos != assigned_exit:
                        next_step = bfs_next_step(ff_pos, assigned_exit, graph)
                        if next_step:
                            ff_actions.append({
                                'type': 'move',
                                'target': next_step
                            })
                            ff_pos = next_step
                            continue

                    # No work remaining - firefighter waits at exit
                    break

                else:
                    # Following sweep path
                    target_room = path[path_idx]

                    # If already at target room, move to next
                    if ff_pos == target_room:
                        self.globally_visited.add(target_room)
                        path_idx += 1
                        self.current_path_index[ff_id] = path_idx

                        if path_idx >= len(path):
                            # Path complete - will check for capable occupants next iteration
                            continue

                        target_room = path[path_idx]

                    # Move towards target room
                    next_step = bfs_next_step(ff_pos, target_room, graph)

                    if next_step:
                        ff_actions.append({
                            'type': 'move',
                            'target': next_step
                        })
                        ff_pos = next_step
                    else:
                        # Can't reach target - skip to next
                        path_idx += 1
                        self.current_path_index[ff_id] = path_idx

            actions[ff_id] = ff_actions

        return actions

    def is_sweep_complete(self, state: Dict) -> bool:
        """
        Check if all rooms have been discovered OR all reachable rooms visited.

        Args:
            state: Current simulation state

        Returns:
            True if all rooms visited OR all remaining rooms unreachable
        """
        graph = state['graph']
        vertices = graph['vertices']

        all_rooms = {
            v_id for v_id, v_data in vertices.items()
            if v_data['type'] == 'room'
        }

        # Check if all rooms visited
        if all_rooms.issubset(self.globally_visited):
            return True

        # Track progress to detect stalls
        current_visited = len(self.globally_visited)
        if current_visited > self.last_visited_count:
            # Progress made - reset stall counter
            self.ticks_since_progress = 0
            self.last_visited_count = current_visited
        else:
            # No progress - increment stall counter
            self.ticks_since_progress += 1

        # Quick check: If all firefighters are at exits with completed paths,
        # assume sweep is done (don't wait 20 ticks)
        firefighters = state.get('firefighters', {})
        all_at_exits_with_completed_paths = True
        for ff_id in firefighters.keys():
            assigned_exit = self.ff_to_exit.get(ff_id)
            ff_pos = firefighters[ff_id]['position']
            path = self.sweep_paths.get(ff_id, [])
            path_idx = self.current_path_index.get(ff_id, 0)

            # Check if path complete and at exit
            if path_idx < len(path) or ff_pos != assigned_exit:
                all_at_exits_with_completed_paths = False
                break

        if all_at_exits_with_completed_paths and self.ticks_since_progress >= 2:
            # All firefighters at exits, paths complete, and no progress for 2+ ticks
            unvisited_rooms = all_rooms - self.globally_visited
            print(f"\n✓ All firefighters at exits with completed sweep paths")
            print(f"   Visited: {len(self.globally_visited)}/{len(all_rooms)} rooms")
            if unvisited_rooms:
                print(f"   {len(unvisited_rooms)} rooms unreachable (blocked by fire)")
            print(f"   Switching to rescue phase...")
            return True

        # Only check reachability if stalled for 20+ ticks (expensive operation)
        if self.ticks_since_progress < 20:
            return False

        # Safety check: are all unvisited rooms unreachable?
        unvisited_rooms = all_rooms - self.globally_visited

        if not unvisited_rooms:
            return True

        # Check if any firefighter can reach any unvisited room
        firefighters = state.get('firefighters', {})
        for ff_id, ff_data in firefighters.items():
            ff_pos = ff_data['position']
            for room in unvisited_rooms:
                if self._bfs_distance(ff_pos, room, graph) < float('inf'):
                    # At least one room is reachable - reset stall counter
                    self.ticks_since_progress = 0
                    return False

        # All unvisited rooms are unreachable - force phase transition
        print(f"\n⚠️  All unvisited rooms unreachable ({len(unvisited_rooms)} rooms cut off by fire)")
        print(f"   Visited: {len(self.globally_visited)}/{len(all_rooms)} rooms")
        print(f"   Stalled for {self.ticks_since_progress} ticks")
        print(f"   Forcing phase transition to rescue mode...")
        return True

    def _k_medoids_partition(
        self,
        rooms: List[str],
        k: int,
        graph: Dict
    ) -> Dict[str, List[str]]:
        """
        K-medoids (PAM) clustering with corridor distance.

        Args:
            rooms: List of room IDs
            k: Number of clusters
            graph: Graph structure

        Returns:
            {medoid_id: [room_ids]}
        """
        if len(rooms) <= k:
            # Fewer rooms than clusters - one room per cluster
            return {room: [room] for room in rooms[:k]}

        # Initialize: random medoids with optional seed for reproducibility
        if self.seed is not None:
            random.seed(self.seed)

        medoids = random.sample(rooms, k)
        max_iterations = 50

        for iteration in range(max_iterations):
            # Assignment step: assign each room to nearest medoid
            clusters = {m: [] for m in medoids}

            for room in rooms:
                nearest_medoid = min(
                    medoids,
                    key=lambda m: self._bfs_distance(room, m, graph)
                )
                clusters[nearest_medoid].append(room)

            # Update step: find best medoid for each cluster
            new_medoids = []

            for medoid, cluster_rooms in clusters.items():
                if not cluster_rooms:
                    new_medoids.append(medoid)
                    continue

                # Find room that minimizes total distance to all others
                best_medoid = min(
                    cluster_rooms,
                    key=lambda r: sum(
                        self._bfs_distance(r, other, graph)
                        for other in cluster_rooms
                    )
                )
                new_medoids.append(best_medoid)

            # Check convergence
            if set(new_medoids) == set(medoids):
                break

            medoids = new_medoids

        return clusters

    def _build_complete_graph(
        self,
        cluster_rooms: List[str],
        graph: Dict
    ) -> Dict[str, Dict[str, float]]:
        """
        Build complete graph with all-pairs shortest paths.

        Args:
            cluster_rooms: Rooms in this cluster
            graph: Graph structure

        Returns:
            {room_a: {room_b: distance}}
        """
        complete_graph = {}

        for room_a in cluster_rooms:
            complete_graph[room_a] = {}

            # Use Dijkstra to get all distances from room_a
            # dijkstra_single_source(graph, start) returns {vertex: (distance, path)}
            result = dijkstra_single_source(graph, room_a)

            for room_b in cluster_rooms:
                if room_a != room_b:
                    # Extract distance from tuple (distance, path)
                    dist_tuple = result.get(room_b, (float('inf'), []))
                    complete_graph[room_a][room_b] = dist_tuple[0]

        return complete_graph

    def _build_mst_prim(
        self,
        complete_graph: Dict[str, Dict[str, float]],
        rooms: List[str]
    ) -> Dict[str, List[str]]:
        """
        Construct MST using Prim's algorithm.

        Args:
            complete_graph: All-pairs distances
            rooms: Rooms in cluster

        Returns:
            MST as adjacency list {room: [neighbors]}
        """
        import heapq

        if not rooms:
            return {}

        mst = {room: [] for room in rooms}
        visited = set()
        pq = []

        # Start from first room
        start = rooms[0]
        visited.add(start)

        # Add all edges from start
        for neighbor, weight in complete_graph.get(start, {}).items():
            heapq.heappush(pq, (weight, start, neighbor))

        # Build MST
        while pq and len(visited) < len(rooms):
            weight, u, v = heapq.heappop(pq)

            if v in visited:
                continue

            # Add edge to MST (undirected)
            mst[u].append(v)
            mst[v].append(u)
            visited.add(v)

            # Add edges from newly visited vertex
            for neighbor, weight in complete_graph.get(v, {}).items():
                if neighbor not in visited:
                    heapq.heappush(pq, (weight, v, neighbor))

        return mst

    def _dfs_traversal_2x(
        self,
        mst: Dict[str, List[str]],
        start: str
    ) -> List[str]:
        """
        Generate DFS pre-order traversal order using MST as GUIDANCE only.

        This returns the ORDER of rooms to visit (DFS pre-order on MST),
        but does NOT include duplicate visits. The actual pathfinding
        between rooms will be done during execution to avoid physically
        reentering the same room multiple times.

        Args:
            mst: MST adjacency list (used for guidance only)
            start: Starting room

        Returns:
            List of room IDs in DFS pre-order (each room appears once)
        """
        path = []
        visited = set()

        def dfs(node: str):
            if node in visited:
                return

            path.append(node)
            visited.add(node)

            for neighbor in mst.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)

        dfs(start)
        return path

    def _bfs_distance(self, start: str, end: str, graph: Dict) -> float:
        """
        Calculate corridor distance using BFS.

        Args:
            start: Start vertex ID
            end: End vertex ID
            graph: Graph structure

        Returns:
            BFS distance (number of hops)
        """
        if start == end:
            return 0.0

        from collections import deque

        queue = deque([(start, 0)])
        visited = {start}
        edges = graph['edges']

        while queue:
            current, dist = queue.popleft()

            # Check all edges from current vertex
            for edge_id, edge_data in edges.items():
                if edge_data.get('is_burned'):
                    continue

                vertex_a = edge_data['vertex_a']
                vertex_b = edge_data['vertex_b']

                neighbor = None
                if vertex_a == current:
                    neighbor = vertex_b
                elif vertex_b == current:
                    neighbor = vertex_a

                if neighbor and neighbor not in visited:
                    if neighbor == end:
                        return dist + 1

                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))

        return float('inf')

    def _find_nearest_exit(self, room: str, graph: Dict, state: Dict) -> str:
        """
        Find nearest exit from a room.

        Args:
            room: Room ID
            graph: Graph structure
            state: Current simulation state

        Returns:
            Exit ID or None
        """
        vertices = graph['vertices']
        exits = [
            v_id for v_id, v_data in vertices.items()
            if v_data['type'] == 'exit'
        ]

        if not exits:
            return None

        return min(exits, key=lambda e: self._bfs_distance(room, e, graph))

    def _hash_graph(self, graph: Dict) -> int:
        """
        Hash the graph structure to detect changes.

        Args:
            graph: Graph structure

        Returns:
            Hash of burned edges
        """
        edges = graph['edges']
        burned_edges = tuple(sorted([
            edge_id for edge_id, edge_data in edges.items()
            if edge_data.get('is_burned', False)
        ]))
        return hash(burned_edges)

    def _replan_sweep(self, state: Dict):
        """
        Replan sweep paths when graph changes.

        Strategy:
        1. Find all unvisited rooms (globally_visited tracks progress)
        2. Re-partition unvisited rooms using K-medoids
        3. Rebuild MST for each cluster
        4. Generate new DFS paths starting from firefighter's current position

        Args:
            state: Current simulation state
        """
        print(f"  Replanning sweep: {len(self.globally_visited)} rooms already visited")

        graph = state['graph']
        vertices = graph['vertices']

        # Find unvisited rooms
        all_rooms = [
            v_id for v_id, v_data in vertices.items()
            if v_data['type'] == 'room'
        ]

        unvisited_rooms = [
            room for room in all_rooms
            if room not in self.globally_visited
        ]

        print(f"  Unvisited rooms: {len(unvisited_rooms)}/{len(all_rooms)}")

        if len(unvisited_rooms) == 0:
            # All rooms visited - no need to replan
            print(f"  All rooms visited - no replanning needed")
            return

        # Re-partition unvisited rooms
        clusters = self._k_medoids_partition(unvisited_rooms, self.num_firefighters, graph)

        # Rebuild paths for each firefighter
        firefighters = list(state['firefighters'].keys())
        for i, (medoid, cluster_rooms) in enumerate(clusters.items()):
            if i >= len(firefighters):
                break

            ff_id = firefighters[i]

            if not cluster_rooms:
                # No rooms assigned to this firefighter
                self.sweep_paths[ff_id] = []
                self.current_path_index[ff_id] = 0
                continue

            # Get firefighter's current position
            ff_pos = state['firefighters'][ff_id]['position']

            # Build complete graph for this cluster
            complete_graph = self._build_complete_graph(cluster_rooms, graph)

            # Construct MST
            mst = self._build_mst_prim(complete_graph, cluster_rooms)

            # Generate new DFS path starting from closest room to current position
            start_room = min(cluster_rooms, key=lambda r: self._bfs_distance(ff_pos, r, graph))
            dfs_path = self._dfs_traversal_2x(mst, start_room)

            self.sweep_paths[ff_id] = dfs_path
            self.current_path_index[ff_id] = 0

            print(f"    {ff_id}: Assigned {len(cluster_rooms)} unvisited rooms")

        print(f"  Replanning complete")
