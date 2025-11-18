# Scroll and Pan Behavior - Updated!

## Changes Made

### ✓ Mouse Wheel Now Pans (Instead of Zoom)
**Previous:** Mouse wheel zoomed in/out
**Now:** Mouse wheel scrolls/pans the canvas

**Benefits:**
- More intuitive navigation
- Consistent with standard graphics applications
- Prevents accidental zoom changes

### ✓ Reduced Scroll Sensitivity
**Previous:** High sensitivity made scrolling jerky
**Now:** Smooth scrolling with reduced sensitivity (15 pixels per scroll notch)

**Technical Details:**
- Each scroll "notch" = 120 units
- Converted to 15 pixels of movement
- Approximately 1/8th the previous sensitivity

### ✓ Middle Mouse Button Panning
**New Feature:** Click and drag with middle mouse button to pan

**How it Works:**
- Press middle mouse button → cursor changes to closed hand
- Drag to pan in any direction
- Release → returns to normal mode

**Alternative:** Scroll wheel panning also works for vertical movement

## Usage Guide

### Navigation Methods

| Action | Method |
|--------|--------|
| **Pan Vertically** | Mouse wheel up/down |
| **Pan Horizontally** | Shift + Mouse wheel (if supported) OR Middle-drag |
| **Pan Any Direction** | Middle mouse button + drag |
| **Zoom** | Use scale slider at bottom of canvas |

### Workflow Tips

**Best Practice:**
1. Use **scale slider** to set overall zoom level (10-400%)
2. Use **mouse wheel** for quick vertical scrolling
3. Use **middle-click drag** for precise 2D panning

**When to Use Each:**
- **Scale Slider:** Setting specific zoom level (e.g., 200% for detail work)
- **Mouse Wheel:** Scrolling up/down through large graphs
- **Middle-Click Drag:** Fine-tuning view position in both X and Y

## Technical Implementation

### Mouse Wheel Event
```python
def wheelEvent(self, event):
    delta = event.angleDelta()
    pan_amount = 15  # pixels per scroll tick

    # Vertical scrolling
    if delta.y() != 0:
        scroll_amount = delta.y() / 120.0 * pan_amount
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value() - int(scroll_amount)
        )
```

### Middle Mouse Button Panning
```python
def mousePressEvent(self, event):
    if event.button() == Qt.MiddleButton:
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setCursor(Qt.ClosedHandCursor)
        # ... handle dragging

def mouseReleaseEvent(self, event):
    if event.button() == Qt.MiddleButton:
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setCursor(Qt.ArrowCursor)
```

## Comparison: Before vs After

### Before
```
Mouse Wheel       → Zoom in/out (high sensitivity)
Middle Mouse Drag → Not implemented
Scale Slider      → Zooms but conflicts with wheel
Panning           → Scroll bars only
```

### After
```
Mouse Wheel       → Smooth vertical pan (low sensitivity)
Middle Mouse Drag → Pan in any direction ✓
Scale Slider      → Precise zoom control (10-400%)
Panning           → Wheel + middle-click + scroll bars
```

## Benefits

1. **Better Control:** Zoom via slider is more precise than wheel
2. **Smooth Scrolling:** Reduced sensitivity prevents jumpy movement
3. **Flexible Panning:** Three ways to pan (wheel, middle-click, scrollbars)
4. **Standard Behavior:** Matches common graphics software (GIMP, Inkscape, etc.)
5. **No Conflicts:** Zoom and pan are separate operations

## Examples

### Scenario 1: Viewing Large Graph
```
1. Zoom out using slider (50%)
2. Scroll with mouse wheel to find area of interest
3. Zoom in using slider (150%)
4. Fine-tune position with middle-click drag
```

### Scenario 2: Precise Editing
```
1. Set zoom to 200% using slider
2. Middle-click drag to pan to exact location
3. Edit nodes/edges
4. Wheel scroll to move to next area
```

### Scenario 3: Overview Then Detail
```
1. Start at 100% zoom (default)
2. Wheel scroll to browse different sections
3. Find interesting area
4. Zoom to 300% with slider for detail work
5. Middle-click drag for pixel-perfect positioning
```

## Keyboard + Mouse Combos

| Combo | Action |
|-------|--------|
| Mouse wheel | Vertical pan |
| Shift + Mouse wheel | Horizontal pan (if supported) |
| Middle mouse + drag | Pan any direction |
| Left click + drag node | Move node |
| Left click + drag (empty) | Rubber band selection |
| Right click | Context menu |

## Troubleshooting

**Q: Mouse wheel still zooms?**
A: Make sure you're using the latest version. Restart the app if needed.

**Q: Middle-click doesn't work?**
A: Some trackpads require enabling middle-click in system settings. Try three-finger click.

**Q: Scrolling too fast/slow?**
A: Sensitivity is set to 15px per notch. Can be adjusted in canvas.py line 1024.

**Q: Want to zoom with wheel again?**
A: Use the scale slider instead - it provides more precise control.

## Configuration

You can adjust scroll sensitivity by changing `pan_amount` in `canvas.py`:

```python
# Line ~1024 in canvas.py
pan_amount = 15  # pixels per scroll tick

# Faster scrolling:
pan_amount = 30

# Slower scrolling:
pan_amount = 8
```

## Files Modified

- **graph_maker/canvas.py**
  - `wheelEvent()` - Changed from zoom to pan
  - `mousePressEvent()` - Added middle-button handling
  - `mouseReleaseEvent()` - Added middle-button release handling
  - Added `QMouseEvent` import

## Summary

✅ Mouse wheel scrolls instead of zooms
✅ Reduced sensitivity for smooth scrolling
✅ Middle-click drag panning implemented
✅ Scale slider remains the zoom control
✅ All navigation methods work together

The canvas now provides professional-grade navigation with multiple intuitive panning methods and precise zoom control!
