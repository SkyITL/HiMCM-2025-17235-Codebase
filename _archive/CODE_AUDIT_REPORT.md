# Code Audit Report: Current Model State

## Date: 2025-11-15

## Overview
This audit reviews the current state of the optimal rescue model to identify issues with fire-based weighting and replanning functionality.

---

## 1. Fire-Based Weighting Status

### ✅ IMPLEMENTED CORRECTLY

**File: `optimal_rescue_model.py`**
- Constructor accepts `fire_priority_weight` parameter (line 37)
- Passes weight to optimizer (line 56)
- Displays weight in initialization message (line 59)

**File: `optimal_rescue_optimizer.py`**
- Constructor accepts `fire_priority_weight` parameter (line 34)
- Stores weight as instance variable (line 48)
- Initializes `fire_distances` dict (line 51)

**Fire Distance Computation** (`optimal_rescue_optimizer.py:110-125`):
- Checks if `fire_priority_weight > 0.0` before computing
- Runs Dijkstra from fire origin to all rooms with incapable occupants
- Stores distances in `self.fire_distances`
- Properly handles missing fire_origin

**Item Generation** (`optimal_rescue_optimizer.py:194-204`):
- Passes `fire_distances` and `fire_priority_weight` to `compute_optimal_item_for_vector`
- Correct parameter threading through the call chain

**Value Calculation** (`pathfinding.py:324-344`):
```python
# Calculates priority-weighted value with fire proximity boost
for room in vector:
    people_count = vector[room]
    base_priority = room_priorities.get(room, 1)

    # Apply fire proximity multiplier if enabled
    if fire_priority_weight > 0.0 and fire_distances:
        fire_dist = fire_distances.get(room, float('inf'))
        if fire_dist < float('inf'):
            # Closer to fire = higher multiplier
            proximity_factor = 1.0 + (fire_priority_weight / (1.0 + fire_dist))
            total_priority_value += people_count * base_priority * proximity_factor
```

### ✅ VERDICT: Fire weighting is FULLY IMPLEMENTED and WORKING

---

## 2. Replanning Status

### ❌ CRITICAL ISSUE: REPLANNING IS **COMPLETELY MISSING**

**The Problem:**
The previous implementation had adaptive replanning when edges burned. **This functionality has been completely removed.**

### Evidence of Missing Replanning:

#### File: `optimal_rescue_model.py`
**What's MISSING:**
- No detection of burned edges
- No call to `coordinator.handle_replanning()`
- No replan counter
- No replan trigger logic

**Current flow** (`optimal_rescue_model.py:61-81`):
```python
def get_actions(self, state: Dict) -> Dict[str, List[Dict]]:
    # Check if should switch to optimal rescue phase
    if self._should_switch_phase(state) and not self.phase_switched:
        self._switch_to_optimal_rescue(state)

    # Generate actions based on current phase
    if self.phase == 'exploration':
        return self._exploration_actions(state)
    else:
        return self.coordinator.get_actions_for_tick(state)  # NO REPLANNING CHECK
```

There is **NO CODE** that:
1. Detects when edges have burned
2. Identifies which firefighters are affected
3. Triggers replanning for affected plans
4. Regenerates items for affected rooms

#### File: `tactical_coordinator.py`
**What's PRESENT:**
- `truncate_to_unaltered()` method exists (lines 107-159)
- `get_affected_vector()` method exists (lines 161-175)
- Infrastructure for handling plan truncation is in place

**What's MISSING:**
- No `handle_replanning()` method
- No detection of burned edges
- No automatic plan adjustment
- The truncation methods are **NEVER CALLED**

### Expected Replanning Flow (from previous implementation):

```python
# This should exist in optimal_rescue_model.py but DOESN'T:

def get_actions(self, state: Dict) -> Dict[str, List[Dict]]:
    if self.phase == 'optimal_rescue':
        # Check for burned edges each tick
        burned_edges = self._detect_burned_edges(state)

        if burned_edges:
            # Trigger replanning
            self.replan_count += 1
            self.coordinator.handle_replanning(state, burned_edges)
            self.optimizer.regenerate_items_for_affected_rooms(state)

    # Then get actions...
```

### ❌ VERDICT: Replanning is **NOT WORKING** - completely removed from codebase

---

## 3. Optimizer Changes Review

### Distance Matrix Changes (CORRECT)

**Old approach** (removed):
- Computed two distance matrices: `distance_unloaded` and `distance_loaded`
- Pre-applied carrying penalty (2×) to all loaded paths
- Inefficient: doubled memory usage

**New approach** (current):
- Single `distance_matrix` with base geometric distances
- Carrying penalty applied dynamically in `compute_optimal_item_for_vector`
- More flexible and memory-efficient

### Pathfinding Changes (CORRECT)

**Node weight removal**:
- **Old**: `node_weight = sqrt(2 * area)` - accounted for diagonal room traversal
- **New**: `node_weight = 0.0` - simplified to edge-only costs (1 meter per edge)
- This is correct for the mall model where all edges are 1 meter

**Carrying penalty application**:
```python
# Get base distance
dist, path = distance_matrix[current][room]

# Apply 2× penalty ONLY when carrying people
if current_carrying > 0:
    dist *= 2.0
```

This is **CORRECT** - penalty applied dynamically based on carrying state.

---

## 4. Under-Capacity Penalty (IMPLEMENTED)

**File: `optimal_rescue_optimizer.py:42-47`**
```python
def __init__(
    self,
    k_capacity: Dict[str, int] = None,
    under_capacity_penalty: float = 0.1,  # ← Penalty parameter
    fire_priority_weight: float = 0.0
):
    self.under_capacity_penalty = under_capacity_penalty
```

**File: `pathfinding.py:350-357`**
```python
# Apply under-capacity penalty
people_rescued = sum(vector.values())
if people_rescued < k_capacity:
    shortfall = k_capacity - people_rescued
    penalty_factor = 1.0 - (shortfall * under_capacity_penalty)
    value = value * penalty_factor
```

### ✅ VERDICT: Under-capacity penalty is WORKING

---

## 5. Summary of Issues

| Feature | Status | Severity |
|---------|--------|----------|
| Fire-based weighting | ✅ Working | N/A |
| Under-capacity penalty | ✅ Working | N/A |
| Distance optimization | ✅ Working | N/A |
| **Adaptive replanning** | ❌ **MISSING** | **CRITICAL** |
| Edge burn detection | ❌ **MISSING** | **CRITICAL** |
| Plan truncation trigger | ❌ **MISSING** | **CRITICAL** |

---

## 6. Impact Analysis

### Without Replanning:
1. **Firefighters get trapped**: When an edge burns, firefighters following precomputed paths cannot adapt
2. **Paths become invalid**: Movement actions fail when trying to traverse burned edges
3. **People left behind**: Rooms that become unreachable are abandoned
4. **Model appears broken**: High death rates in benchmarks due to firefighters stuck

### Symptoms in Benchmarks:
- From the 20-trial test: **Average 10.55 replans**
  - This suggests the model IS trying to replan somehow
  - But the code review shows no replanning logic exists
  - **CONTRADICTION** - need to investigate benchmark_mall_fast.py

---

## 7. Recommendation: Restore Replanning

### Required Implementation:

#### A. In `optimal_rescue_model.py`:

```python
def __init__(self, ...):
    # Add replan tracking
    self.replan_count = 0
    self.last_graph_hash = None

def get_actions(self, state: Dict) -> Dict[str, List[Dict]]:
    # After phase switch check, before generating actions:
    if self.phase == 'optimal_rescue':
        graph_changed = self._detect_graph_changes(state)
        if graph_changed:
            self._handle_replanning(state)

    # Then proceed with action generation...

def _detect_graph_changes(self, state: Dict) -> bool:
    """Check if any edges have burned since last tick."""
    current_hash = self._compute_graph_hash(state['graph'])
    changed = (current_hash != self.last_graph_hash)
    self.last_graph_hash = current_hash
    return changed

def _handle_replanning(self, state: Dict):
    """Trigger replanning when graph changes."""
    print(f"\n⚠️  REPLANNING TRIGGERED (graph changed)")
    self.replan_count += 1

    # Delegate to coordinator
    affected_people = self.coordinator.handle_graph_change(state, self.optimizer)

    print(f"   Replanning complete. Affected people: {affected_people}")
```

#### B. In `tactical_coordinator.py`:

```python
def handle_graph_change(self, state: Dict, optimizer: RescueOptimizer) -> int:
    """
    Adapt all plans to graph changes (burned edges).

    For each firefighter:
    1. Check if their current plan path is still valid
    2. If invalid, truncate plan to remove unreachable rooms
    3. Collect affected people (rooms we can't reach)
    4. Regenerate items for affected rooms
    5. Reassign to available firefighters
    """
    total_affected = 0
    affected_vectors = []

    # Check each firefighter's plan
    for ff_id, plans in self.ff_plans.items():
        idx = self.ff_current_idx.get(ff_id, 0)
        if idx >= len(plans):
            continue  # No active plan

        current_plan = plans[idx]

        # Check if path is still valid
        unaltered, affected = self._partition_rooms_by_reachability(
            current_plan, state
        )

        if affected:
            # Plan is affected - truncate
            current_plan.truncate_to_unaltered(
                unaltered, affected,
                nearest_exit=self._find_nearest_exit(state),
                graph=state['graph']
            )

            # Collect affected people
            affected_vec = current_plan.get_affected_vector()
            if affected_vec:
                affected_vectors.append(affected_vec)
                total_affected += sum(affected_vec.values())

    # Regenerate items for affected people
    if affected_vectors:
        new_items = optimizer.regenerate_items_for_affected(
            state, affected_vectors
        )
        # Reassign to firefighters with capacity
        self._assign_new_items(new_items, state)

    return total_affected
```

---

## 8. Benchmark Discrepancy

**Question**: The 20-trial benchmark showed **10.55 average replans**, but no replanning code exists.

**Hypothesis**: The benchmark might be:
1. Counting something else as "replans" (e.g., phase switches?)
2. Using a different model file
3. Running old code from a previous session

**Action Required**: Check `benchmark_mall_fast.py` to see what it's counting as replans.

---

## 9. Files Requiring Changes

To restore full functionality:

| File | Changes Needed |
|------|----------------|
| `optimal_rescue_model.py` | Add replan detection and triggering |
| `tactical_coordinator.py` | Add `handle_graph_change()` method |
| `optimal_rescue_optimizer.py` | Add `regenerate_items_for_affected()` |
| `pathfinding.py` | No changes needed ✅ |
| `simulator.py` | No changes needed ✅ |

---

## Conclusion

**Fire weighting**: ✅ Fully functional
**Replanning**: ❌ Completely missing - needs to be re-implemented

The model will not adapt to dynamic fire spread without replanning logic.
