# Unit Length Adjustments - 1 Meter Units

## Summary

The simulator has been adjusted to work properly with **1 meter unit lengths** instead of the original 5 meter units.

## Changes Made

### Tick Duration: 10s → 2s → 1s

**Original:**
- `TICK_DURATION = 10` seconds per tick
- Movement: 2 units per tick = 2m / 10s = **0.2 m/s** (way too slow!)

**Intermediate:**
- `TICK_DURATION = 2` seconds per tick
- Movement: 2 units per tick = 2m / 2s = **1.0 m/s** (too slow for firefighters)

**Current:**
- `TICK_DURATION = 1` second per tick
- Movement: 2 units per tick = 2m / 1s = **2.0 m/s** (realistic for trained firefighters!)

### Movement Speed

**Firefighters:**
- 2 actions (movement points) per tick
- 1 second per tick = 0.5 seconds per action
- Speed: **2.0 m/s**
- This is realistic for trained firefighters moving quickly through a building
- Fast walking/light jogging pace, appropriate for professionals who know the layout

**Occupants (Instructed):**
- Also move at 2.0 m/s once instructed
- Represents evacuation urgency

### Time Scale Implications

**Fire Spread:**
- Fire spread calculations use `TICK_DURATION` automatically
- With 1s ticks, fire spreads 10× faster in simulation time
- But same real-world time (burn rates are per-second)

**Smoke Accumulation:**
- Smoke generation scales with `TICK_DURATION`
- Also adjusts automatically with shorter ticks

**Example Timeline (1m hallway):**
- Old (10s ticks): 5 ticks = 50 seconds to traverse
- Intermediate (2s ticks): 1 tick = 2 seconds to traverse
- Current (1s ticks): 0.5 ticks = 0.5 seconds to traverse ✓

## Realistic Speeds

For reference, these are typical emergency speeds:

| Condition | Speed (m/s) | Speed (mph) |
|-----------|-------------|-------------|
| Normal walking | 1.4 | 3.1 |
| **Fast walking** | **2.0** | **4.5** |
| Emergency evacuation | 1.0-1.2 | 2.2-2.7 |
| Through fire/smoke | 0.8-1.0 | 1.8-2.2 |
| Crawling (thick smoke) | 0.3-0.5 | 0.7-1.1 |
| Jogging | 2.5-3.5 | 5.6-7.8 |

Our simulation uses **2.0 m/s**, which is appropriate for:
- Trained firefighters moving quickly
- Clear or lightly smoky corridors
- Professional responders who know the building
- Balance between speed and safety

## Graph Maker Integration

The graph maker already uses 1m units:
- Each edge represents 1 meter
- Room areas in square meters
- Corridor widths in meters
- Measurement scale in pixels/meter

**Everything is now consistent!**

## Testing

To verify the changes work correctly:

```bash
# Run a test simulation
python3 test_simulator.py

# Check movement speeds in visualizer
python3 demo_visualizer.py auto
```

**Expected behavior:**
- Firefighters move at reasonable speed
- Fire spreads realistically (not too fast/slow)
- Occupants evacuate in believable time
- Simulation runs 5× more ticks, but represents same real time

## Backward Compatibility

**Old config files:** Still work! The only change is internal tick duration.

**Graph files:** No changes needed - they already use meters.

**Visualization:** No changes - displays correctly with new timing.
