# Trapped Firefighter Item Redistribution - Implementation Plan

## Current Behavior (tactical_coordinator.py:441-444)

When a firefighter becomes trapped (no exits reachable):
```python
if nearest_exit is None:
    # Firefighter is completely trapped - no exits reachable
    print(f"   WARNING: {ff_id} is trapped (no exits reachable)")
    nearest_exit = current_plan.drop_exit  # Keep original, they're stuck anyway
```

**Problem**: The trapped firefighter keeps their remaining items, but can't execute them. These items are lost.

## Proposed Enhancement

When a firefighter becomes completely trapped:
1. **Detect** that no exits are reachable (`nearest_exit is None`)
2. **Extract** all remaining items from the trapped firefighter's queue
3. **Redistribute** those items to non-trapped firefighters
4. **Mark** the trapped firefighter as inactive (no more items)

## Implementation Location

File: `tactical_coordinator.py`
Method: `handle_graph_change()` (lines 371-497)
Specific location: Lines 441-444 (where trapped firefighters are detected)

## Detailed Implementation

### Step 1: Detect Trapped Firefighters

Already implemented:
```python
if nearest_exit is None:
    # Firefighter is completely trapped
```

### Step 2: Collect Remaining Items

Add after line 444:
```python
# Firefighter is completely trapped - redistribute their items
remaining_items = self.ff_plans[ff_id][idx+1:]  # All items after current
if remaining_items:
    print(f"   {ff_id} is trapped with {len(remaining_items)} remaining items - redistributing")

    # Collect all people from remaining items
    trapped_vector = {}
    for item_plan in remaining_items:
        for room, count in item_plan.vector.items():
            trapped_vector[room] = trapped_vector.get(room, 0) + count

    # Clear this firefighter's remaining items
    self.ff_plans[ff_id] = self.ff_plans[ff_id][:idx+1]  # Keep only current item

    # Add to affected vectors for redistribution
    if trapped_vector:
        affected_vectors.append(trapped_vector)
        count = sum(trapped_vector.values())
        total_affected += count
        print(f"   {ff_id}: {count} people from trapped firefighter's items will be redistributed")
```

### Step 3: Filter Out Trapped Firefighters from Reassignment

Modify the reassignment logic (lines 486-493) to exclude trapped firefighters:
```python
# Get list of non-trapped firefighters
active_firefighters = []
for ff_id, ff_state in state['firefighters'].items():
    # Check if this firefighter can reach any exit
    exits = pathfinding.find_exits(graph)
    for exit_id in exits:
        path = pathfinding.bfs_next_step(ff_state['position'], exit_id, graph)
        if path is not None:
            active_firefighters.append(ff_id)
            break

# Create temporary state with only active firefighters
temp_state['firefighters'] = {
    ff_id: state['firefighters'][ff_id]
    for ff_id in active_firefighters
}

# Run greedy assignment for new items (excluding trapped firefighters)
new_assignments = optimizer.greedy_assignment(new_items, temp_state)
```

## Benefits

1. **Improved survival rates**: Items from trapped firefighters are reassigned to active firefighters
2. **Better resource utilization**: No wasted rescue capacity
3. **Realistic behavior**: Mimics real emergency response where trapped responders' assignments are redistributed
4. **Automatic handling**: No manual intervention required

## Edge Cases

1. **All firefighters trapped**: If all firefighters are trapped, redistribution won't help. The system should detect this and continue without reassignment.

2. **Partially completed item**: If the trapped firefighter is in the middle of executing an item (has picked up some people but not all), those people being carried are lost (they die with the trapped firefighter).

3. **Multiple trapped firefighters**: The implementation handles this automatically by collecting items from all trapped firefighters into `affected_vectors`.

## Testing

Create test case:
1. 2 firefighters
2. Fire spreads to trap firefighter #1
3. Verify firefighter #1's remaining items are redistributed to firefighter #2
4. Verify survival rate improves compared to no redistribution

## Files Modified

- `tactical_coordinator.py`: Add trapped firefighter detection and item redistribution logic
