# Multi-Floor Building System Design

## Overview
Extend the evacuation simulator to support multi-floor buildings with vertical connectivity through staircases. This requires changes to graph creation, physics simulation, pathfinding, and visualization.

---

## 1. Data Model & Graph Structure

### 1.1 Node Representation
Each node gets a `floor` attribute:
```json
{
  "id": "Room_A",
  "type": "room",
  "floor": 1,  // NEW: Floor number (1-indexed or 0-indexed)
  "position": {"x": 100, "y": 200},  // 2D position on floor plan
  "visual_position": {"x": 100, "y": 200}
}
```

### 1.2 Staircase Nodes
Staircases are special nodes that exist on BOTH floors they connect:
```json
{
  "id": "Staircase_A",  // Same name on both floors
  "type": "staircase",
  "floor": 1,  // This instance is on floor 1
  "connects_to_floor": 2,  // Connects to floor 2
  "position": {"x": 300, "y": 150}
}
```

**Key Design Decision**: Each staircase creates TWO nodes in the graph:
- `Staircase_A_F1` (floor 1 instance)
- `Staircase_A_F2` (floor 2 instance)

These are automatically connected with a special "vertical edge" representing the staircase travel time.

### 1.3 Edge Representation
```json
{
  "id": "edge_1",
  "vertex_a": "Room_A_F1",
  "vertex_b": "Staircase_A_F1",
  "type": "hallway",  // or "staircase" for vertical edges
  "unit_length": 5.0,  // Meters
  "floor": 1  // NEW: Floor this edge belongs to (null for staircase edges)
}
```

**Vertical Edges** (auto-generated for staircases):
```json
{
  "id": "stair_Staircase_A",
  "vertex_a": "Staircase_A_F1",
  "vertex_b": "Staircase_A_F2",
  "type": "staircase",
  "unit_length": 10.0,  // Configurable - time to traverse one floor
  "floor": null  // Vertical edge doesn't belong to a single floor
}
```

---

## 2. Graph Maker GUI Changes

### 2.1 Floor Selector Widget
Add a floor selector to the main window:
```
[Floor Selector: ▼ Floor 1] [+ Add Floor] [- Remove Floor]
```

- **Current floor** determines which nodes/edges are visible on canvas
- All editing operations happen on the currently selected floor
- Floor list stored in: `self.model.floors = [1, 2, 3, ...]`

### 2.2 Staircase Placement Workflow

**Option 1: Explicit Linking (RECOMMENDED)**
1. User creates a staircase node on Floor 1 with name "Staircase_A"
2. User switches to Floor 2
3. User creates another staircase node with **the same name** "Staircase_A"
4. Graph maker automatically detects matching names and creates vertical edge
5. Visual indicator shows which staircases are linked (e.g., green outline)

**Option 2: Automatic Mirroring**
1. User creates staircase on Floor 1
2. Checkbox: "Mirror to adjacent floors"
3. System automatically creates matching staircase on Floor 0 and Floor 2
4. User can adjust positions independently

### 2.3 Staircase Properties Panel
When staircase is selected:
```
Node ID: Staircase_A
Type: Staircase
Current Floor: 2
Linked Floors: [1, 2, 3]  // If staircase spans multiple floors
Vertical Travel Time: 8.0 seconds (per floor)
```

### 2.4 Visual Enhancements
- **Floor indicator** on each node: Small badge showing floor number
- **Staircase highlighting**: Different color for staircase nodes (e.g., purple)
- **Link status**: Green checkmark if staircase has valid links to other floors
- **Ghost nodes**: Optionally show staircases from other floors as semi-transparent

---

## 3. JSON File Format

### 3.1 Structure
```json
{
  "description": "3-floor office building",
  "num_floors": 3,
  "floor_height_meters": 3.0,  // NEW: For fire spread calculations

  "vertices": {
    "Room_A_F1": {
      "id": "Room_A_F1",
      "type": "room",
      "floor": 1,
      "position": {"x": 100, "y": 200},
      ...
    },
    "Staircase_A_F1": {
      "id": "Staircase_A_F1",
      "type": "staircase",
      "floor": 1,
      "staircase_group": "Staircase_A",  // Links instances
      ...
    },
    "Staircase_A_F2": {
      "id": "Staircase_A_F2",
      "type": "staircase",
      "floor": 2,
      "staircase_group": "Staircase_A",
      ...
    }
  },

  "edges": {
    "edge_1": {
      "vertex_a": "Room_A_F1",
      "vertex_b": "Staircase_A_F1",
      "floor": 1,
      ...
    },
    "stair_Staircase_A_1_2": {
      "vertex_a": "Staircase_A_F1",
      "vertex_b": "Staircase_A_F2",
      "type": "staircase",
      "unit_length": 10.0,
      "floor": null
    }
  },

  "fire_origin": "Room_B_F2",  // Can be on any floor
  ...
}
```

### 3.2 Saving/Loading Logic
- Graph maker saves separate floor info for each node
- On load, automatically rebuild vertical edges based on `staircase_group` matching
- Validate that all staircase groups have valid connections

---

## 4. Fire Spread Physics (3D)

### 4.1 Distance Calculation Enhancement
Current: `distance_2d = sqrt((x1-x2)^2 + (y1-y2)^2)`

**New: 3D Distance for Fire Spread**
```python
def calculate_3d_distance(node_a, node_b, floor_height=3.0):
    """Calculate 3D distance between nodes, accounting for vertical separation."""
    dx = node_a.position['x'] - node_b.position['x']
    dy = node_a.position['y'] - node_b.position['y']

    # Calculate vertical distance
    floor_diff = abs(node_a.floor - node_b.floor)
    dz = floor_diff * floor_height  # meters

    # 3D Euclidean distance
    distance_3d = sqrt(dx**2 + dy**2 + dz**2)
    return distance_3d
```

### 4.2 Fire Spread Rules
1. **Horizontal spread** (same floor): Uses existing logic with 2D distance
2. **Vertical spread** (different floors):
   - Fire can spread through connected staircases (if staircase edge is burning)
   - Direct vertical spread through structure (e.g., elevator shafts, HVAC)
   - Use 3D distance: `floor_height * |floor_a - floor_b| + 2D_distance`

### 4.3 Smoke Propagation
Smoke naturally rises:
```python
# Smoke spreads faster upward than downward
if target_floor > source_floor:
    smoke_spread_rate *= 1.5  # Faster upward
elif target_floor < source_floor:
    smoke_spread_rate *= 0.5  # Slower downward
```

### 4.4 Configuration Parameters
```python
FLOOR_HEIGHT_METERS = 3.0  # Standard floor height
VERTICAL_FIRE_SPREAD_MODIFIER = 0.7  # Slower through floors
SMOKE_RISE_MULTIPLIER = 1.5  # Smoke prefers moving up
```

---

## 5. Pathfinding & Movement

### 5.1 Firefighter Pathfinding
- A* algorithm works unchanged (operates on full 3D graph)
- Vertical edges treated as normal edges with appropriate costs
- Staircase traversal cost: `unit_length / movement_speed`

### 5.2 Occupant Movement
- Occupants can use staircases to evacuate
- Movement through staircase: Same as hallway (1 tick per unit_length)
- Prefer staircases that lead DOWN toward ground floor exits

### 5.3 Entry/Exit Nodes
- Typically on ground floor (Floor 1 or Floor 0)
- Can have multiple exits on different floors (fire escapes)
- Firefighters spawn at exits (ground floor by default)

---

## 6. Visualization

### 6.1 Single-Floor View (Default)
**Canvas displays one floor at a time:**
- Shows all nodes/edges on selected floor
- Staircases highlighted with special color/icon
- Indicator showing which staircases connect to which floors
- Background image specific to current floor

**UI Controls:**
```
Current View: [Floor 1 ▼]  [Show All Floors (3D)]
```

### 6.2 Multi-Floor View (Optional)
**Stacked 2D representation:**
```
┌─────────────────┐  Floor 3
│   ╔═══╗         │
│   ║STR║         │
│   ╚═╦═╝         │
└─────╨───────────┘
      │
┌─────╨───────────┐  Floor 2
│   ╔═╦═╗         │
│   ║STR║         │
│   ╚═╦═╝         │
└─────╨───────────┘
      │
┌─────╨───────────┐  Floor 1 (Ground)
│   ╔═╦═╗         │
│   ║STR║  [EXIT] │
│   ╚═══╝         │
└─────────────────┘
```

Each floor rendered separately, stacked vertically with connectors.

### 6.3 3D Isometric View (Advanced)
Use pygame to render isometric 3D view:
- Each floor as a horizontal plane
- Staircases as vertical connectors
- Fire/smoke rendered with transparency on each floor
- Camera angle adjustable

### 6.4 Floor-Specific Visualization States
Track fire/smoke separately per floor:
```python
{
  "floor_1": {
    "fire_cells": [...],
    "smoke_cells": [...],
    "occupants": [...]
  },
  "floor_2": {...}
}
```

---

## 7. Implementation Plan

### Phase 1: Data Model (graph_maker/models.py)
- [ ] Add `floor` field to GraphModel
- [ ] Add `num_floors`, `floor_height_meters` to config
- [ ] Add floor to vertex schema
- [ ] Implement staircase_group linking logic
- [ ] Auto-generate vertical edges for staircases

### Phase 2: Graph Maker GUI
- [ ] Add floor selector widget to main_window.py
- [ ] Filter canvas to show only current floor nodes/edges
- [ ] Add floor field to PropertyPanel
- [ ] Implement staircase linking detection
- [ ] Add visual indicators for linked staircases
- [ ] Update save/load to handle floor data

### Phase 3: Simulator Core (model.py)
- [ ] Add floor attribute to Node class
- [ ] Update position to track floor
- [ ] Implement 3D distance calculation
- [ ] Modify fire spread to use 3D distance
- [ ] Add vertical smoke propagation rules
- [ ] Update pathfinding (should work automatically)

### Phase 4: Visualization (visualizer.py)
- [ ] Add floor selector to visualization UI
- [ ] Render only current floor by default
- [ ] Add "show all floors" stacked view
- [ ] Color-code entities by floor
- [ ] Show staircase connections between floors
- [ ] Optional: Isometric 3D rendering mode

### Phase 5: Testing & Validation
- [ ] Create 2-floor test building
- [ ] Verify fire spread between floors
- [ ] Test smoke rise behavior
- [ ] Validate pathfinding through staircases
- [ ] Benchmark performance with multiple floors

---

## 8. Key Design Questions

### Q1: Floor Numbering Convention?
**Recommendation**: Use 1-indexed (Floor 1 = ground floor, Floor 2 = first floor above ground)
- Matches common building conventions
- Avoids confusion with "0th floor"
- Alternative: 0-indexed (programming convention)

### Q2: Staircase Edge Length?
**Recommendation**: Configurable per staircase, default = 10 meters
- Accounts for: vertical climb + horizontal distance on stairs
- Typical floor: 3m vertical + ~6-8m horizontal travel = ~10m total
- Can adjust based on staircase design (spiral vs straight)

### Q3: Background Images Per Floor?
**Recommendation**: Support separate background images per floor
```python
self.background_images = {
    1: "floor1_plan.png",
    2: "floor2_plan.png",
    3: "floor3_plan.png"
}
```

### Q4: Fire Origin on Different Floors?
**Recommendation**: Allow fire to start on any floor
- Store floor info with fire_origin: `{"node": "Room_B", "floor": 2}`
- Fire spreads in all directions (including vertically)

---

## 9. Example Workflow

### Creating a 2-Floor Building:

1. **Launch graph_maker.py**
2. **Configure building**: Set num_floors = 2, floor_height = 3.0m
3. **Design Floor 1**:
   - Set current floor to 1
   - Draw rooms, hallways, exits
   - Place staircase node "Stair_Main" at (300, 150)
4. **Design Floor 2**:
   - Switch to floor 2
   - Draw rooms, hallways
   - Place staircase node "Stair_Main" at (300, 150) (same name!)
   - System auto-creates vertical edge
5. **Set fire origin**: Select a room on Floor 2
6. **Save**: Exports JSON with all floor data
7. **Run simulator**: Load JSON, fire spreads through both floors

---

## 10. Potential Challenges

### Challenge 1: Visualization Complexity
**Solution**: Start with simple floor-selector view, add 3D later

### Challenge 2: Performance with Many Floors
**Solution**:
- Spatial indexing per floor (don't check fire spread to distant floors)
- Limit vertical spread checks to adjacent floors ± 1

### Challenge 3: Pathfinding Through Multiple Floors
**Solution**:
- Graph naturally handles this with vertical edges
- May need to tune edge weights for stair preference

### Challenge 4: Smoke Rendering on Multiple Floors
**Solution**:
- Render smoke separately per floor
- Alpha blending for stacked view
- Use color intensity to show concentration

---

## 11. Future Enhancements

1. **Elevators**: Similar to staircases but with different mechanics (can fail, limited capacity)
2. **Fire Doors**: Auto-close to contain fire between floors
3. **Sprinkler Systems**: Floor-specific activation
4. **Smoke Vents**: Roof-level vents on top floor
5. **Helicopter Rescue**: Rooftop evacuation option
6. **Basement Levels**: Negative floor numbers

---

## Summary

**Your suggestion is excellent and aligns well with best practices:**

✅ Draw different floor plans separately
✅ Connect staircases with matching names
✅ Use configurable unit_length for staircase travel time
✅ 3D distance for fire spread (with 3m floor height)
✅ Floor-specific visualization with selector

**Recommended Implementation Order:**
1. Start with 2-floor support
2. Add floor selector to graph maker
3. Implement staircase linking (matching names)
4. Extend fire physics to 3D
5. Add floor-filtered visualization
6. Test thoroughly before expanding to 3+ floors
