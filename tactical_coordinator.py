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
        self.remaining_occupants = {}  # {room_id: count} - rooms with people still needing rescue
        self.optimizer = None  # Will be set by OptimalRescueModel

    def assign_items(self, assignments: Dict[str, List[Dict]], all_occupants: Dict[str, int] = None):
        """
        Load item assignments from optimizer.

        Initialize remaining_occupants pool with all people that need rescuing.

        Args:
            assignments: {ff_id: [item1, item2, ...]} from greedy/LP
            all_occupants: {room_id: count} of all incapable people in building (optional)
        """
        for ff_id, items in assignments.items():
            self.ff_plans[ff_id] = [ItemExecutionPlan(item) for item in items]
            self.ff_current_idx[ff_id] = 0

        # Initialize remaining occupants pool
        if all_occupants:
            self.remaining_occupants = dict(all_occupants)

            # Subtract people assigned in initial items
            for ff_id, items in assignments.items():
                for item in items:
                    for room, count in item['vector'].items():
                        if room in self.remaining_occupants:
                            self.remaining_occupants[room] = max(0, self.remaining_occupants[room] - count)
                            if self.remaining_occupants[room] == 0:
                                del self.remaining_occupants[room]

            total_remaining = sum(self.remaining_occupants.values())
            total_assigned = sum(sum(item['vector'].values()) for items in assignments.values() for item in items)
            print(f"Tactical coordinator loaded {len(assignments)} firefighter assignments")
            print(f"  Assigned: {total_assigned} people, Remaining: {total_remaining} people")
        else:
            print(f"Tactical coordinator loaded {len(assignments)} firefighter assignments")

    def get_actions_for_tick(self, state: Dict) -> Dict[str, List[Dict]]:
        """
        Generate 1 action per firefighter for current tick.

        Simplified replanning model:
        1. Validate current route - truncate if next step is blocked
        2. If at exit with no task, claim next rescue task from remaining rooms
        3. Generate actions for current task

        Args:
            state: Full state from sim.read()

        Returns:
            {ff_id: [action]} where action is:
            {'type': 'move', 'target': vertex_id}
            {'type': 'pick_up_incapable', 'count': N}
            {'type': 'drop_off', 'count': 'all'}
        """
        actions = {}

        # Step 1: Validate and truncate routes for all firefighters
        self._validate_and_truncate_routes(state)

        # Step 2: Check if any firefighters need new tasks
        self._assign_tasks_at_exits(state)

        # Step 3: Generate actions from plans
        for ff_id, ff_state in state['firefighters'].items():
            # Get current plan
            plan = self._get_current_plan(ff_id, ff_state)

            if not plan:
                # All items complete or no assignment
                actions[ff_id] = []
                continue

            # Generate 1 action based on plan
            ff_actions = self._plan_to_actions(ff_id, plan, ff_state, state)
            actions[ff_id] = ff_actions

            # Log if plan generated no actions
            if not ff_actions:
                current_pos = ff_state['position']
                carrying = ff_state.get('carrying_incapable', 0)
                target = plan.get_current_target()
                print(f"  [{ff_id}] NO MOVEMENT - Plan exists but generated no actions")
                print(f"              Position: {current_pos}, Target: {target}, Carrying: {carrying}")
                print(f"              Plan status: {plan.get_status()}")

        # Fallback: if a firefighter has no actions this round, move toward nearest exit
        for ff_id, ff_state in state['firefighters'].items():
            if not actions.get(ff_id):
                # No actions - log reason and try to move toward exit
                current_pos = ff_state['position']
                carrying = ff_state.get('carrying_incapable', 0)
                action_points = ff_state.get('action_points', 0)

                # Determine why firefighter has no actions
                plan = self._get_current_plan(ff_id, ff_state)
                if not plan:
                    # Check if all items are complete
                    idx = self.ff_current_idx.get(ff_id, 0)
                    total_items = len(self.ff_plans.get(ff_id, []))
                    if idx >= total_items and total_items > 0:
                        reason = f"All {total_items} rescue items completed"
                    elif total_items == 0:
                        reason = "No rescue items assigned"
                    else:
                        reason = f"No active plan (idx={idx}, total={total_items})"
                else:
                    reason = "Plan exists but generated no actions"

                print(f"  [{ff_id}] NO MOVEMENT - Reason: {reason}")
                print(f"              Position: {current_pos}, Carrying: {carrying}, Action points: {action_points}")

                # Only try to move if firefighter has action points
                if action_points <= 0:
                    print(f"              Cannot move: No action points remaining")
                    continue

                # Try to navigate to nearest exit
                exits = [v_id for v_id, v_data in state['graph']['vertices'].items()
                        if v_data['type'] in ['exit', 'window_exit']]

                if exits:
                    import pathfinding
                    # Find nearest exit by trying BFS to each and picking closest
                    best_exit = None
                    best_distance = float('inf')

                    for exit_id in exits:
                        # Use BFS to calculate distance
                        dist = self._bfs_distance(current_pos, exit_id, state['graph'])
                        if dist is not None and dist < best_distance:
                            best_distance = dist
                            best_exit = exit_id

                    if best_exit:
                        # Get next step toward exit
                        next_step = pathfinding.bfs_next_step(current_pos, best_exit, state['graph'])

                        if next_step and next_step != current_pos:
                            # Check if the edge to next_step actually exists
                            edge_exists = False
                            for edge_data in state['graph']['edges'].values():
                                if not edge_data['exists']:
                                    continue
                                if ((edge_data['vertex_a'] == current_pos and edge_data['vertex_b'] == next_step) or
                                    (edge_data['vertex_b'] == current_pos and edge_data['vertex_a'] == next_step)):
                                    edge_exists = True
                                    break

                            if edge_exists:
                                actions[ff_id] = [{'type': 'move', 'target': next_step}]
                                print(f"  [{ff_id}] Fallback action: Moving toward nearest exit {best_exit} (distance: {best_distance}) via {next_step}")
                            else:
                                print(f"  [{ff_id}] WARNING: BFS suggested {next_step} but edge {current_pos} <-> {next_step} does not exist!")
                        else:
                            print(f"  [{ff_id}] WARNING: Cannot move toward exit {best_exit} (already there or blocked)")
                    else:
                        print(f"  [{ff_id}] WARNING: No reachable exits found from {current_pos}")
                else:
                    print(f"  [{ff_id}] WARNING: No exits exist in building")

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
        ff_id: str,
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
        # DEBUG: Check if current position is a room that should have people
        if current_pos in plan.visit_sequence:
            if current_pos not in plan.vector:
                print(f"  [{ff_id}] ERROR: At {current_pos} in visit_sequence but not in vector!")
            elif plan.rescued_so_far[current_pos] >= plan.vector[current_pos]:
                print(f"  [{ff_id}] DEBUG: At {current_pos}, already rescued all {plan.vector[current_pos]} people")
            else:
                if carrying >= capacity:
                    print(f"  [{ff_id}] DEBUG: At {current_pos} but carrying {carrying}/{capacity} (full)")

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
                print(f"  [{ff_id}] Picking up {count} from {room} ({plan.rescued_so_far[room]}/{plan.vector[room]} rescued)")

                # If done at this room, advance path
                if plan.rescued_so_far[room] >= plan.vector[room]:
                    # Find next room or exit in path
                    while plan.current_path_idx < len(plan.full_path):
                        next_vertex = plan.full_path[plan.current_path_idx]
                        if next_vertex != current_pos:
                            break
                        plan.advance_path()
                    print(f"  [{ff_id}] Finished picking up from {room}, advancing to next target")

        # Case 2: At ANY exit with people - auto drop
        elif current_pos in state['graph']['vertices'] and state['graph']['vertices'][current_pos]['type'] in ['exit', 'window_exit'] and carrying > 0:
            actions.append({'type': 'drop_off', 'count': 'all'})
            # Dropped at any exit, not just the planned drop exit

        # Case 3: Need to move along precomputed path
        else:
            target = plan.get_current_target()

            # Skip waypoints that match current position
            # (This means we successfully moved there in a previous tick)
            while target and target == current_pos:
                plan.advance_path()
                target = plan.get_current_target()

            if target and target != current_pos:
                # CRITICAL: Don't trust the precomputed path - use BFS to get actual next step
                # This ensures we're using the current graph state, not stale data
                import pathfinding
                next_step = pathfinding.bfs_next_step(current_pos, target, state['graph'])

                if next_step and next_step != current_pos:
                    # Move toward target via BFS-validated step
                    # IMPORTANT: Don't advance path yet - wait until next tick to see if move succeeded
                    actions.append({'type': 'move', 'target': next_step})
                else:
                    # Cannot reach target - path is blocked, will be fixed by _validate_and_truncate_routes next tick
                    pass
            elif not target and carrying > 0:
                # Path exhausted but still carrying people - find nearest exit
                import pathfinding
                exits = [v_id for v_id, v_data in state['graph']['vertices'].items()
                        if v_data['type'] in ['exit', 'window_exit']]
                if exits:
                    # Find nearest exit using BFS distance
                    best_exit = None
                    best_distance = float('inf')
                    for exit_id in exits:
                        dist = self._bfs_distance(current_pos, exit_id, state['graph'])
                        if dist is not None and dist < best_distance:
                            best_distance = dist
                            best_exit = exit_id

                    if best_exit:
                        next_step = pathfinding.bfs_next_step(current_pos, best_exit, state['graph'])
                        if next_step:
                            actions.append({'type': 'move', 'target': next_step})

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

    def _validate_and_truncate_routes(self, state: Dict):
        """
        Validate each firefighter's current route and truncate if blocked.

        Check ALL remaining rooms in the plan to see if they're still reachable.
        If any room is unreachable, rebuild the entire plan.

        Args:
            state: Full state from sim.read()
        """
        import pathfinding

        graph = state['graph']

        for ff_id, ff_state in state['firefighters'].items():
            # Get current plan
            idx = self.ff_current_idx.get(ff_id, 0)
            if ff_id not in self.ff_plans or idx >= len(self.ff_plans[ff_id]):
                continue  # No active plan

            current_plan = self.ff_plans[ff_id][idx]
            current_pos = ff_state['position']

            # Check ALL remaining rooms in the plan, not just the next target
            need_replan = False

            # Find which rooms we still need to visit
            remaining_rooms = []
            for room in current_plan.visit_sequence:
                if current_plan.rescued_so_far.get(room, 0) < current_plan.vector.get(room, 0):
                    remaining_rooms.append(room)

            # Check if each remaining room is reachable
            for room in remaining_rooms:
                next_step = pathfinding.bfs_next_step(current_pos, room, graph)
                if next_step is None:
                    # Found an unreachable room - need to replan
                    print(f"  [{ff_id}] Route blocked: cannot reach room {room} from {current_pos}")
                    need_replan = True
                    break

            # Also check if drop exit is reachable
            if not need_replan and current_plan.drop_exit:
                next_step = pathfinding.bfs_next_step(current_pos, current_plan.drop_exit, graph)
                if next_step is None:
                    print(f"  [{ff_id}] Route blocked: cannot reach drop exit {current_plan.drop_exit} from {current_pos}")
                    need_replan = True

            if need_replan:
                # Rebuild path to remaining rooms
                self._rebuild_plan_path(current_plan, current_pos, graph, ff_id)

    def _rebuild_plan_path(self, plan: ItemExecutionPlan, current_pos: str, graph: Dict, ff_id: str):
        """
        Rebuild the path for a plan when current path is blocked.

        Args:
            plan: ItemExecutionPlan to rebuild
            current_pos: Current firefighter position
            graph: Current graph state
            ff_id: Firefighter ID (for logging)
        """
        import pathfinding

        # Find which rooms we still need to visit (not yet fully rescued)
        remaining_rooms = []
        for room in plan.visit_sequence:
            if plan.rescued_so_far.get(room, 0) < plan.vector.get(room, 0):
                remaining_rooms.append(room)

        if not remaining_rooms:
            # No more rooms to visit - just go to drop exit
            path, _ = pathfinding.bfs_path_with_edges(current_pos, plan.drop_exit, graph)
            if path:
                plan.full_path = path
                plan.current_path_idx = 0
                print(f"  [{ff_id}] Rebuilt path to drop exit: {len(path)} waypoints")
            else:
                print(f"  [{ff_id}] WARNING: Cannot reach drop exit {plan.drop_exit}")
                # Mark this plan as unreachable
                plan.full_path = []
                plan.current_path_idx = 0
            return

        # Check which rooms are still reachable
        reachable_rooms = []
        unreachable_rooms = []

        for room in remaining_rooms:
            path, _ = pathfinding.bfs_path_with_edges(current_pos, room, graph)
            if path:
                reachable_rooms.append(room)
            else:
                unreachable_rooms.append(room)

        if unreachable_rooms:
            print(f"  [{ff_id}] {len(unreachable_rooms)} rooms now unreachable: {unreachable_rooms}")

            # Add unreachable people back to remaining_occupants pool
            # BUT: only if we haven't already picked them up
            for room in unreachable_rooms:
                already_rescued = plan.rescued_so_far.get(room, 0)
                planned = plan.vector.get(room, 0)
                still_in_room = planned - already_rescued

                if still_in_room > 0:
                    self.remaining_occupants[room] = self.remaining_occupants.get(room, 0) + still_in_room
                    print(f"  [{ff_id}] Added {still_in_room} people from {room} to remaining pool (rescued {already_rescued}/{planned})")

            # Remove unreachable rooms from plan
            plan.visit_sequence = reachable_rooms
            for room in unreachable_rooms:
                if room in plan.vector:
                    del plan.vector[room]

        # Rebuild path through reachable rooms
        new_path = []
        current = current_pos

        for room in reachable_rooms:
            path, _ = pathfinding.bfs_path_with_edges(current, room, graph)
            if path:
                if not new_path:
                    new_path = path
                else:
                    new_path.extend(path[1:])  # Skip first element (duplicate)
                current = room

        # Add path to drop exit
        if current != plan.drop_exit:
            path, _ = pathfinding.bfs_path_with_edges(current, plan.drop_exit, graph)
            if path:
                new_path.extend(path[1:])
            else:
                print(f"  [{ff_id}] WARNING: Cannot reach drop exit {plan.drop_exit} from {current}")

        plan.full_path = new_path
        plan.current_path_idx = 0
        print(f"  [{ff_id}] Rebuilt path: {len(reachable_rooms)} reachable rooms, {len(new_path)} waypoints")

    def _assign_tasks_at_exits(self, state: Dict):
        """
        Let idle firefighters at exits "claim" rescue quests.

        Firefighters pick up quests themselves when:
        - They are at an exit
        - They have no current task
        - They are not carrying anyone
        - There are remaining people to rescue that are reachable

        Args:
            state: Full state from sim.read()
        """
        if not self.remaining_occupants:
            return  # No remaining people to rescue

        import pathfinding

        exits = [v_id for v_id, v_data in state['graph']['vertices'].items()
                if v_data['type'] in ['exit', 'window_exit']]

        for ff_id, ff_state in state['firefighters'].items():
            current_pos = ff_state['position']
            carrying = ff_state.get('carrying_incapable', 0)

            # Firefighter must be at exit, not carrying, and idle to claim a quest
            if current_pos not in exits or carrying > 0:
                continue

            # Check if firefighter is idle (no active tasks)
            idx = self.ff_current_idx.get(ff_id, 0)
            if ff_id in self.ff_plans and idx < len(self.ff_plans[ff_id]):
                continue  # Still has tasks - cannot claim new quest

            # Firefighter claims a quest from available rooms accessible from ANY exit
            if self.remaining_occupants and self.optimizer:
                print(f"  [{ff_id}] Claiming rescue quest (checking all exits)...")

                # Try all exits to find the best available quest
                best_item = None
                best_value_ratio = -1
                best_entry_exit = None

                for exit_id in exits:
                    # Filter remaining occupants reachable from this exit
                    reachable_from_exit = {}
                    for room, count in self.remaining_occupants.items():
                        next_step = pathfinding.bfs_next_step(exit_id, room, state['graph'])
                        if next_step is not None:
                            reachable_from_exit[room] = count

                    if not reachable_from_exit:
                        continue

                    # Generate items for this exit
                    temp_discovered = {
                        room: {'capable': 0, 'incapable': count}
                        for room, count in reachable_from_exit.items()
                    }

                    temp_state = dict(state)
                    temp_state['discovered_occupants'] = temp_discovered

                    # Override firefighter position to this exit for item generation
                    temp_ff_state = dict(state['firefighters'])
                    temp_ff_state[ff_id] = dict(ff_state)
                    temp_ff_state[ff_id]['position'] = exit_id
                    temp_state['firefighters'] = temp_ff_state

                    # Generate items from this exit
                    exit_items = self.optimizer.generate_items(temp_state)

                    # Find best item from this exit
                    for item in exit_items:
                        value_ratio = item['value'] / max(item['time'], 0.1)
                        if value_ratio > best_value_ratio:
                            best_value_ratio = value_ratio
                            best_item = item
                            best_entry_exit = exit_id

                if not best_item:
                    print(f"  [{ff_id}] No reachable rooms from any exit")
                    continue

                # If best quest is from a different exit, we'll teleport there
                if best_entry_exit != current_pos:
                    print(f"  [{ff_id}] Best quest is from {best_entry_exit}, will teleport from {current_pos}")

                # Ensure the item uses the correct entry_exit
                best_item['entry_exit'] = best_entry_exit

                # Update remaining occupants
                for room, count in best_item['vector'].items():
                    self.remaining_occupants[room] = max(0, self.remaining_occupants.get(room, 0) - count)
                    if self.remaining_occupants[room] == 0:
                        del self.remaining_occupants[room]

                # Create plan and assign
                plan = ItemExecutionPlan(best_item)

                if ff_id not in self.ff_plans:
                    self.ff_plans[ff_id] = []
                    self.ff_current_idx[ff_id] = 0

                self.ff_plans[ff_id].append(plan)

                total_people = sum(best_item['vector'].values())
                rooms_list = ', '.join(best_item['vector'].keys())
                print(f"  [{ff_id}] Quest claimed: Rescue {total_people} people from {len(best_item['vector'])} rooms ({rooms_list})")

    def _bfs_distance(self, start: str, goal: str, graph: Dict) -> Optional[int]:
        """
        Calculate BFS distance between two vertices.

        Args:
            start: Starting vertex ID
            goal: Goal vertex ID
            graph: State graph from sim.read()

        Returns:
            Number of edges in shortest path, or None if unreachable
        """
        if start == goal:
            return 0

        vertices = graph['vertices']
        edges = graph['edges']

        # Build adjacency, skipping burned edges
        adjacency = {v_id: [] for v_id in vertices}
        for edge_data in edges.values():
            if not edge_data['exists']:
                continue
            va = edge_data['vertex_a']
            vb = edge_data['vertex_b']
            adjacency[va].append(vb)
            adjacency[vb].append(va)

        # BFS
        queue = [(start, 0)]
        visited = {start}

        while queue:
            node, dist = queue.pop(0)

            if node == goal:
                return dist

            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))

        return None  # Unreachable
