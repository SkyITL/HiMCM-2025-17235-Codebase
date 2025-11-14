#!/usr/bin/env python3
"""
Optimal rescue optimizer using greedy and Linear Programming approaches.

Implements the algorithm from the HiMCM paper:
- Generate all valid rescue combinations (vectors)
- Try all visit permutations and E² exit combinations
- Prune dominated items (slower than sequential singles)
- Assign items to firefighters using greedy value density
- Optionally use LP solver for optimal assignment
"""

from typing import Dict, List, Tuple, Optional
from itertools import combinations, permutations
import pathfinding


class RescueOptimizer:
    """
    Generates optimal rescue item assignments.

    Key algorithm steps:
    1. Preprocess: Dijkstra all-pairs shortest paths
    2. Generate items: For r=1 to k rooms, create all valid vectors
    3. Optimize paths: Try all permutations × E² exit combos
    4. Prune: Remove items slower than sequential singles
    5. Assign: Greedy by value density or LP solver
    """

    def __init__(self, k_capacity: Dict[str, int] = None):
        """
        Initialize optimizer.

        Args:
            k_capacity: {firefighter_id: max_rooms_per_trip}
                       If None, uses default k=3 for all firefighters
        """
        self.k_capacity = k_capacity or {}
        self.default_k = 3
        self.distance_matrix = {}
        self.room_priorities = {}
        self.items = []

    def preprocess_distances(self, state: Dict):
        """
        Run Dijkstra all-pairs on rooms.

        This is run once when switching to optimal rescue phase.
        Time complexity: O(V × E log V)

        Args:
            state: Full state from sim.read()
        """
        print("Preprocessing: Computing all-pairs shortest paths...")

        graph = state['graph']

        # Compute all-pairs shortest paths (rooms only for efficiency)
        self.distance_matrix = pathfinding.dijkstra_all_pairs(graph, rooms_only=True)

        # Also need paths from/to exits
        exits = pathfinding.find_exits(graph)
        for exit_id in exits:
            self.distance_matrix[exit_id] = pathfinding.dijkstra_single_source(graph, exit_id)

        # Extract room priorities
        self.room_priorities = {
            v_id: v_data['priority']
            for v_id, v_data in graph['vertices'].items()
            if v_data['type'] == 'room'
        }

        print(f"Preprocessing complete. Distance matrix size: {len(self.distance_matrix)} vertices")

    def generate_items(self, state: Dict, k: int = None) -> List[Dict]:
        """
        Generate all valid rescue items with pruning.

        Args:
            state: Full state from sim.read()
            k: Maximum capacity (default: self.default_k = 3)

        Returns:
            List of items, each with:
            {
                'vector': {room_id: count},
                'visit_sequence': [room1, room2, ...],
                'entry_exit': exit_id,
                'drop_exit': exit_id,
                'full_path': [entry, ...rooms..., drop],
                'time': float,
                'value': float,
                'people_rescued': int
            }

        Time complexity: O(V^k × k! × E²) where V=rooms, k=capacity, E=exits
        With V=22, k=3, E=2: ~22^3 × 6 × 4 = ~250k items before pruning
        """
        if k is None:
            k = self.default_k

        print(f"Generating items with k={k}...")

        items = []
        rooms = pathfinding.get_rooms_with_incapable(state)
        exits = pathfinding.find_exits(state['graph'])
        discovered = state['discovered_occupants']

        print(f"Rooms with incapable: {len(rooms)}")
        print(f"Exits: {len(exits)}")

        # Generate items for r = 1, 2, 3, ..., k rooms
        for num_rooms in range(1, min(k + 1, len(rooms) + 1)):
            print(f"  Generating {num_rooms}-room combinations...")

            count_for_this_r = 0

            # For each combination of num_rooms
            for room_combo in combinations(rooms, num_rooms):
                # Generate all valid vectors for this combination
                vectors = self._generate_vectors(room_combo, k, discovered)

                for vector in vectors:
                    # CRITICAL: Only include rooms with non-zero counts in visit sequence
                    # Filter out rooms with count=0 to avoid wasteful detours
                    rooms_to_visit = [room for room in room_combo if vector.get(room, 0) > 0]

                    if not rooms_to_visit:
                        continue  # Skip empty vectors

                    # OPTIMIZATION: For each vector, find the BEST permutation
                    # and BEST exit combination, not all combinations
                    best_item = None
                    best_time = float('inf')

                    # Try all visit orders (permutations) and exit combinations
                    for visit_seq in permutations(rooms_to_visit):
                        for entry_exit in exits:
                            for drop_exit in exits:
                                item = pathfinding.compute_optimal_item_for_vector(
                                    vector,
                                    list(visit_seq),
                                    entry_exit,
                                    drop_exit,
                                    self.distance_matrix,
                                    self.room_priorities
                                )

                                # Keep only the fastest one
                                if item['time'] < best_time:
                                    best_time = item['time']
                                    best_item = item

                    # Add only the best permutation/exit combo for this vector
                    if best_item:
                        items.append(best_item)
                        count_for_this_r += 1

            print(f"    Generated {count_for_this_r} items for {num_rooms}-room combos")

        print(f"Total raw items: {len(items)}")

        # CRITICAL: Prune dominated items
        items = self.prune_dominated_items(items)

        print(f"After pruning: {len(items)} items remain")

        self.items = items
        return items

    def _generate_vectors(
        self,
        rooms: Tuple[str, ...],
        k: int,
        discovered: Dict[str, Dict]
    ) -> List[Dict[str, int]]:
        """
        Generate all valid vectors for given room combination.

        A vector is a distribution of rescue counts across rooms.
        Constraints:
        - sum(counts) ≤ k (firefighter capacity)
        - count[room] ≤ incapable_count[room] (can't rescue more than exist)

        Args:
            rooms: Tuple of room IDs
            k: Maximum total people to rescue
            discovered: discovered_occupants from state

        Returns:
            List of vectors: [{room_id: count}, ...]

        Example: rooms=(A, B), k=3, incapable={A:5, B:2}
        Vectors: {A:1}, {A:2}, {A:3}, {B:1}, {B:2},
                {A:1,B:1}, {A:1,B:2}, {A:2,B:1}
        """
        vectors = []

        # Get max possible from each room
        max_counts = {}
        for room in rooms:
            max_counts[room] = discovered[room]['incapable']

        # Generate all valid distributions using recursive partitioning
        def generate_partitions(
            remaining_capacity: int,
            remaining_rooms: List[str],
            current_vector: Dict[str, int]
        ):
            if not remaining_rooms:
                # Base case: all rooms assigned
                if sum(current_vector.values()) > 0:
                    vectors.append(dict(current_vector))
                return

            room = remaining_rooms[0]
            rest_rooms = remaining_rooms[1:]

            # Try all possible counts for this room
            max_for_room = min(max_counts[room], remaining_capacity)

            for count in range(0, max_for_room + 1):
                current_vector[room] = count
                generate_partitions(
                    remaining_capacity - count,
                    rest_rooms,
                    current_vector
                )

            # Backtrack
            del current_vector[room]

        generate_partitions(k, list(rooms), {})

        return vectors

    def prune_dominated_items(self, items: List[Dict]) -> List[Dict]:
        """
        Remove items that are slower than doing sequential single-room rescues.

        For an item visiting rooms [A, B, C]:
        - If time(A,B,C combined) > time(A_alone) + time(B_alone) + time(C_alone)
        - Then the combined item is dominated and should be removed

        This dramatically reduces the item count while maintaining optimality.

        Args:
            items: List of all generated items

        Returns:
            List of non-dominated items
        """
        print("Pruning dominated items...")

        # Step 1: Build lookup of best single-room times
        single_times = {}  # {(room_id, count): best_time}

        for item in items:
            if len(item['visit_sequence']) == 1:
                room = item['visit_sequence'][0]
                count = item['vector'][room]
                key = (room, count)

                if key not in single_times or item['time'] < single_times[key]:
                    single_times[key] = item['time']

        # Step 2: Filter multi-room items
        pruned = []
        removed_count = 0

        for item in items:
            rooms = item['visit_sequence']

            if len(rooms) == 1:
                # Always keep single-room items
                pruned.append(item)
            else:
                # Check if combined is faster than sequential singles
                sequential_time = sum(
                    single_times.get((room, item['vector'][room]), float('inf'))
                    for room in rooms
                )

                if item['time'] < sequential_time:
                    # Combined is faster - keep it!
                    pruned.append(item)
                else:
                    # Dominated - remove it
                    removed_count += 1

        print(f"  Removed {removed_count} dominated items")

        return pruned

    def greedy_assignment(
        self,
        items: List[Dict],
        state: Dict
    ) -> Dict[str, List[Dict]]:
        """
        Greedy algorithm: assign items to firefighters by value density.

        Algorithm:
        1. Sort items by value/time (value density) descending
        2. For each item, check if it violates linear constraints
        3. If valid, assign to nearest available firefighter
        4. Track remaining capacity per room

        Args:
            items: List of generated items
            state: Full state from sim.read()

        Returns:
            {firefighter_id: [item1, item2, ...]}
        """
        print("Running greedy assignment...")

        # Sort by value density (high to low)
        sorted_items = sorted(items, key=lambda x: x['value'], reverse=True)

        # Track remaining incapable people per room
        discovered = state['discovered_occupants']
        remaining = {
            room_id: occupants['incapable']
            for room_id, occupants in discovered.items()
        }

        # Track firefighter assignments
        assignments = {ff_id: [] for ff_id in state['firefighters']}

        # Greedy selection
        selected_count = 0

        for item in sorted_items:
            # Check if this item violates constraints
            valid = True
            for room, count in item['vector'].items():
                if remaining.get(room, 0) < count:
                    valid = False
                    break

            if not valid:
                continue  # Skip this item

            # Assign to nearest firefighter (simplified: just round-robin)
            # TODO: Could optimize by assigning to firefighter nearest to entry_exit
            ff_id = min(assignments.keys(), key=lambda fid: len(assignments[fid]))

            # Add to assignment
            assignments[ff_id].append(item)
            selected_count += 1

            # Update remaining capacity
            for room, count in item['vector'].items():
                remaining[room] -= count

        print(f"  Selected {selected_count} items")
        print(f"  Assignments: {[len(assignments[fid]) for fid in sorted(assignments.keys())]}")

        # Remove firefighters with no assignments
        assignments = {fid: items for fid, items in assignments.items() if items}

        return assignments
