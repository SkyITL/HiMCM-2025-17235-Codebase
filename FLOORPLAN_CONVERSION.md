# Floor Plan to Graph Conversion

## Overview

Successfully converted a real-world architectural floor plan into our graph-based evacuation simulator format.

## Source Floor Plan

**Building Type**: Residential apartment or office space
**Dimensions**: Approximately 15m x 9m (135 sqm total)
**Layout**: Multi-room configuration with central circulation

### Identified Spaces

From the architectural drawing, we identified:

**Rooms (7 total):**
1. **Room 1** (Top-left) - Bedroom, 13.7 sqm
2. **Room 2** (Top-center) - Bedroom, 13.0 sqm
3. **Room 3** (Top-right) - Bedroom, 16.0 sqm
4. **Living Room** (East side) - Large room, 25.2 sqm
5. **Room 4** (Bottom-left) - Office, 9.9 sqm
6. **Room 5** (Bottom-center-left) - Office, 10.8 sqm
7. **Room 6** (Bottom-center-right) - Office, 11.7 sqm

**Circulation (4 spaces):**
- **Hallway West** - 9.6 sqm corridor
- **Hallway Central** - 12.0 sqm main corridor
- **Hallway East** - 9.0 sqm corridor
- **Entrance Hall** - 9.0 sqm entry area

**Vertical Circulation:**
- **Stairwell** - 10.1 sqm (connects floors)

**Exits:**
- **Main Exit** - Primary entrance/exit door

## Graph Representation

### Vertices (13 total)

```
Rooms:        7 (bedrooms + living room + offices)
Hallways:     4 (circulation spaces)
Stairwell:    1 (vertical circulation)
Exits:        1 (main door)
```

### Edges (14 connections)

Represents doorways and passage connections:

```
Hallway Network:
  hallway_west ←→ hallway_central
  hallway_central ←→ hallway_east
  hallway_central ←→ entrance_hall
  entrance_hall ←→ stairwell
  stairwell ←→ hallway_central

Room Connections:
  room_1 ←→ hallway_west
  room_2 ←→ hallway_central
  room_3 ←→ hallway_east
  room_4 ←→ hallway_west
  room_5 ←→ hallway_central
  room_6 ←→ hallway_central
  living_room ←→ hallway_east
  living_room ←→ entrance_hall

Exit:
  entrance_hall ←→ exit_main
```

## Conversion Process

### 1. Manual Analysis
- Examined architectural drawing
- Identified distinct rooms and spaces
- Measured approximate dimensions from scale
- Located doorways and connections
- Classified room types (bedroom, office, living, etc.)

### 2. Graph Creation
Created `analyze_floorplan.py` to:
- Define vertices with properties (type, dimensions, capacity)
- Map connections as edges
- Calculate areas and occupancy probabilities
- Generate simulation-compatible JSON config

### 3. Configuration Output

Generated `config_realistic_apartment.json` with:

```json
{
  "description": "Realistic apartment/office floor plan",
  "dimensions": {
    "width_m": 15.0,
    "height_m": 9.0,
    "total_area_sqm": 135.0
  },
  "vertices": [...],
  "edges": [...],
  "occupancy_probabilities": {...},
  "fire_params": {
    "origin": "room_5"
  }
}
```

## Simulation Parameters

### Room-Specific Settings

**Bedrooms** (Rooms 1-3):
- Priority: 3 (HIGH - people sleeping)
- Capacity: 4 people
- Sweep time: 3 seconds
- Occupancy: 15% per sqm (likely occupied at night)

**Living Room**:
- Priority: 2 (MEDIUM)
- Capacity: 10 people
- Sweep time: 4 seconds
- Occupancy: 10% per sqm

**Offices** (Rooms 4-6):
- Priority: 2 (MEDIUM)
- Capacity: 6 people
- Sweep time: 2 seconds
- Occupancy: 8% per sqm

**Hallways/Circulation**:
- Priority: 1 (LOW)
- No initial occupants
- Faster sweep times (1-2 seconds)

**Stairwell**:
- Special type (connects floors)
- Can be used for multi-floor scenarios
- No initial occupants

## Key Differences from Simple Office

| Aspect | Simple Office | Realistic Apartment |
|--------|---------------|---------------------|
| **Area** | ~600 sqm | 135 sqm |
| **Exits** | 2 (both sides) | 1 (main door) |
| **Rooms** | 6 (all offices) | 7 (mixed use) |
| **Priorities** | All equal | Variable (bedrooms=high) |
| **Vertical** | None | Stairwell present |
| **Complexity** | Simple linear | Complex branching |

## Challenges Identified

Initial testing revealed the greedy AI performs **poorly** on this layout:
- **Simple office**: 34.8% survival rate
- **Apartment**: 0% survival rate

**Why?**
1. **Single exit** - bottleneck vs two exits
2. **Complex topology** - longer paths to exit
3. **Stairwell** - AI may get confused by vertical connection
4. **Higher occupancy density** - more people in smaller space

This demonstrates the value of testing multiple building types!

## Usage

### Generate Configuration
```bash
python3 analyze_floorplan.py
```

### Test Without GUI
```bash
python3 test_realistic_apartment.py
```

### Visualize
```bash
python3 run_scenario.py apartment manual
# or
python3 run_scenario.py apartment auto
```

### Compare Scenarios
```bash
# Simple office (good performance)
python3 run_scenario.py office auto

# Realistic apartment (challenging!)
python3 run_scenario.py apartment auto
```

## Future Work

### For Paper
- Create multiple building types (school, hospital, warehouse)
- Vary number of floors (use stairwell connections)
- Test different exit configurations
- Compare AI performance across layouts
- Demonstrate model robustness

### For Competition
- Import more floor plans from architectural drawings
- Automated floor plan OCR/recognition
- Building generator tool (random floor plans)
- Benchmark suite of standard buildings

### Technical Improvements
- Auto-layout algorithm for visualizer positioning
- Floor plan image overlay in visualizer
- Multi-floor visualization (3D or stacked 2D)
- Heat map showing evacuation efficiency

## Files Created

1. **analyze_floorplan.py** - Floor plan analyzer and converter
2. **config_realistic_apartment.json** - Generated configuration
3. **test_realistic_apartment.py** - Test script
4. **run_scenario.py** - Scenario launcher
5. **FLOORPLAN_CONVERSION.md** - This documentation

## Conclusion

Successfully demonstrated:
- ✅ Real floor plan → graph conversion
- ✅ Realistic building parameters
- ✅ Multi-room type support (bedroom, office, living)
- ✅ Stairwell for future multi-floor expansion
- ✅ Easy scenario switching

The apartment configuration provides a **challenging test case** that exposes weaknesses in simple greedy strategies, motivating development of better decision models!
