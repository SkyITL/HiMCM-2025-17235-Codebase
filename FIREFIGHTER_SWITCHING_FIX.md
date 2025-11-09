# Firefighter Selection Cycling Fix

## Problem
When two or more firefighters were at the same position (same vertex), clicking on them would always select the first one. There was no way to switch between them.

## Solution

### 1. Cycle Detection Logic
Updated the click handling to:
- Find **all** firefighters at the clicked position
- If the currently selected firefighter is one of them, cycle to the **next** one
- Use modulo arithmetic to wrap around (ff_0 → ff_1 → ff_0 → ...)

### 2. Visual Indicator
Added a yellow badge showing the count when multiple firefighters occupy the same position:
- Badge displays "x2", "x3", etc.
- Positioned at top-right of the vertex
- Only drawn once per position (by the first firefighter in the list)

### 3. Position-Aware Positioning
Fixed firefighter rendering to offset based on **local** position:
- Before: Offset was based on global firefighter index (wrong!)
- After: Offset based on how many are at **this specific position**
- Firefighters arranged in a circle around the vertex center

### 4. Console Feedback
Added helpful messages when selecting/switching:
```
Selected ff_0 (1/2 at this location)
Switched to ff_1 (2/2 at this location)
Switched to ff_0 (1/2 at this location)
```

## Implementation Details

### Cycling Logic
```python
# Find all firefighters at clicked position
clicked_firefighters = [...]

if self.selected_firefighter in clicked_firefighters and len(clicked_firefighters) > 1:
    # Cycle to next
    current_idx = clicked_firefighters.index(self.selected_firefighter)
    next_idx = (current_idx + 1) % len(clicked_firefighters)
    self.selected_firefighter = clicked_firefighters[next_idx]
else:
    # Select first one
    self.selected_firefighter = clicked_firefighters[0]
```

### Visual Badge
```python
if ff_count > 1 and ff_index == 0:  # Only draw once per position
    badge_pos = (base_pos[0] + 25, base_pos[1] - 25)
    pygame.draw.circle(screen, (255, 200, 0), badge_pos, 10)  # Yellow
    text = font.render(f"x{ff_count}", ...)
```

### Position-Aware Offset
```python
# Count firefighters at SAME position (not all firefighters)
firefighters_at_same_pos = [
    fid for fid, f in sim.firefighters.items()
    if f.position == ff.position
]

ff_count = len(firefighters_at_same_pos)
ff_index = firefighters_at_same_pos.index(ff_id)

# Arrange in circle
offset_angle = ff_index * (2 * pi / ff_count)
```

## Testing

Created `test_firefighter_switching.py` to verify:
1. Multiple firefighters can occupy same position
2. Cycling logic works correctly
3. Wraps around properly (last → first)

**Test Results:**
```
✓ SUCCESS! Both firefighters are at hallway_left
✓ Cycling logic works correctly!
  First click: Selected ff_0 (1/2)
  Second click: Cycled to ff_1 (2/2)
  Third click: Cycled to ff_0 (1/2)
```

## User Experience

### Before:
- Click on overlapping firefighters → always selects same one
- No visual indication of overlap
- Can't control both firefighters independently

### After:
- Click once → selects first firefighter
- Click again → cycles to next firefighter
- Yellow "x2" badge shows there are multiple
- Console shows which one is selected (1/2, 2/2, etc.)
- Can now control all firefighters even when overlapping!

## Files Modified

- `visualizer.py`:
  - Updated click handling logic (lines ~470-505)
  - Modified `draw_firefighter()` to accept `firefighters_at_same_pos` parameter
  - Added position-aware offset calculation
  - Added yellow badge rendering

- `demo_visualizer.py`:
  - Updated controls description
  - Added tip about cycling

- `README.md`:
  - Updated controls section
  - Added badge to visual guide

- `test_firefighter_switching.py`:
  - New test file to verify functionality

## Use Cases

This is particularly useful when:
1. Both firefighters return to the same exit
2. Firefighters meet in a hallway
3. Multiple firefighters sweeping the same area
4. Strategic positioning for coordinated actions

## Future Enhancements

Possible improvements:
- Keyboard shortcuts (Tab to cycle)
- Different colors for each firefighter
- Draw lines connecting firefighters at same position
- Show selection number in larger font
