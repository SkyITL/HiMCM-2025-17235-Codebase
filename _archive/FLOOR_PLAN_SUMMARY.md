# Floor Plan Analysis - Summary

## What We Built

Successfully created a **graph-based representation** of a real architectural floor plan for use in the emergency evacuation simulator.

## Input

**Source**: Architectural floor plan drawing (image provided)
- Approximate dimensions: 15m × 9m
- Total area: ~135 sqm
- Multi-room residential/office space
- Chinese labels on original drawing

## Output

### 1. Graph Structure
- **13 vertices** (rooms, hallways, stairwell, exit)
- **14 edges** (doorways and connections)
- Realistic dimensions and areas

### 2. Configuration File
`config_realistic_apartment.json` with:
- Vertex properties (type, dimensions, capacity, priority)
- Edge properties (max flow, burn rates)
- Occupancy probabilities per room
- Fire origin specification

### 3. Metadata

**Rooms (7 total):**
```
Bedrooms (3):     13.7 sqm, 13.0 sqm, 16.0 sqm
Living Room (1):  25.2 sqm (large)
Offices (3):       9.9 sqm, 10.8 sqm, 11.7 sqm
```

**Circulation (5 spaces):**
```
Hallways (3):      9.6 sqm, 12.0 sqm, 9.0 sqm
Entrance Hall (1): 9.0 sqm
Stairwell (1):    10.1 sqm
```

**Exits (1):**
```
Main Door:         Primary entrance/exit
```

### 4. Room-Specific Parameters

| Room Type | Priority | Capacity | Sweep Time | Occupancy |
|-----------|----------|----------|------------|-----------|
| Bedroom   | 3 (HIGH) | 4 people | 3 seconds  | 15% / sqm |
| Living Room | 2 (MED) | 10 people | 4 seconds | 10% / sqm |
| Office    | 2 (MED)  | 6 people | 2 seconds  | 8% / sqm  |
| Hallway   | 1 (LOW)  | 20 people | 1 second  | 0% (empty) |
| Stairwell | 1 (LOW)  | 10 people | 2 seconds | 0% (empty) |

## Tools Created

### 1. **analyze_floorplan.py**
Converts floor plan analysis into simulation config:
- Reads floor plan structure (rooms, connections)
- Calculates areas from dimensions
- Assigns room types and priorities
- Generates occupancy probabilities
- Creates graph representation (vertices + edges)
- Outputs JSON configuration file

### 2. **run_scenario.py**
Easy scenario launcher:
- Switch between different buildings
- List available scenarios
- Run in manual or auto mode
- Compare building performance

### 3. **test_realistic_apartment.py**
Test script for apartment layout:
- Loads apartment configuration
- Runs simulation with 3 firefighters
- Uses greedy AI model
- Reports performance statistics

## Key Findings

### Performance Comparison

| Building | Area | Exits | Rooms | Firefighters | Survival Rate |
|----------|------|-------|-------|--------------|---------------|
| **Simple Office** | 600 sqm | 2 | 6 | 2 | **34.8%** |
| **Realistic Apartment** | 135 sqm | 1 | 7 | 3 | **0%** |

### Why Apartment is Harder

1. **Single Exit** - Bottleneck vs two exits in office
2. **Complex Topology** - More branching, longer paths
3. **Stairwell** - Adds complexity (vertical circulation)
4. **Higher Density** - More people per sqm
5. **Mixed Priorities** - Bedrooms (high) vs offices (medium)

This demonstrates the **value of multiple building types** for testing models!

## Usage

### Quick Start
```bash
# Generate the config from floor plan analysis
python3 analyze_floorplan.py

# Test without visualization
python3 test_realistic_apartment.py

# Visualize in manual mode
python3 run_scenario.py apartment manual

# Watch AI in auto mode
python3 run_scenario.py apartment auto
```

### Compare Scenarios
```bash
# Easy building (good performance)
python3 run_scenario.py office auto

# Hard building (poor performance - needs better model!)
python3 run_scenario.py apartment auto
```

## Applications for HiMCM Paper

### 1. Model Validation
- Test on **multiple building types**
- Show model works on diverse layouts
- Demonstrate robustness (or lack thereof!)

### 2. Comparative Analysis
- Simple vs Complex layouts
- Single vs Multiple exits
- Single-use vs Mixed-use buildings

### 3. Prioritization Testing
- High-priority rooms (bedrooms)
- Low-priority areas (hallways)
- Critical zones (near fire origin)

### 4. Real-World Scenarios
- Apartment evacuation at night (bedrooms occupied)
- Office evacuation during work hours
- Mixed-use building challenges

### 5. Model Improvements
- Current greedy model fails on apartment (0% survival)
- Need better pathfinding/strategy
- Motivates development of advanced models
- Can quantify improvement (0% → X%)

## Graph Visualization

```
Floor Plan Topology:

                [Exit]
                  |
            [Entrance Hall]
            /     |     \
    [Living]  [Stair]  [Hall Central]
         |       |      /    |    \
    [Hall E]    |   [R2] [R5] [R6]
      /  \      |
  [R3]  [R1] [Hall W]
              /     \
           [R1]    [R4]

Legend:
  [Exit]   - Main door
  [RX]     - Room X
  [Hall X] - Hallway segment X
  [Stair]  - Stairwell
  [Living] - Living room
```

## Future Enhancements

### More Building Types
- School (classrooms, cafeteria, gym)
- Hospital (patient rooms, ICU, ER)
- Warehouse (large open spaces)
- Shopping mall (stores, food court)
- Multi-floor buildings (use stairwell)

### Automated Conversion
- OCR for floor plan images
- Auto-detect rooms and doors
- Machine learning for classification
- Generate configs automatically

### Advanced Features
- Window exits (emergency egress)
- Fire doors (delay spread)
- Sprinkler systems
- Elevator shafts (hazard zones)
- Assembly points (muster stations)

## Files Generated

1. **config_realistic_apartment.json** - Simulation config
2. **analyze_floorplan.py** - Conversion tool
3. **test_realistic_apartment.py** - Test script
4. **run_scenario.py** - Scenario launcher
5. **FLOORPLAN_CONVERSION.md** - Detailed guide
6. **FLOOR_PLAN_SUMMARY.md** - This summary

## Conclusion

Successfully demonstrated:
✅ Real floor plan → graph conversion
✅ Realistic building parameters
✅ Multi-room type support
✅ Challenging test case for models
✅ Easy scenario switching
✅ Comprehensive documentation

The apartment configuration provides an excellent **benchmark** for testing and improving evacuation strategies!

## For Your Paper

Use this to show:
1. **Model generalization** - works on different building types
2. **Realistic scenarios** - based on actual architecture
3. **Comparative analysis** - quantify difficulty differences
4. **Model limitations** - exposes weaknesses in simple strategies
5. **Room for improvement** - motivates advanced techniques

The 0% survival rate on the apartment layout is actually **valuable** - it shows where simple approaches fail and justifies more sophisticated methods!
