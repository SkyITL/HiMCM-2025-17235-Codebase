# Visualization Guide for Stuck Scenarios

This guide explains how to visualize the different types of failures in the optimal rescue model.

## Available Visualizations

### 1. Seed 6 - Sweep Stuck (0 replans)
```bash
python3 visualize_trapped_seed6.py
```

**What to watch for:**
- Fire origin: room_2
- Gets stuck during **exploration phase** around tick 109
- Both firefighters complete their MST paths but don't visit remaining rooms
- 3 unvisited rooms: room_12, room_13, room_14
- 0 replans triggered
- 23/48 occupants rescued when stuck

**Root cause:** Sweep coordinator not assigning remaining rooms after MST paths complete

---

### 2. Seed 1 - Rescue Stuck (20 replans)
```bash
python3 visualize_trapped_seed1.py
```

**What to watch for:**
- Fire origin: room_2
- Gets stuck during **rescue phase**
- Many replans triggered (~20)
- Firefighters may get trapped by fire blocking paths
- Constant replanning as graph topology changes

**Root cause:** Fire disrupting plans repeatedly, possible trapped firefighter scenarios

---

### 3. Seed 3 - Rescue Stuck (moderate replans)
```bash
python3 visualize_trapped_seed3.py
```

**What to watch for:**
- Fire origin: room_10
- Gets stuck during **rescue phase**
- Moderate number of replans
- Similar pattern to seed 1 but different fire origin

**Root cause:** Fire disrupting rescue operations

---

## Controls

All visualizations support these controls:
- **SPACE**: Pause/Resume
- **Q or ESC**: Quit
- **+ / -**: Adjust simulation speed

## Benchmark Results Context

From the 100-trial benchmark (2 firefighters):
- **51 completed** successfully (51%)
- **11 stuck in sweep** (0 replans) - like seed 6
- **38 stuck in rescue** (moderate replans) - like seeds 1 and 3

## Debug Scripts

For detailed text output without visualization:

```bash
python3 debug_stuck_detailed.py
```

This runs seeds 6, 3, and 11 and shows detailed status including:
- Phase changes
- Replan events
- Firefighter positions and actions
- Unvisited rooms
- When firefighters get stuck

## Next Steps

The visualizations reveal two main issues to fix:

1. **Sweep stuck**: Sweep coordinator needs to assign remaining rooms after MST completion
2. **Rescue stuck**: Better trapped firefighter detection or alternative strategies when paths are blocked
