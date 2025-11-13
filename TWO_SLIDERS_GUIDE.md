# Two Sliders Explained - Zoom vs Measurement Scale

## Overview

The canvas now has TWO separate sliders at the bottom, each with a different purpose:

```
┌─────────────────────────────────────────────────────────────────┐
│                        CANVAS                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
Zoom: [====|====] 100%  |  Measurement Scale: [====|====] 20 px/m (100px = 5m)
      ↑                       ↑
   View Zoom              Measurement Conversion
```

## Slider 1: Zoom (Left Side)

### Purpose
Controls how much you **magnify/shrink the view**

### Range
- Minimum: 10% (zoomed out, see everything)
- Maximum: 400% (zoomed in, extreme detail)
- Default: 100% (normal view)

### What It Does
- Changes the visual size of nodes, edges, and everything on canvas
- Affects what you SEE, not what you MEASURE
- Like zooming in/out with a camera

### When to Use
- **10-50%:** Overview of entire building
- **100%:** Normal editing
- **150-200%:** Detailed work on specific areas
- **300-400%:** Pixel-perfect positioning

### Example
```
At 50% zoom:  Building fits on screen, nodes look small
At 100% zoom: Normal view, nodes regular size
At 200% zoom: Everything 2× bigger, easier to see details
```

---

## Slider 2: Measurement Scale (Right Side)

### Purpose
Controls how **screen pixels translate to real-world meters** for measurement tools

### Range
- Minimum: 5 pixels/meter (5px = 1m)
- Maximum: 100 pixels/meter (100px = 1m)
- Default: 20 pixels/meter (20px = 1m)

### What It Does
- Defines the conversion ratio for measurement tools (Ctrl+B, Ctrl+L)
- Affects how measurements are CALCULATED, not how things LOOK
- Like setting the scale of a map

### Visual Indicator
Shows a helpful example:
- At 20 px/m: "(100px = 5m)"
- At 50 px/m: "(100px = 2m)"
- At 10 px/m: "(100px = 10m)"

### When to Use
**Set this ONCE based on your background image:**

1. Find a known dimension on your floor plan (e.g., "10m" wall)
2. Measure it with a ruler/tool (e.g., 200 pixels)
3. Calculate: pixels ÷ meters = 200 ÷ 10 = 20 px/m
4. Set slider to 20

### Example Calibration
```
Background image has a wall labeled "5 meters"
You measure it: 100 pixels wide
Calculation: 100 ÷ 5 = 20 pixels/meter
→ Set Measurement Scale slider to 20
```

---

## Key Differences

| Aspect | Zoom Slider | Measurement Scale Slider |
|--------|-------------|--------------------------|
| **Purpose** | Change view size | Set measurement conversion |
| **Affects** | What you SEE | What you MEASURE |
| **Changes** | Constantly (while working) | Once (during setup) |
| **Range** | 10-400% | 5-100 px/m |
| **Analogy** | Camera zoom | Map scale |
| **Unit** | Percentage | Pixels per meter |

---

## Complete Workflow

### Step 1: Initial Setup (One Time)

```
1. Load your floor plan background image

2. Find a known distance (e.g., wall labeled "10m")

3. Use line tool (Ctrl+L) to measure it:
   - Draw line across the wall
   - Note the pixel length (e.g., "200 pixels")

4. Calculate pixels per meter:
   pixels ÷ meters = 200 ÷ 10 = 20 px/m

5. Set Measurement Scale slider to 20

6. Verify with visual indicator:
   "(100px = 5m)" ← Correct!
```

### Step 2: Working (Ongoing)

```
1. Use Zoom slider to navigate:
   - Zoom out (50%) to see whole building
   - Zoom in (200%) for detailed editing

2. Use measurement tools:
   - Ctrl+B for room areas
   - Ctrl+L for passage widths
   - All measurements use the scale you set!

3. Pan with:
   - Mouse wheel (vertical)
   - Middle-click drag (any direction)
```

---

## Real-World Examples

### Example 1: Small Floor Plan

**Scenario:** Small office, background image is 500×500 pixels, represents 25m × 25m building

**Setup:**
- Known dimension: 10m wall = 200 pixels
- Calculation: 200 ÷ 10 = 20 px/m
- Set Measurement Scale: 20 px/m
- Set Zoom: 100% (fits nicely)

**Result:** Drawing a 100-pixel box measures as 5m × 5m ✓

### Example 2: Large Campus Map

**Scenario:** University campus, background is 2000×2000 pixels, represents 100m × 100m

**Setup:**
- Known dimension: 50m building = 1000 pixels
- Calculation: 1000 ÷ 50 = 20 px/m
- Set Measurement Scale: 20 px/m
- Set Zoom: 25% (to see everything)

**Result:** Drawing a 100-pixel box measures as 5m × 5m ✓

### Example 3: Detailed Room Layout

**Scenario:** Single room detail, background is 1000×1000 pixels, represents 10m × 10m

**Setup:**
- Known dimension: 2m door = 200 pixels
- Calculation: 200 ÷ 2 = 100 px/m
- Set Measurement Scale: 100 px/m
- Set Zoom: 100%

**Result:** Drawing a 100-pixel box measures as 1m × 1m ✓

---

## Common Mistakes

### ❌ Mistake 1: Confusing the Sliders
```
User thinks: "I'll zoom in to make measurements more accurate"
Problem: Zoom doesn't affect measurements at all!
Solution: Set measurement scale based on background image,
          then use zoom for comfortable viewing.
```

### ❌ Mistake 2: Changing Scale While Working
```
User: Changes measurement scale from 20 to 40 halfway through
Problem: Old measurements now wrong!
Solution: Set measurement scale ONCE at start, don't change.
```

### ❌ Mistake 3: Forgetting to Calibrate
```
User: Leaves measurement scale at default 20 px/m
Problem: Measurements are wrong if image has different scale!
Solution: Always calibrate using known dimension first.
```

---

## Technical Details

### Zoom Slider
```python
# Range: 10-400
zoom_factor = slider_value / 100.0
canvas.scale(zoom_factor, zoom_factor)

# Examples:
# 50 → 0.5× (half size)
# 100 → 1.0× (normal)
# 200 → 2.0× (double size)
```

### Measurement Scale Slider
```python
# Range: 5-100 px/m
canvas.pixels_per_meter = slider_value

# When measuring:
width_meters = width_pixels / pixels_per_meter

# Examples at 20 px/m:
# 100 pixels → 100/20 = 5 meters
# 200 pixels → 200/20 = 10 meters
```

---

## Quick Reference

### Zoom Slider
- **Label:** "Zoom: [slider] 100%"
- **When:** Adjust constantly for comfortable viewing
- **Purpose:** Change what you see
- **Range:** 10-400%

### Measurement Scale Slider
- **Label:** "Measurement Scale: [slider] 20 px/m (100px = 5m)"
- **When:** Set once during initial setup
- **Purpose:** Calibrate measurement tools
- **Range:** 5-100 px/m

---

## Summary

✅ **Zoom Slider** = How BIG things look (changes view)
✅ **Measurement Scale Slider** = How to CONVERT pixels to meters (calibrates measurements)

They are **completely independent** and serve different purposes:
- Zoom: Adjust anytime for comfortable viewing
- Scale: Set once based on your background image

Both sliders work together to give you:
1. Comfortable viewing (zoom)
2. Accurate measurements (scale)
3. Professional workflow 🎉
