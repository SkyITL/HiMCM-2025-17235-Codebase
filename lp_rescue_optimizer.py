#!/usr/bin/env python3
"""
Linear Programming optimizer for optimal rescue assignment.

Uses scipy's LP solver to find the mathematically optimal assignment
of rescue items to firefighters, maximizing total value while respecting
room capacity constraints.
"""

from typing import Dict, List
import numpy as np
from scipy.optimize import linprog


def lp_optimal_assignment(items: List[Dict], state: Dict) -> Dict[str, List[Dict]]:
    """
    Use Linear Programming to find optimal item assignment.

    Formulation:
        Variables: x_i ∈ [0,1] for each item i
        Objective: Maximize Σ(x_i × value_i)
        Constraints: For each room r: Σ(x_i × vector_i[r]) ≤ incapable_count[r]

    Args:
        items: List of rescue items from optimizer
        state: Full state from sim.read()

    Returns:
        {firefighter_id: [item1, item2, ...]} assignments
    """
    if not items:
        return {}

    print(f"LP Solver: Optimizing assignment of {len(items)} items...")

    # Extract problem parameters
    n_items = len(items)
    discovered = state['discovered_occupants']
    rooms = list(discovered.keys())

    # Build coefficient matrix A and bounds b
    # Constraint: A @ x <= b
    # For each room: sum of (x_i * vector_i[room]) <= incapable_count[room]

    A_ub = []  # Inequality constraint matrix
    b_ub = []  # Inequality constraint bounds

    for room in rooms:
        # Create constraint for this room
        constraint = []
        for item in items:
            # How many people does this item rescue from this room?
            count = item['vector'].get(room, 0)
            constraint.append(count)

        A_ub.append(constraint)
        b_ub.append(discovered[room]['incapable'])

    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)

    # Objective: maximize sum of (x_i * value_i)
    # linprog minimizes, so negate the coefficients
    c = np.array([-item['value'] for item in items])

    # Bounds: 0 <= x_i <= 1 for all i
    bounds = [(0, 1) for _ in range(n_items)]

    print(f"  Problem size: {n_items} variables, {len(rooms)} constraints")
    print(f"  Solving LP...")

    # Solve LP
    result = linprog(
        c=c,
        A_ub=A_ub,
        b_ub=b_ub,
        bounds=bounds,
        method='highs',  # Use HiGHS solver (fast and accurate)
        options={'disp': False}
    )

    if not result.success:
        print(f"  WARNING: LP solver failed: {result.message}")
        print(f"  Falling back to greedy heuristic")
        return _greedy_fallback(items, state)

    print(f"  LP solved successfully!")
    print(f"  Optimal objective value: {-result.fun:.3f}")

    # Extract solution
    x_solution = result.x

    # Convert continuous solution to discrete assignment
    # Strategy: Sort by x_i value, take items with x_i > threshold
    selected_items = []
    threshold = 0.01  # Include items with x_i > 1%

    for i, x_i in enumerate(x_solution):
        if x_i > threshold:
            selected_items.append((items[i], x_i))

    # Sort by selection value (x_i) descending
    selected_items.sort(key=lambda pair: pair[1], reverse=True)

    print(f"  Selected {len(selected_items)} items (x_i > {threshold})")

    # Assign to firefighters (round-robin by estimated time)
    firefighters = list(state['firefighters'].keys())
    assignments = {ff_id: [] for ff_id in firefighters}
    ff_times = {ff_id: 0.0 for ff_id in firefighters}

    # Greedy assignment: assign each item to firefighter with least time
    remaining = {room: discovered[room]['incapable'] for room in discovered}

    for item, x_i in selected_items:
        # Check if item violates remaining capacity
        valid = all(item['vector'].get(r, 0) <= remaining.get(r, 0) for r in item['vector'])

        if not valid:
            continue  # Skip items that would exceed capacity

        # Assign to firefighter with minimum current time
        ff_id = min(ff_times.keys(), key=lambda fid: ff_times[fid])
        assignments[ff_id].append(item)
        ff_times[ff_id] += item['time']

        # Update remaining capacity
        for room, count in item['vector'].items():
            remaining[room] -= count

    # Remove empty assignments
    assignments = {fid: items for fid, items in assignments.items() if items}

    # Print assignment summary
    total_assigned = sum(len(items) for items in assignments.values())
    print(f"  Assigned {total_assigned} items to {len(assignments)} firefighters")

    for ff_id in sorted(assignments.keys()):
        items_list = assignments[ff_id]
        total_people = sum(sum(item['vector'].values()) for item in items_list)
        total_time = sum(item['time'] for item in items_list)
        print(f"    {ff_id}: {len(items_list)} items, {total_people} people, ~{total_time:.0f}s")

    return assignments


def _greedy_fallback(items: List[Dict], state: Dict) -> Dict[str, List[Dict]]:
    """
    Fallback to greedy algorithm if LP fails.

    Args:
        items: List of items
        state: Full state

    Returns:
        Greedy assignment
    """
    from optimal_rescue_optimizer import RescueOptimizer
    optimizer = RescueOptimizer()
    return optimizer.greedy_assignment(items, state)
