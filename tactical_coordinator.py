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


class TacticalCoordinator:
    """
    Manages multi-tick execution of assigned rescue items.

    Responsibilities:
    - Maintain execution plans for each firefighter
    - Generate 2 actions per tick per firefighter
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
        Generate 2 actions per firefighter for current tick.

        This is the main entry point called by the model each tick.

        Args:
            state: Full state from sim.read()

        Returns:
            {ff_id: [action1, action2]} where actions are:
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

            # Generate 2 actions based on plan
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
        Convert execution plan into 2 concrete actions.

        Decision logic:
        0. If not at entry_exit → travel to entry_exit (Phase: travel_to_entry)
        1. If at pickup room and need to pick up → pickup action(s)
        2. If carrying and at drop exit → drop_off action
        3. If not at target → move toward target (follow precomputed path)
        4. If at waypoint → advance to next waypoint

        Args:
            plan: Current ItemExecutionPlan
            ff_state: Firefighter state from state['firefighters'][ff_id]
            state: Full state

        Returns:
            List of 0-2 actions
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
                # Use BFS to find path to entry
                import pathfinding
                next_step = pathfinding.bfs_next_step(current_pos, plan.entry_exit, state['graph'])
                if next_step:
                    actions.append({'type': 'move', 'target': next_step})

                    # Try second move
                    next_next = pathfinding.bfs_next_step(next_step, plan.entry_exit, state['graph'])
                    if next_next:
                        actions.append({'type': 'move', 'target': next_next})

                return actions[:2]

        # Phase 1: Execute the rescue plan

        # Case 1: At pickup room, need to pick up people
        if plan.at_pickup_location(current_pos):
            room = current_pos
            needed = plan.vector[room] - plan.rescued_so_far[room]
            can_carry = capacity - carrying

            if needed > 0 and can_carry > 0:
                # Pick up (use 1-2 actions)
                count1 = min(1, needed, can_carry)
                actions.append({'type': 'pick_up_incapable', 'count': count1})
                plan.rescued_so_far[room] += count1
                carrying += count1

                # Action 2: pick up more if needed and have room
                if len(actions) < 2 and needed > count1 and carrying < capacity:
                    count2 = min(1, needed - count1, capacity - carrying)
                    actions.append({'type': 'pick_up_incapable', 'count': count2})
                    plan.rescued_so_far[room] += count2
                    carrying += count2

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
            while target and target == current_pos:
                plan.advance_path()
                target = plan.get_current_target()

            if target and target != current_pos:
                # Move toward target
                actions.append({'type': 'move', 'target': target})
                plan.advance_path()

                # Action 2: Continue moving if possible
                if len(actions) < 2:
                    next_target = plan.get_current_target()
                    if next_target and next_target != current_pos:
                        actions.append({'type': 'move', 'target': next_target})
                        plan.advance_path()

        return actions[:2]  # Max 2 actions

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
