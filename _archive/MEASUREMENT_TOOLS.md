# Measurement Tools Guide

The graph maker includes measurement tools to help estimate room areas and passage widths when working with background floor plan images.

## Setting the Scale

Before using measurement tools, you need to set the scale to convert pixels to meters:

1. **Tools → Measurement Tools → Set Scale**
2. Enter the **pixels per meter** ratio
   - Example: If 100 pixels = 5 meters, enter `20` (100/5 = 20)
   - Example: If 50 pixels = 2.5 meters, enter `20` (50/2.5 = 20)

**How to calculate your scale:**
- Find a known distance on your floor plan (e.g., a wall labeled "10 meters")
- Measure it in pixels using any graphics tool
- Divide pixels by meters: `pixels_per_meter = measured_pixels / known_meters`

## Box Tool - Measuring Room Areas

Use the box tool to measure room dimensions and calculate area:

1. **Activate:** Tools → Measurement Tools → Box Tool (or `Ctrl+B`)
2. **Draw:** Click and drag to draw a rectangle over the room
3. **View:** Real-time display shows:
   - Width and height in meters
   - Total area in m²
4. **Apply:** Release mouse to apply measurement
   - If a node is selected: Prompted to set the area
   - If no node selected: Area displayed for reference

**Tips:**
- Draw the box to match the room boundaries on your background image
- Select the node first, then measure, for quick application
- The box shows as an orange dashed rectangle with semi-transparent fill

**Example Workflow:**
```
1. Load background floor plan image
2. Set scale (e.g., 20 pixels/meter)
3. Click on a room node to select it
4. Press Ctrl+B to start box measurement
5. Draw box over the room in the background
6. Confirm to apply the measured area to the node
```

## Line Tool - Measuring Passage Widths

Use the line tool to measure passage/corridor widths:

1. **Activate:** Tools → Measurement Tools → Line Tool (or `Ctrl+L`)
2. **Draw:** Click and drag to draw a line across the passage
3. **View:** Real-time display shows:
   - Length in meters
4. **Apply:** Release mouse to apply measurement
   - If an edge is selected: Prompted to set the width
   - If no edge selected: Width displayed for reference

**Tips:**
- Draw the line perpendicular to the passage for accurate width
- Select the edge first, then measure, for quick application
- The line shows as a blue thick line

**Example Workflow:**
```
1. Select an edge (corridor/doorway connection)
2. Press Ctrl+L to start line measurement
3. Draw line across the passage in the background
4. Confirm to apply the measured width to the edge
```

## Keyboard Shortcuts

- `Ctrl+B` - Start box measurement (area)
- `Ctrl+L` - Start line measurement (width)
- `Esc` - Cancel current measurement

## Cancel Measurement

To exit measurement mode without applying:
- Press `Esc`
- Or: Tools → Measurement Tools → Cancel Measurement

## Visual Indicators

**Box Tool:**
- Orange dashed rectangle with semi-transparent fill
- Label shows dimensions and area in real-time

**Line Tool:**
- Thick blue line
- Label shows length in real-time

## Common Scale Values

| Floor Plan Scale | Pixels per Meter | Example |
|-----------------|------------------|---------|
| 1:50 | ~20-40 | Detailed floor plans |
| 1:100 | ~10-20 | Building layouts |
| 1:200 | ~5-10 | Large buildings |

**Note:** Actual pixels per meter depends on your image resolution and how zoomed in you are. Always measure a known distance to calculate the exact scale.

## Example: Complete Workflow

1. **Load your floor plan:**
   - View → Load Background Image
   - Adjust opacity if needed (30-50% works well)

2. **Calibrate scale:**
   - Find a labeled dimension (e.g., "5m" wall)
   - Measure it with the line tool
   - Calculate: pixels_measured / 5 = pixels_per_meter
   - Tools → Measurement Tools → Set Scale
   - Enter the calculated value

3. **Measure rooms:**
   - Create/select room nodes
   - Use Ctrl+B for each room
   - Draw boxes matching background rooms
   - Apply measurements

4. **Measure passages:**
   - Create/select corridor edges
   - Use Ctrl+L for each passage
   - Draw lines across passage widths
   - Apply measurements

5. **Verify:**
   - Check Properties panel to see applied values
   - Adjust if needed using the property editor
