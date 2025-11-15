# Critical Bug Analysis: Firefighters Stuck After Sweep

## Summary

Firefighters complete the sweep phase but then get stuck with empty queues, even though 20+ occupants remain in the building.

## Root Cause

**File:** `optimal_rescue_model.py:160-186`

The `_switch_to_optimal_rescue()` function only counts **incapable** occupants from `discovered_occupants`:

```python
# Line 178-182
discovered = state['discovered_occupants']
total_incapable = sum(
    occ['incapable'] for occ in discovered.values()
)
print(f"Remaining incapable occupants: {total_incapable}")

if total_incapable == 0:
    print("No incapable occupants remaining - staying in exploration mode")
    return
```

## The Problem Sequence

1. **During Sweep Phase:**
   - Firefighters visit all rooms
   - They instruct **capable** occupants to self-evacuate
   - These occupants are marked as "instructed" in `discovered_occupants`

2. **Occupants Become Incapacitated:**
   - Instructed occupants try to evacuate
   - Many get stuck due to smoke/fire blocking paths
   - They become **incapacitated** over time (smoke inhalation)
   - BUT they're still marked as "instructed capable" in `discovered_occupants`

3. **Phase Transition Fails:**
   - `_switch_to_optimal_rescue()` only looks for `incapable` occupants
   - Finds 0 incapable (because they were all "capable" when discovered)
   - Returns early without generating rescue items
   - Firefighters have empty queues and do nothing

4. **Result:**
   - 28 occupants remain in building (now incapacitated from smoke)
   - Firefighters stuck with no tasks
   - Simulation times out

## Evidence from Seed 6

```
⚠️  STUCK at tick 139
   Phase: exploration
   Remaining: 28
   Rescued: 23
   Dead: 0

   ff_0: pos=room_18                        | queue=0 | actions=[NONE]
   ff_1: pos=ersection_17_intersection_16_1 | queue=0 | actions=[NONE]

Analyzing rooms with occupants:

   Found 0 rooms with occupants  <-- THIS IS THE SMOKING GUN

Coordinator status:
   Items in coordinator:  <-- EMPTY!
```

The 28 remaining occupants are:
- Marked as "instructed capable" in `discovered_occupants`
- Actually incapacitated in hallways/intersections trying to evacuate
- NOT visible in room occupant counts
- NOT being rescued because transition aborted

## Fix Required

The transition should check for **ALL remaining occupants**, not just incapable ones:

```python
# Instead of only counting incapable:
total_incapable = sum(occ['incapable'] for occ in discovered.values())

# Should count ALL discovered occupants that haven't been rescued:
total_remaining = sum(
    occ['count'] - occ.get('rescued', 0)
    for occ in discovered.values()
)
```

Or better yet, use `sim.get_stats()['remaining']` which gives the true count of all non-rescued occupants.

## Impact

This bug affects approximately **49% of trials** (the ones that get stuck). The 51% success rate is only achieved when:
- All capable occupants successfully self-evacuate, OR
- Incapable occupants exist from the start

This explains why we went from 39% → 51% after fixing the replan position bug, but couldn't get higher.
