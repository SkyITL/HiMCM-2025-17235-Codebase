#!/usr/bin/env python3
"""
Optimal Rescue Model - Two-phase evacuation strategy.

Phase 1: Exploration
- Instruct capable occupants to evacuate
- Discover all rooms (fog of war)
- Basic greedy rescue of encountered incapable people

Phase 2: Optimal Rescue
- Activate when: all rooms visited + all capable instructed
- Run optimization algorithm (greedy or LP)
- Execute optimized rescue plans via tactical coordinator

This model implements the algorithm from the HiMCM paper.
"""

from typing import Dict, List, Optional
import pathfinding
from optimal_rescue_optimizer import RescueOptimizer
from tactical_coordinator import TacticalCoordinator


class OptimalRescueModel:
    """
    Two-phase evacuation model with optimal rescue algorithm.

    Usage:
        model = OptimalRescueModel(k_capacity={'ff_0': 3, 'ff_1': 3}, use_lp=False)

        while not done:
            state = sim.read()
            actions = model.get_actions(state)
            results = sim.update(actions)
    """

    def __init__(self, k_capacity: Dict[str, int] = None, use_lp: bool = False):
        """
        Initialize optimal rescue model.

        Args:
            k_capacity: {firefighter_id: max_capacity} for each firefighter
                       If None, uses default k=3 for all
            use_lp: If True, use LP solver for optimal assignment
                   If False, use greedy algorithm (faster)
        """
        self.phase = 'exploration'
        self.use_lp = use_lp
        self.phase_switched = False

        # Initialize components
        self.optimizer = RescueOptimizer(k_capacity)
        self.coordinator = TacticalCoordinator()

        print(f"OptimalRescueModel initialized (use_lp={use_lp})")

    def get_actions(self, state: Dict) -> Dict[str, List[Dict]]:
        """
        Main entry point: generate actions for all firefighters.

        This is called once per tick by the simulator.

        Args:
            state: Full state from sim.read()

        Returns:
            {firefighter_id: [action1, action2]}
        """
        # Check if should switch to optimal rescue phase
        if self._should_switch_phase(state) and not self.phase_switched:
            self._switch_to_optimal_rescue(state)

        # Generate actions based on current phase
        if self.phase == 'exploration':
            return self._exploration_actions(state)
        else:
            return self.coordinator.get_actions_for_tick(state)

    def _should_switch_phase(self, state: Dict) -> bool:
        """
        Check if should switch from exploration to optimal rescue.

        Criteria:
        1. All rooms have been visited at least once
        2. All capable occupants have been instructed

        Args:
            state: Full state from sim.read()

        Returns:
            True if should switch phases
        """
        # Check 1: All rooms visited
        graph = state['graph']
        all_rooms = [
            v_id for v_id, v_data in graph['vertices'].items()
            if v_data['type'] == 'room'
        ]

        visited_rooms = set()
        for ff_state in state['firefighters'].values():
            visited_rooms.update(ff_state['visited_vertices'])

        all_rooms_visited = all(room in visited_rooms for room in all_rooms)

        # Check 2: All capable instructed
        discovered = state['discovered_occupants']
        all_capable_instructed = all(
            occupants['capable'] == 0
            for occupants in discovered.values()
        )

        return all_rooms_visited and all_capable_instructed

    def _switch_to_optimal_rescue(self, state: Dict):
        """
        Execute one-time phase transition to optimal rescue.

        Steps:
        1. Preprocess distances (Dijkstra all-pairs)
        2. Generate all rescue items
        3. Run greedy or LP assignment
        4. Load assignments into tactical coordinator

        Args:
            state: Full state from sim.read()
        """
        print("\n" + "="*60)
        print("PHASE TRANSITION: Switching to Optimal Rescue Mode")
        print("="*60)

        # Get remaining incapable occupants
        discovered = state['discovered_occupants']
        total_incapable = sum(
            occ['incapable'] for occ in discovered.values()
        )
        print(f"Remaining incapable occupants: {total_incapable}")

        if total_incapable == 0:
            print("No incapable occupants remaining - staying in exploration mode")
            return

        # Step 1: Preprocessing
        print("\nStep 1: Preprocessing distances...")
        self.optimizer.preprocess_distances(state)

        # Step 2: Generate items
        print("\nStep 2: Generating rescue items...")
        items = self.optimizer.generate_items(state)

        if not items:
            print("No valid items generated - staying in exploration mode")
            return

        # Step 3: Assignment
        print(f"\nStep 3: Assigning items ({'LP' if self.use_lp else 'Greedy'})...")

        if self.use_lp:
            # Use LP solver (if implemented)
            try:
                from lp_rescue_optimizer import lp_optimal_assignment
                assignments = lp_optimal_assignment(items, state)
            except ImportError:
                print("Warning: LP solver not available, falling back to greedy")
                assignments = self.optimizer.greedy_assignment(items, state)
        else:
            # Use greedy algorithm
            assignments = self.optimizer.greedy_assignment(items, state)

        if not assignments:
            print("No assignments generated - staying in exploration mode")
            return

        # Step 4: Load into coordinator
        print("\nStep 4: Loading assignments into tactical coordinator...")
        self.coordinator.assign_items(assignments)

        # Log detailed assignments
        print("\n" + "="*60)
        print("CHOSEN ITEM ASSIGNMENTS")
        print("="*60)
        for ff_id in sorted(assignments.keys()):
            items = assignments[ff_id]
            print(f"\n{ff_id}: {len(items)} items assigned")
            total_time = 0
            total_people = 0
            for idx, item in enumerate(items):
                people = sum(item['vector'].values())
                total_people += people
                total_time += item['time']

                # Format vector nicely (only show rooms with count > 0)
                vector_str = ', '.join([f"{room}:{count}" for room, count in item['vector'].items() if count > 0])

                print(f"  {idx+1}. Rescue {people} from [{vector_str}]")
                print(f"     Route: {item['entry_exit']} → {' → '.join(item['visit_sequence'])} → {item['drop_exit']}")
                print(f"     Time: {item['time']:.1f}s, Value: {item['value']:.3f}")

            print(f"  {ff_id} subtotal: {total_people} people, ~{total_time:.0f}s estimated")

        # Calculate total
        total_assigned = sum(sum(item['vector'].values()) for items in assignments.values() for item in items)
        print(f"\nGrand total: {total_assigned}/{total_incapable} people assigned ({total_assigned/total_incapable*100:.1f}%)")

        # Transition complete
        self.phase = 'optimal_rescue'
        self.phase_switched = True

        print("\n" + "="*60)
        print("PHASE TRANSITION COMPLETE - Now in Optimal Rescue Mode")
        print("="*60 + "\n")

    def _exploration_actions(self, state: Dict) -> Dict[str, List[Dict]]:
        """
        Phase 1: Exploration strategy.

        Simple greedy approach:
        - Priority 1: If carrying + at exit → drop off
        - Priority 2: If carrying → move toward exit
        - Priority 3: If at room with capable → instruct
        - Priority 4: If at room with incapable → pick up
        - Priority 5: Move to nearest unvisited room

        Args:
            state: Full state from sim.read()

        Returns:
            {firefighter_id: [action1, action2]}
        """
        actions = {}

        for ff_id, ff_state in state['firefighters'].items():
            ff_actions = []
            current_pos = ff_state['position']
            carrying = ff_state['carrying_incapable']
            visited = set(ff_state['visited_vertices'])

            # Get current vertex info
            vertex = state['graph']['vertices'][current_pos]
            discovered = state['discovered_occupants'].get(current_pos)

            # Priority 1: Drop off if carrying and at exit
            if carrying > 0 and vertex['type'] in ['exit', 'window_exit']:
                ff_actions.append({'type': 'drop_off', 'count': 'all'})

            # Priority 2: Move toward exit if carrying
            elif carrying > 0:
                next_step = self._find_path_to_nearest_exit(current_pos, state)
                if next_step:
                    ff_actions.append({'type': 'move', 'target': next_step})

            # Priority 3: Instruct if capable people present
            elif discovered and discovered['capable'] > 0:
                ff_actions.append({'type': 'instruct'})

            # Priority 4: Pick up if incapable people present
            elif discovered and discovered['incapable'] > 0:
                capacity = ff_state['max_carry_capacity']
                can_carry = capacity - carrying
                if can_carry > 0:
                    ff_actions.append({'type': 'pick_up_incapable', 'count': min(1, can_carry)})

            # Priority 5: Explore - move to nearest unvisited room
            else:
                next_step = self._find_path_to_unvisited_room(current_pos, visited, state)
                if next_step:
                    ff_actions.append({'type': 'move', 'target': next_step})

            # Fill second action if possible
            if len(ff_actions) == 1:
                # Try to take another step toward goal
                if ff_actions[0]['type'] == 'move':
                    # Simulate being at next position
                    next_pos = ff_actions[0]['target']
                    next_next = self._get_next_move_from(next_pos, current_pos, visited, state)
                    if next_next:
                        ff_actions.append({'type': 'move', 'target': next_next})

            actions[ff_id] = ff_actions[:2]

        return actions

    def _find_path_to_nearest_exit(self, current: str, state: Dict) -> Optional[str]:
        """Find next step toward nearest exit using BFS."""
        exits = pathfinding.find_exits(state['graph'])

        for exit_id in exits:
            next_step = pathfinding.bfs_next_step(current, exit_id, state['graph'])
            if next_step:
                return next_step

        return None

    def _find_path_to_unvisited_room(
        self,
        current: str,
        visited: set,
        state: Dict
    ) -> Optional[str]:
        """Find next step toward nearest unvisited room using BFS."""
        graph = state['graph']

        # Find all unvisited rooms
        unvisited_rooms = [
            v_id for v_id, v_data in graph['vertices'].items()
            if v_data['type'] == 'room' and v_id not in visited
        ]

        if not unvisited_rooms:
            return None  # All rooms visited

        # Try to find path to nearest unvisited room
        for room in unvisited_rooms:
            next_step = pathfinding.bfs_next_step(current, room, graph)
            if next_step:
                return next_step

        return None

    def _get_next_move_from(
        self,
        current: str,
        avoid: str,
        visited: set,
        state: Dict
    ) -> Optional[str]:
        """
        Get next move from current position.
        Used for filling second action slot during exploration.
        """
        # Try to continue toward unvisited room
        next_step = self._find_path_to_unvisited_room(current, visited, state)
        if next_step and next_step != avoid:
            return next_step

        return None

    def get_status(self) -> str:
        """
        Get current status of the model.

        Returns:
            Status string describing current phase and progress
        """
        if self.phase == 'exploration':
            return "Phase: Exploration (discovering rooms, instructing capable)"
        else:
            status = self.coordinator.get_status()
            return f"Phase: Optimal Rescue\n" + "\n".join(
                f"  {ff_id}: {s}" for ff_id, s in status.items()
            )
