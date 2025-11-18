# Auto-Hallway Generation Guide

## Overview

The auto-hallway generation tool simplifies creating building layouts by automatically subdividing long hallway connections into 1-meter segments. This makes it much easier to map floor plans accurately.

## Key Changes

### Unit Length Update
- **Old**: 1 grid unit = 5 meters
- **New**: 1 grid unit = 1 meter
- **Benefit**: More precise mapping and easier to visualize on floor plans

This change affects:
- Firefighter movement speed (now 0.2 m/s in fire conditions)
- Spatial distance calculations
- All physical measurements in the simulation

## How It Works

### Workflow

1. **Create Intersection Nodes**
   - Place hallway/exit nodes at corridor intersections
   - Connect them with edges (don't worry about the distance)
   - Set room nodes and connect to hallways

2. **Run Auto-Generation**
   - Tools → Auto-Generate Hallway Segments (or `Ctrl+H`)
   - Tool automatically:
     - Detects long hallway edges (>1.5 grid units)
     - Calculates optimal number of segments
     - Creates intermediate hallway nodes
     - Splits edges into ~1 meter segments
     - Labels nodes automatically

3. **Result**
   - Long hallways are subdivided into 1-meter segments
   - Each segment gets a unique label
   - Original edge properties (width, flow) are preserved

### Example

**Before:**
```
exit_left -----(5 units)------ exit_right
```

**After:**
```
exit_left -- hallway_1 -- hallway_2 -- hallway_3 -- hallway_4 -- exit_right
   (1m)         (1m)         (1m)         (1m)         (1m)
```

## Detailed Instructions

### Step 1: Create Major Nodes

Place nodes only at key positions:
- **Exits**: Building exits and stairwells
- **Intersections**: Where hallways meet
- **Rooms**: Room entrances connected to hallways

**Don't worry about hallway length!** Just connect the endpoints.

### Step 2: Set Positions

Use the background image as reference:
- Load background floor plan (View → Load Background Image)
- Place intersection nodes at corridor junctions
- Connect them with edges
- Distance doesn't matter - tool will handle it

### Step 3: Run Auto-Generation

1. Click **Tools → Auto-Generate Hallway Segments**
2. Tool processes all hallway-type edges
3. Progress dialog shows:
   - Number of long edges processed
   - Number of segments created

### Step 4: Refine

After auto-generation:
- Check the Statistics panel
- Validate the graph
- Adjust individual hallway nodes if needed
- Use measurement tools to set precise widths

## What Gets Processed

The tool processes edges connecting:
- `hallway` to `hallway`
- `hallway` to `exit`
- `hallway` to `stairwell`
- `exit` to `exit`
- `stairwell` to `hallway`

**Not processed:**
- Room connections (these are doors, should stay as single edges)
- Edges already ~1 unit or shorter

## Automatic Labeling

Generated hallway nodes are labeled as:
```
hallway_<source>_<destination>_<segment_number>
```

Examples:
- `hallway_exit_left_intersection_1_1`
- `hallway_exit_left_intersection_1_2`
- `hallway_intersection_1_intersection_2_1`

If names conflict, a counter is appended.

## Combined Workflow: Measurement + Auto-Generation

### Complete Example

**Goal:** Create accurate floor plan from background image

1. **Setup Background:**
   ```
   - Load floor plan image
   - Set measurement scale (Ctrl+M or Tools → Set Scale)
   - Calculate pixels per meter using a known dimension
   ```

2. **Create Major Structure:**
   ```
   - Place exit nodes at building exits
   - Place hallway nodes at corridor intersections
   - Place room nodes
   ```

3. **Connect Structure:**
   ```
   - Draw edges between intersections (ignore distance)
   - Connect rooms to adjacent hallways
   - Don't create intermediate hallway nodes manually
   ```

4. **Auto-Generate Hallways:**
   ```
   - Press Ctrl+H
   - Tool creates 1-meter hallway segments
   ```

5. **Measure Dimensions:**
   ```
   - For rooms: Select node → Ctrl+B → Draw box → Apply area
   - For corridors: Select edge → Ctrl+L → Draw line → Apply width
   ```

6. **Set Occupancy:**
   ```
   - Go to Occupancy tab
   - Set probabilities for room occupants
   ```

7. **Validate and Export:**
   ```
   - Tools → Validate Graph
   - File → Export Config
   ```

## Tips and Best Practices

### Grid Alignment
- Try to align intersection nodes to integer grid coordinates
- This makes auto-generation create cleaner segments
- Use snap-to-grid if available (future feature)

### When to Use
**Good candidates:**
- Long straight corridors
- L-shaped hallways
- Building perimeter paths

**Don't use for:**
- Short doorway connections (<1.5 units)
- Room-to-hallway connections
- Already-segmented hallways

### Edge Properties
The tool preserves:
- `max_flow`
- `base_burn_rate`
- `width`

All segments inherit from the original edge.

### Undo
If you don't like the result:
- Use File → Open to reload previous version
- Or manually delete generated nodes
- Then run auto-generation again

## Technical Details

### Distance Calculation
```
distance = sqrt((x2-x1)² + (y2-y1)²)
```

### Segment Count
```
num_segments = round(distance)
```
Rounds to nearest integer for clean 1-meter segments.

### Threshold
Edges are processed if `distance > 1.5 units`

This allows:
- 1-unit edges: Unchanged
- 2-unit edges: Split into 2 segments
- 3-unit edges: Split into 3 segments
- etc.

## Keyboard Shortcuts Summary

| Shortcut | Action |
|----------|--------|
| `Ctrl+H` | Auto-generate hallway segments |
| `Ctrl+B` | Box measurement tool (area) |
| `Ctrl+L` | Line measurement tool (width) |
| `Ctrl+M` | Set measurement scale |
| `Esc` | Cancel measurement mode |

## Example: Office Building

### Before Auto-Generation
```
Nodes: 15 (2 exits, 3 intersections, 10 rooms)
Edges: 13
```

### After Auto-Generation
```
Nodes: 28 (2 exits, 3 intersections, 10 rooms, 13 hallway segments)
Edges: 26
```

Each long corridor automatically subdivided into 1-meter segments!

## Troubleshooting

**Problem:** Tool doesn't process some edges
- **Check:** Are the nodes hallway/exit/stairwell type?
- **Check:** Is the edge longer than 1.5 units?

**Problem:** Too many segments created
- **Cause:** Nodes are too far apart
- **Solution:** Add intermediate intersection nodes first

**Problem:** Irregular segment lengths
- **Cause:** Non-integer distances
- **Solution:** Align nodes to grid coordinates

**Problem:** Duplicate node IDs
- **Cause:** Running tool multiple times
- **Solution:** Tool automatically adds counters to avoid conflicts

## Integration with Simulation

The auto-generated hallways work seamlessly with the simulator:

- **Fire Spread:** Each 1-meter segment acts as a discrete fire spread point
- **Smoke:** Smoke fills and spreads through each segment
- **Movement:** Occupants and firefighters traverse realistic distances
- **Preheating:** Spatial distance calculations use actual positions

This creates much more realistic fire behavior than coarse 5-meter segments!
