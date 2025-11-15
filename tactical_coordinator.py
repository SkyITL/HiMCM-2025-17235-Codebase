#!/usr/bin/env python3
"""
Tactical coordinator for executing rescue items.

Translates high-level rescue plans (items) into low-level simulator actions.
Manages multi-tick execution, state tracking, and action sequencing.

Key responsibilities:
- Decompose items into waypoint sequences
- Track execution progress for each firefighter
- Generate 2 actions per tick per firefighter
- Handle item completion and transition to next item
- Follow precomputed paths without replanning
"""

from typing import Dict, List, Optional


class ItemExecutionPlan:
    """
    Tracks execution state for one rescue item.

    An item specifies:
    - Which rooms to visit and how many people to rescue
    - Exact visiting sequence
    - Entry and drop exits
    - Precomputed full path

    This class tracks progress through that plan.
    """

    def __init__(self, item: Dict):
        """
        Initialize execution plan from item.

        Args:
            item: Item dict from optimizer with:
                'vector': {room_id: count}
                'visit_sequence': [room1, room2, ...]
                'entry_exit': exit_id
                'drop_exit': exit_id
                'full_path': [entry, ...rooms..., drop]
                'time': float
                'value': float
        """
        self.item = item
        self.vector = item['vector']  # {room_id: count to rescue}
        self.visit_sequence = item['visit_sequence']  # Room order
        self.full_path = item['full_path']  # Complete path
        self.entry_exit = item['entry_exit']
        self.drop_exit = item['drop_exit']

        # Execution state
        self.current_path_idx = 0  # Index in full_path
        self.rescued_so_far = {room: 0 for room in self.vector}  # Progress
        self.phase = 'travel_to_entry'  # 'travel_to_entry', 'executing', 'complete'
        self.at_entry = False  # Whether firefighter has reached entry_exit

        # Replanning state
        self.original_vector = dict(item['vector'])  # Backup before truncation
        self.affected_rooms = []  # Rooms we can't reach anymore
        self.truncated = False  # Flag for truncation

    def get_current_target(self) -> Optional[str]:
        """Get next vertex in precomputed path."""
        if self.current_path_idx < len(self.full_path):
            return self.full_path[self.current_path_idx]
        return None

    def advance_path(self):
        """Move to next vertex in path."""
        self.current_path_idx += 1

    def at_pickup_location(self, current_pos: str) -> bool:
        """Check if at a room where we need to pick up people."""
        return (current_pos in self.visit_sequence and
                self.rescued_so_far[current_pos] < self.vector[current_pos])

    def all_picked_up(self) -> bool:
        """Check if we've rescued everyone from all rooms."""
        return all(
            self.rescued_so_far[room] >= self.vector[room]
            for room in self.vector
        )

    def is_complete(self, carrying: int = 0) -> bool:
        """
        Check if plan is fully executed.

        Args:
            carrying: Number of people currently being carried

        Returns:
            True if plan complete (all rescued, path complete, dropped off)
        """
        return (self.current_path_idx >= len(self.full_path) and
                self.all_picked_up() and
                carrying == 0  # Must have dropped off everyone
        )

    def get_status(self) -> str:
        """Get human-readable status string."""
        total_to_rescue = sum(self.vector.values())
        total_rescued = sum(self.rescued_so_far.values())
        return f"{total_rescued}/{total_to_rescue} rescued, path: {self.current_path_idx}/{len(self.full_path)}"

    def truncate_to_unaltered(
        self,
        unaltered_rooms: List[str],
        affected_rooms: List[str],
        nearest_exit: str,
        graph: Dict
    ):
        """
        Modify this plan to only visit unaltered rooms.

        Args:
            unaltered_rooms: Rooms that can still be visited
            affected_rooms: Rooms now unreachable
            nearest_exit: Exit to drop off at
            graph: Current graph state
        """
        self.affected_rooms = affected_rooms
        self.visit_sequence = unaltered_rooms
        self.drop_exit = nearest_exit
        self.truncated = True

        # Remove affected rooms from vector
        for room in affected_rooms:
            if room in self.vector:
                del self.vector[room]

        # Rebuild full_path using BFS for unaltered rooms + exit
        # Note: We can't use distance_matrix as it's stale after graph changes
        import pathfinding

        # Determine current position safely
        if self.current_path_idx == 0:
            current = self.entry_exit
            new_path = [self.entry_exit]
        elif self.current_path_idx < len(self.full_path):
            current = self.full_path[self.current_path_idx]
            new_path = []
        else:
            # Path index beyond path length - firefighter has completed path
            # Use last position in path (likely at exit)
            current = self.full_path[-1] if self.full_path else self.entry_exit
            new_path = []

        for room in unaltered_rooms:
            if current == room:
                continue

            path, _ = pathfinding.bfs_path_with_edges(current, room, graph)
            if path:
                if not new_path:
                    new_path = path
                else:
                    new_path.extend(path[1:])
                current = room

        # Add path to drop exit
        if current != nearest_exit:
            path, _ = pathfinding.bfs_path_with_edges(current, nearest_exit, graph)
            if path:
                new_path.extend(path[1:])

        self.full_path = new_path
        self.current_path_idx = 0  # Reset path index

    def get_affected_vector(self) -> Dict[str, int]:
        """
        Return people from affected rooms we haven't picked up yet.

        Returns:
            {room_id: count} for rooms we can't reach anymore
        """
        affected = {}
        for room in self.affected_rooms:
            planned = self.original_vector.get(room, 0)
            rescued = self.rescued_so_far.get(room, 0)
            remaining = planned - rescued
            if remaining > 0:
                affected[room] = remaining
        return affected


class TacticalCoordinator:
    """
    Manages multi-tick execution of assigned rescue items.

    Responsibilities:
    - Maintain execution plans for each firefighter
    - Generate 1 action per tick per firefighter
    - Follow precomputed paths from items
    - Handle pickup/dropoff sequencing
    - Transition between items when complete
    """

    def __init__(self):
        """Initialize coordinator."""
        self.ff_plans = {}  # {ff_id: [ItemExecutionPlan, ...]}
        self.ff_current_idx = {}  # {ff_id: current_item_index}

    def assign_items(self, assignments: Dict[str, List[Dict]]):
        """
        Load item assignments from optimizer.

        Args:
            assignments: {ff_id: [item1, item2, ...]} from greedy/LP
        """
        for ff_id, items in assignments.items():
            self.ff_plans[ff_id] = [ItemExecutionPlan(item) for item in items]
            self.ff_current_idx[ff_id] = 0

        print(f"Tactical coordinator loaded {len(assignments)} firefighter assignments")

    def get_actions_for_tick(self, state: Dict) -> Dict[str, List[Dict]]:
        """
        Generate 1 action per firefighter for current tick.

        This is the main entry point called by the model each tick.

        Args:
            state: Full state from sim.read()

        Returns:
            {ff_id: [action]} where action is:
            {'type': 'move', 'target': vertex_id}
            {'type': 'pick_up_incapable', 'count': N}
            {'type': 'drop_off', 'count': 'all'}
        """
        actions = {}

        for ff_id, ff_state in state['firefighters'].items():
            # Get current plan
            plan = self._get_current_plan(ff_id, ff_state)

            if not plan:
                # All items complete or no assignment
                actions[ff_id] = []
                continue

            # Generate 1 action based on plan
            ff_actions = self._plan_to_actions(plan, ff_state, state)
            actions[ff_id] = ff_actions

        return actions

    def _get_current_plan(self, ff_id: str, ff_state: Dict) -> Optional[ItemExecutionPlan]:
        """
        Get current active plan for firefighter.

        Automatically advances to next item when current is complete.

        Args:
            ff_id: Firefighter ID
            ff_state: Firefighter state dict with 'carrying_incapable'

        Returns:
            ItemExecutionPlan or None if all items complete
        """
        if ff_id not in self.ff_plans:
            return None

        queue = self.ff_plans[ff_id]
        idx = self.ff_current_idx.get(ff_id, 0)

        if idx >= len(queue):
            return None  # All items complete

        plan = queue[idx]

        carrying = ff_state['carrying_incapable']
        if plan.is_complete(carrying):
            # Advance to next item
            print(f"  {ff_id}: Completed item {idx+1}/{len(queue)}")
            self.ff_current_idx[ff_id] = idx + 1
            return self._get_current_plan(ff_id, ff_state)  # Recursive

        return plan

    def _plan_to_actions(
        self,
        plan: ItemExecutionPlan,
        ff_state: Dict,
        state: Dict
    ) -> List[Dict]:
        """
        Convert execution plan into 1 concrete action.

        Decision logic:
        0. If not at entry_exit → travel to entry_exit (Phase: travel_to_entry)
        1. If at pickup room and need to pick up → pickup action
        2. If carrying and at drop exit → drop_off action
        3. If not at target → move toward target (follow precomputed path)
        4. If at waypoint → advance to next waypoint

        Args:
            plan: Current ItemExecutionPlan
            ff_state: Firefighter state from state['firefighters'][ff_id]
            state: Full state

        Returns:
            List with 0-1 actions
        """
        actions = []
        current_pos = ff_state['position']
        carrying = ff_state['carrying_incapable']
        capacity = ff_state['max_carry_capacity']

        # Phase 0: Travel to entry exit if not there yet
        if plan.phase == 'travel_to_entry':
            if current_pos == plan.entry_exit:
                # Reached entry, transition to executing
                plan.phase = 'executing'
                plan.at_entry = True
            else:
                # Check if both current and target are exits - if so, teleport
                current_vertex = state['graph']['vertices'][current_pos]
                target_vertex = state['graph']['vertices'][plan.entry_exit]

                if current_vertex['type'] in ['exit', 'window_exit'] and target_vertex['type'] in ['exit', 'window_exit']:
                    # Instant teleport between exits (free repositioning)
                    actions.append({'type': 'teleport', 'target': plan.entry_exit})
                else:
                    # Regular movement using BFS
                    import pathfinding
                    next_step = pathfinding.bfs_next_step(current_pos, plan.entry_exit, state['graph'])
                    if next_step:
                        actions.append({'type': 'move', 'target': next_step})

                return actions[:1]

        # Phase 1: Execute the rescue plan

        # Case 1: At pickup room, need to pick up people
        if plan.at_pickup_location(current_pos):
            room = current_pos
            needed = plan.vector[room] - plan.rescued_so_far[room]
            can_carry = capacity - carrying

            if needed > 0 and can_carry > 0:
                # Pick up 1 person per tick
                count = min(1, needed, can_carry)
                actions.append({'type': 'pick_up_incapable', 'count': count})
                plan.rescued_so_far[room] += count
                carrying += count

                # If done at this room, advance path
                if plan.rescued_so_far[room] >= plan.vector[room]:
                    # Find next room or exit in path
                    while plan.current_path_idx < len(plan.full_path):
                        next_vertex = plan.full_path[plan.current_path_idx]
                        if next_vertex != current_pos:
                            break
                        plan.advance_path()

        # Case 2: At drop exit with people
        elif current_pos == plan.drop_exit and carrying > 0:
            actions.append({'type': 'drop_off', 'count': 'all'})
            # Plan should mark as complete after this

        # Case 3: Need to move along precomputed path
        else:
            target = plan.get_current_target()

            # Skip waypoints that match current position
            # (This means we successfully moved there in a previous tick)
            while target and target == current_pos:
                plan.advance_path()
                target = plan.get_current_target()

            if target and target != current_pos:
                # Move toward target
                # IMPORTANT: Don't advance path yet - wait until next tick to see if move succeeded
                actions.append({'type': 'move', 'target': target})

        return actions[:1]  # Max 1 action

    def handle_graph_change(self, state: Dict, optimizer) -> int:
        """
        Adapt all firefighter plans to graph changes (burned edges).

        For each firefighter with an active plan:
        1. Check if their current path is still valid
        2. If not, partition rooms into reachable/unreachable
        3. Truncate plan to only reachable rooms
        4. Collect people from unreachable rooms
        5. Regenerate items for unreachable people
        6. Reassign new items to available firefighters

        Args:
            state: Full state from sim.read()
            optimizer: RescueOptimizer instance for regenerating items

        Returns:
            Total number of people affected by graph changes
        """
        import pathfinding

        total_affected = 0
        affected_vectors = []  # Collect {room: count} for unreachable people

        graph = state['graph']

        # Check each firefighter's active plan
        for ff_id, plans in self.ff_plans.items():
            idx = self.ff_current_idx.get(ff_id, 0)

            if idx >= len(plans):
                continue  # No active plan

            current_plan = plans[idx]
            ff_state = state['firefighters'][ff_id]

            # Check path validity: are all rooms in visit_sequence still reachable?
            current_pos = ff_state['position']
            unreachable_rooms = []
            reachable_rooms = []

            for room in current_plan.visit_sequence:
                # Check if we can still reach this room
                path = pathfinding.bfs_next_step(current_pos, room, graph)

                if path is None:
                    # Room is unreachable
                    unreachable_rooms.append(room)
                else:
                    # Room is still reachable
                    reachable_rooms.append(room)

            # If any rooms are unreachable, truncate the plan
            if unreachable_rooms:
                print(f"   {ff_id}: {len(unreachable_rooms)} rooms now unreachable")

                # Find nearest exit for drop-off
                exits = pathfinding.find_exits(graph)
                nearest_exit = None
                min_dist = float('inf')

                for exit_id in exits:
                    path = pathfinding.bfs_next_step(current_pos, exit_id, graph)
                    if path:
                        # Use BFS distance as approximation
                        full_path, _ = pathfinding.bfs_path_with_edges(current_pos, exit_id, graph)
                        if full_path and len(full_path) < min_dist:
                            min_dist = len(full_path)
                            nearest_exit = exit_id

                if nearest_exit is None:
                    # Firefighter is completely trapped - no exits reachable
                    print(f"   WARNING: {ff_id} is trapped (no exits reachable)")
                    nearest_exit = current_plan.drop_exit  # Keep original, they're stuck anyway

                    # Redistribute this firefighter's remaining items to other firefighters
                    remaining_items = self.ff_plans[ff_id][idx+1:]  # All items after current
                    if remaining_items:
                        print(f"   {ff_id}: Redistributing {len(remaining_items)} remaining items from trapped firefighter")

                        # Collect all people from remaining items
                        trapped_vector = {}
                        for item_plan in remaining_items:
                            for room, count in item_plan.vector.items():
                                trapped_vector[room] = trapped_vector.get(room, 0) + count

                        # Clear this firefighter's remaining items
                        self.ff_plans[ff_id] = self.ff_plans[ff_id][:idx+1]  # Keep only current item

                        # Add to affected vectors for redistribution to other firefighters
                        if trapped_vector:
                            affected_vectors.append(trapped_vector)
                            count = sum(trapped_vector.values())
                            total_affected += count
                            print(f"   {ff_id}: {count} people from trapped firefighter will be redistributed to other firefighters")

                # Truncate plan to only reachable rooms
                current_plan.truncate_to_unaltered(
                    reachable_rooms,
                    unreachable_rooms,
                    nearest_exit,
                    graph
                )

                # Collect affected people (people we haven't picked up yet from unreachable rooms)
                affected_vector = current_plan.get_affected_vector()
                if affected_vector:
                    affected_vectors.append(affected_vector)
                    count = sum(affected_vector.values())
                    total_affected += count
                    print(f"   {ff_id}: {count} people affected in unreachable rooms")

        # Regenerate items for affected people and reassign
        if affected_vectors:
            print(f"   Regenerating items for {total_affected} affected people...")

            # Merge all affected vectors into one
            merged_vector = {}
            for vec in affected_vectors:
                for room, count in vec.items():
                    merged_vector[room] = merged_vector.get(room, 0) + count

            # Update discovered occupants to reflect only affected people
            # Create a temporary state for regeneration
            temp_discovered = {
                room: {'capable': 0, 'incapable': count}
                for room, count in merged_vector.items()
            }

            temp_state = dict(state)
            temp_state['discovered_occupants'] = temp_discovered

            # Filter out trapped firefighters from reassignment
            # (Only assign to firefighters who can reach at least one exit)
            exits = pathfinding.find_exits(graph)
            active_firefighters = {}

            for ff_id, ff_state in state['firefighters'].items():
                # Check if this firefighter can reach any exit
                can_reach_exit = False
                for exit_id in exits:
                    path = pathfinding.bfs_next_step(ff_state['position'], exit_id, graph)
                    if path is not None:
                        can_reach_exit = True
                        break

                if can_reach_exit:
                    active_firefighters[ff_id] = ff_state

            # Use only active (non-trapped) firefighters for reassignment
            temp_state['firefighters'] = active_firefighters

            if not active_firefighters:
                print(f"   WARNING: All firefighters are trapped - cannot reassign items")
                return total_affected

            # Regenerate items for affected rooms only
            new_items = optimizer.generate_items(temp_state)

            if new_items:
                # Run greedy assignment for new items (only to non-trapped firefighters)
                new_assignments = optimizer.greedy_assignment(new_items, temp_state)

                # Append new items to firefighters' queues
                for ff_id, items in new_assignments.items():
                    if ff_id in self.ff_plans:
                        self.ff_plans[ff_id].extend([ItemExecutionPlan(item) for item in items])
                        print(f"   {ff_id}: Assigned {len(items)} new items for affected people")
            else:
                print(f"   WARNING: Could not generate items for affected people (may be completely unreachable)")

        return total_affected

    def get_status(self) -> Dict[str, str]:
        """
        Get status of all firefighter plans.

        Returns:
            {ff_id: status_string}
        """
        status = {}

        for ff_id, queue in self.ff_plans.items():
            idx = self.ff_current_idx.get(ff_id, 0)

            if idx >= len(queue):
                status[ff_id] = "All items complete"
            else:
                current_plan = queue[idx]
                status[ff_id] = f"Item {idx+1}/{len(queue)}: {current_plan.get_status()}"

        return status
