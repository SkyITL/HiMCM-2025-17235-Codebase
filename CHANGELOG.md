# Visualizer Improvements Changelog

## Summary of Changes

Three major improvements to the emergency evacuation visualizer based on user feedback:

### 1. Fog of War (Information Hiding) ✅
**Problem**: In manual mode, player could see all room occupancy counts immediately.

**Solution**:
- Unvisited rooms now display "?" instead of occupant count
- Only rooms that have been visited by firefighters show actual occupancy
- Auto mode still shows all counts (for AI testing)

**Implementation**:
- Added `show_all_occupants` and `visited_vertices` parameters to `draw_vertex()`
- Auto mode: `show_all_occupants=True` (see everything)
- Manual mode: `show_all_occupants=False` (fog of war enabled)

### 2. Reduced Smoke Death Rate ✅
**Problem**: Smoke was killing people too quickly - 15 deaths in 52 ticks.

**Solution**:
- Reduced death probability by ~5x
- Changed formula: `smoke_level^3 * 0.02` (was `smoke_level^2 * 0.1`)
- At 50% smoke: ~0.2% death rate per tick (was ~2.5%)
- At 100% smoke: ~2% death rate per tick (was ~10%)

**Results**:
- Before: 15 deaths by tick 52 (0.87 min)
- After: 11 deaths by tick 100 (1.67 min)
- Much more forgiving - gives players more time to rescue

### 3. Manual Mode Time Control ✅
**Problem**: Every action (move, pick up, drop off) immediately advanced time, making it hard to plan.

**Solution**:
- Actions are now **queued** instead of executed immediately
- Time ONLY advances when "Step" button is clicked
- Pending actions shown in status bar: "Pending: X actions"
- Can queue multiple actions per firefighter per tick

**Implementation**:
- Added `pending_actions: Dict[str, List]` to visualizer
- `_manual_move()` and `_manual_action()` now queue actions
- "Step" button executes all queued actions via `sim.update()`
- Console shows what's being queued and executed

**Benefits**:
- More strategic planning
- Can queue complex multi-action sequences
- Better matches turn-based strategy game feel
- Easier to understand cause and effect

## Visual Improvements

### Enhanced Smoke Visualization
- Smoke radius grows with smoke level
- Alpha values properly clamped to 255 (fixed crash bug)
- Smoke percentage displayed on rooms >20% smoke
- More visible gradient from light to dark gray

### UI Enhancements
- Survival rate shown in stats panel
- Escorting count shows capacity (e.g., "5/10")
- Pending actions count displayed
- Debug console output for all actions

## Testing

All changes tested and verified:
- `test_rescue_count.py` - Confirms rescued counting works correctly
- `test_visualizer_model.py` - Tests greedy AI with new smoke rate
- `test_visual.py` - 5-second visual test of pygame rendering

## Usage

### Manual Mode (New Workflow)
```bash
python3 demo_visualizer.py manual
```

1. Select firefighter by clicking on it
2. Click adjacent rooms to queue movement
3. Click "Pick Up" or "Drop Off" to queue actions
4. Click "Step" to execute all actions and advance time
5. Repeat!

### Auto Mode (Unchanged)
```bash
python3 demo_visualizer.py auto
```
AI controls firefighters automatically, shows all information.

## Files Modified

- `simulator.py` - Reduced smoke death rate in `apply_smoke_deaths()`
- `visualizer.py` - Added fog of war, action queuing, pending actions UI
- `demo_visualizer.py` - Updated instructions for new controls
- `README.md` - Updated documentation
- `test_visual.py` - Updated to use new draw_vertex parameters

## Breaking Changes

None! Auto mode works exactly as before. Only manual mode behavior changed.

## Future Improvements

Potential enhancements based on this foundation:
- Undo/redo for queued actions
- Show ghost/preview of queued movements
- Multi-select firefighters
- Keyboard shortcuts
- Save/load game state
- Replay mode to compare strategies
