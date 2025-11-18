# Graph Maker - Complete Feature List

## Recent Updates

### ✓ Measurement Tools (Just Added)
**Box Tool** - Estimate room areas
- Draw a box over a room on the background image
- Automatically calculates area in m²
- Apply directly to selected nodes
- Keyboard: `Ctrl+B`

**Line Tool** - Estimate passage widths
- Draw a line across a corridor/doorway
- Automatically calculates width in meters
- Apply directly to selected edges
- Keyboard: `Ctrl+L`

**Scale Setting**
- Set pixels-per-meter conversion ratio
- Calibrate using known dimensions on floor plan
- Menu: Tools → Measurement Tools → Set Scale

### ✓ Auto-Hallway Generation (Just Added)
**Automatic Segmentation**
- Automatically subdivide long hallways into 1-meter segments
- Just place intersection nodes and connect them
- Tool creates all intermediate hallway nodes
- Preserves edge properties (width, flow rate)
- Keyboard: `Ctrl+H`

**Benefits:**
- No need to manually place dozens of hallway nodes
- Creates realistic 1-meter fire spread granularity
- Automatic labeling of generated segments
- Much faster workflow for complex buildings

### ✓ Unit Length Change
- **Changed from 5m to 1m per unit edge**
- More realistic spatial resolution
- Easier to map floor plans accurately
- Firefighter speed now 0.2 m/s (appropriate for fire conditions)

## Core Features

### Visual Graph Editor
- Drag-and-drop node placement
- Right-click context menus
- Interactive edge creation
- Real-time visual feedback
- Mouse wheel zoom
- Middle-button pan

### Node Types
- **Room**: Office spaces, classrooms, etc.
- **Hallway**: Corridor segments and junctions
- **Stairwell**: Vertical circulation
- **Exit**: Building exits and emergency exits

### Background Images
- Load floor plan images for reference
- Adjustable opacity (0-100%)
- Helps accurately place nodes and measure distances
- Supports PNG, JPG, JPEG, BMP formats

### Property Editing
**Vertex Properties:**
- Type (room/hallway/exit/stairwell)
- Room type (office, classroom, etc.)
- Capacity (max occupants)
- Priority (search priority)
- Sweep time (firefighter search time)
- Area (m²) - set manually or via box tool
- Position (x, y coordinates)

**Edge Properties:**
- Max flow (people per tick)
- Base burn rate
- Width (meters) - set manually or via line tool
- Connected vertices

### Occupancy Configuration
- Table-based probability editor
- Set capable/incapable occupant probabilities
- Per-room configuration
- Expected occupant calculation

### Fire Origin
- Right-click any node to set as fire origin
- Visual indicator (red highlight)
- Required for simulation

### Validation
- Check for required exits
- Verify all edges connect to existing vertices
- Validate fire origin
- Check visual positions
- Validate occupancy probabilities
- Error reporting with specific messages

### File Operations
- **New**: Create blank graph
- **Open**: Load existing JSON config
- **Save**: Save current work
- **Save As**: Save to new file
- **Export**: Export simulation-ready config

### Statistics Panel
- Total vertices count
- Total edges count
- Breakdown by vertex type
- Expected occupant count
- Fire origin status
- One-click validation

### Quick Test Simulation
- Run 30-tick simulation directly from graph maker
- See evacuation progress
- Test fire spread
- Verify graph functionality
- Built-in testing without leaving the editor

## Complete Workflow

### 1. Setup
```
File → New
View → Load Background Image
Tools → Measurement Tools → Set Scale
```

### 2. Create Structure
```
Right-click → Add Node → (Room/Hallway/Exit)
Place major intersection nodes
Connect with edges (don't worry about distance)
```

### 3. Auto-Generate Hallways
```
Tools → Auto-Generate Hallway Segments (Ctrl+H)
→ Long hallways automatically subdivided into 1m segments
```

### 4. Measure Dimensions
```
For rooms:
  - Click room node
  - Ctrl+B → draw box over room
  - Apply area

For corridors:
  - Click edge
  - Ctrl+L → draw line across width
  - Apply width
```

### 5. Configure Occupancy
```
Occupancy tab
→ Set capable/incapable probabilities for each room
```

### 6. Set Fire Parameters
```
Right-click node → Set as Fire Origin
```

### 7. Validate & Test
```
Statistics tab → Validate Graph
Tools → Quick Test Simulation
```

### 8. Export
```
File → Export Config
→ Ready to use with simulator
```

## Keyboard Shortcuts

### File Operations
- `Ctrl+N` - New file
- `Ctrl+O` - Open file
- `Ctrl+S` - Save
- `Ctrl+Shift+S` - Save As

### Editing
- `Del` - Delete selected item
- `F5` - Refresh all panels

### Tools
- `Ctrl+T` - Quick test simulation
- `Ctrl+H` - Auto-generate hallway segments
- `Ctrl+B` - Box measurement tool
- `Ctrl+L` - Line measurement tool
- `Esc` - Cancel measurement mode

### View
- `Mouse Wheel` - Zoom in/out
- `Middle Mouse + Drag` - Pan canvas

## Menu Structure

```
File
├── New (Ctrl+N)
├── Open... (Ctrl+O)
├── Save (Ctrl+S)
├── Save As... (Ctrl+Shift+S)
├── ───────────
├── Export Config...
├── ───────────
└── Exit

Edit
└── Delete Selected (Del)

View
├── Load Background Image...
├── Set Background Opacity...
├── ───────────
└── Refresh All (F5)

Tools
├── Validate Graph
├── Quick Test Simulation... (Ctrl+T)
├── ───────────
├── Measurement Tools
│   ├── Set Scale...
│   ├── ───────────
│   ├── Box Tool (Area) (Ctrl+B)
│   ├── Line Tool (Width) (Ctrl+L)
│   └── Cancel Measurement (Esc)
├── ───────────
└── Auto-Generate Hallway Segments (Ctrl+H)

Help
└── About
```

## Right-Click Context Menus

### On Node
- Edit Properties
- Delete
- Set as Fire Origin
- Create Edge from Here

### On Edge
- Edit Properties
- Delete

### On Canvas
- Add Node → (Room/Hallway/Stairwell/Exit/Window Exit)
- Background → Load Image.../Adjust Opacity.../Clear

## Panel Tabs

### Properties
- Edit selected node/edge properties
- Real-time updates
- Input validation

### Occupancy
- Table of all rooms
- Set capable/incapable probabilities
- Auto-refresh

### Statistics
- Vertex/edge counts
- Vertex type breakdown
- Expected occupants
- Fire origin status
- Validation errors
- Validate button

## Tips for Efficient Use

### Best Practices
1. **Always load background image first** - Makes positioning much easier
2. **Set scale immediately** - Ensures accurate measurements
3. **Place major nodes first** - Exits, intersections, rooms
4. **Use auto-generation** - Don't manually create hallway segments
5. **Measure after generation** - Use measurement tools for precise dimensions
6. **Validate frequently** - Catch errors early
7. **Test before finalizing** - Quick test simulation is your friend

### Common Patterns

**Simple Building:**
```
1. Place 2 exits
2. Place hallway intersection in middle
3. Place room nodes
4. Connect exits ← → intersection ← → rooms
5. Run auto-generate
6. Measure and adjust
```

**Multi-Floor:**
```
1. Create first floor completely
2. Add stairwell nodes
3. Copy/adapt for second floor
4. Connect floors with stairwell edges
```

**Complex Layout:**
```
1. Place all exits first
2. Place hallway intersections (corners, junctions)
3. Connect hallways with long edges
4. Auto-generate to create segments
5. Add rooms and connect to nearest hallway
6. Use measurement tools for precision
```

## Advanced Features

### Spatial Coordinates
- All nodes have (x, y) visual positions
- Used for fire spread calculations
- Euclidean distance for preheating
- Real-time updates when dragging nodes

### Edge Auto-Update
- Edges update position when nodes move
- Labels track edge midpoints
- Width-based visual thickness

### Smart Labeling
- Auto-generated nodes get descriptive IDs
- Conflict resolution with counters
- Preserves manual labels

### Inherited Properties
- Auto-generated hallways inherit edge properties
- Consistent flow rates
- Consistent burn rates
- Uniform widths (customizable after)

## File Format

The graph maker saves/loads standard JSON configs compatible with the simulator:

```json
{
  "description": "Building layout",
  "vertices": [...],
  "edges": [...],
  "occupancy_probabilities": {...},
  "fire_params": {
    "origin": "room_id",
    "initial_smoke_level": 0.3
  }
}
```

## System Requirements

- Python 3.7+
- PyQt5
- Works on macOS, Linux, Windows
- Recommended: 1920x1080 or higher resolution

## Future Enhancements (Potential)

- Snap-to-grid
- Multi-select and bulk edit
- Copy/paste nodes and edges
- Undo/redo
- Templates for common room types
- Import from CAD formats
- Export to visual reports
