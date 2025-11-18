# Quick Reference Card

## Installation
```bash
pip3 install pygame
```

## Run Scenarios

### List Available Buildings
```bash
python3 run_scenario.py list
```

### Play Manually (You Control Firefighters)
```bash
python3 run_scenario.py office manual      # Easy building
python3 run_scenario.py apartment manual   # Hard building
```

### Watch AI (Automatic Mode)
```bash
python3 run_scenario.py office auto
python3 run_scenario.py apartment auto
```

## Test Without GUI
```bash
python3 test_simulator.py                  # Basic tests
python3 test_visualizer_model.py           # Test AI on simple building
python3 test_realistic_apartment.py        # Test AI on apartment
```

## Create New Building
```bash
# 1. Edit analyze_floorplan.py with your floor plan details
# 2. Run the analyzer
python3 analyze_floorplan.py

# 3. Test the new config
python3 test_realistic_apartment.py

# 4. Add to run_scenario.py SCENARIOS dict
```

## Manual Mode Controls

### Select & Control
- **Click** firefighter (orange circle) to select
- **Click again** to cycle if multiple at same spot
- Look for **yellow "x2"** badge

### Queue Actions
- **Click** adjacent room = queue movement
- **"Pick Up (5)"** button = queue pickup
- **"Drop Off"** button = queue drop-off
- **"Step"** button = **execute all** queued actions + advance time

### Other
- **Play/Pause** = toggle auto-time (usually keep paused in manual)
- **Speed +/-** = adjust tick rate (for auto mode)

## Visual Guide

### Colors
- 🔵 **Blue numbers** = occupants (only in visited rooms)
- ❔ **Gray "?"** = unvisited room (fog of war)
- 🔴 **Red %** = smoke level
- ⚫ **Gray halo** = smoke cloud
- 🔥 **Red circle** = burned room
- ➖ **Dashed line** = blocked corridor
- 🟠 **Orange circle** = firefighter
- 🟡 **Yellow outline** = selected
- 🟡 **Yellow "x2"** = multiple firefighters here

### Status Bar
- **Pending: X actions** = queued actions waiting for Step
- **Survival: X%** = rescued / total ratio

## Building Comparisons

| Building | Area | Exits | Rooms | Difficulty |
|----------|------|-------|-------|------------|
| **Office** | 600 sqm | 2 | 6 | ⭐ Easy |
| **Apartment** | 135 sqm | 1 | 7 | ⭐⭐⭐ Hard |

## Performance Benchmarks

### Greedy AI Results
```
Simple Office:      34.8% survival (8/23 rescued)
Realistic Apartment: 0.0% survival (0/8 rescued)
```

Shows apartment layout is **challenging** - needs better strategies!

## File Organization

```
Configs:
  config_example.json               # Simple office
  config_realistic_apartment.json   # Apartment

Main Tools:
  run_scenario.py                   # ← Start here!
  simulator.py                      # Core engine
  visualizer.py                     # Pygame GUI

Tests:
  test_simulator.py                 # Core tests
  test_realistic_apartment.py       # Apartment test

Documentation:
  README.md                         # Full guide
  QUICK_REFERENCE.md               # This file
  FLOORPLAN_CONVERSION.md          # How to convert floor plans
  FLOOR_PLAN_SUMMARY.md            # Apartment analysis
```

## Common Tasks

### Compare Two Strategies
```bash
# Run scenario 1
python3 run_scenario.py office manual
# Note your score

# Run scenario 2
python3 run_scenario.py office auto
# Compare against AI
```

### Test Your Own Model
```python
# In your model file:
class MyModel:
    def get_actions(self, state):
        actions = {}
        # Your logic here
        return actions

# Then run:
from visualizer import EvacuationVisualizer
viz = EvacuationVisualizer(manual_mode=False)
viz.run(sim, MyModel())
```

### Debug Why AI Fails
```bash
# Run with console output
python3 test_realistic_apartment.py

# Watch what AI does wrong
python3 run_scenario.py apartment auto

# Compare to your manual strategy
python3 run_scenario.py apartment manual
```

## Tips for HiMCM Paper

1. **Run multiple scenarios** - office (easy) + apartment (hard)
2. **Document both** - show model works on diverse layouts
3. **Compare performance** - quantify difficulty difference
4. **Show limitations** - 0% on apartment motivates improvements
5. **Test improvements** - measure before/after of optimizations

## Troubleshooting

### Pygame not found
```bash
pip3 install pygame
```

### File not found
```bash
# Make sure you're in the right directory
cd /Users/skyliu/HiMCM2025
ls *.py  # Should see all Python files
```

### Simulation too slow
- Click "Speed +" button
- Or edit `self.tick_speed` in visualizer.py

### Can't select firefighter
- They might be overlapping - click multiple times to cycle
- Look for yellow "x2" badge

## Quick Demo for Judges

```bash
# 1. Show simple building
python3 run_scenario.py office manual

# 2. Demonstrate controls (queue actions, click Step)

# 3. Show AI on same building
python3 run_scenario.py office auto

# 4. Show harder building
python3 run_scenario.py apartment auto

# 5. Explain why it fails (topology, single exit)

# 6. Show your improved model beats the baseline!
```

## Key Features to Highlight

✅ **Fog of war** - realistic information constraints
✅ **Action queuing** - strategic turn-based planning
✅ **Multiple buildings** - generalization across layouts
✅ **Realistic physics** - smoke spread, fire dynamics
✅ **Visual feedback** - easy to understand and debug
✅ **Reproducible** - seeded random for consistent testing

---

**Remember**: The goal is to save as many people as possible!
Good luck with your HiMCM competition! 🚒🔥
