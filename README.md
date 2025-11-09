# Emergency Evacuation Simulator

A graph-based simulator for modeling building evacuations during emergencies, created for HiMCM 2025 Problem A.

## Installation

Install the required dependencies:

```bash
pip3 install -r requirements.txt
```

Or install pygame directly:

```bash
pip3 install pygame
```

## Project Structure

```
Core Simulation:
  simulator.py                      - Core simulation engine
  config_example.json               - Simple office building (6 rooms)
  config_realistic_apartment.json   - Realistic apartment (13 spaces)

Visualization:
  visualizer.py                     - Interactive pygame visualizer
  demo_visualizer.py                - Demo script with simple AI model
  run_scenario.py                   - Scenario launcher (easy building switching)

Floor Plan Tools:
  analyze_floorplan.py              - Convert floor plans to graph configs
  FLOORPLAN_CONVERSION.md           - Floor plan conversion guide

Testing:
  test_simulator.py                 - Core simulator tests
  test_visualizer_model.py          - Test AI model performance
  test_realistic_apartment.py       - Test apartment scenario
  test_rescue_count.py              - Verify rescue counting
  test_firefighter_switching.py     - Test selection cycling

Documentation:
  README.md                         - This file
  CHANGELOG.md                      - Visualizer improvements log
  FIREFIGHTER_SWITCHING_FIX.md      - Selection cycling documentation
  requirements.txt                  - Python dependencies
```

## Quick Start

### 1. Test the Simulator (No GUI)

Run the test suite to verify the simulator works:

```bash
python3 test_simulator.py
```

This will run 5 tests demonstrating:
- Basic simulation setup
- Firefighter movement
- Occupant rescue mechanics
- Random fire events
- Full sweep scenario

### 2. Manual Control Mode

Play the game yourself - control firefighters manually:

```bash
python3 demo_visualizer.py manual
```

**Controls:**
- Click on firefighters (orange circles) to select them (yellow outline appears)
  - If multiple firefighters at same spot, click again to cycle through them
  - Look for yellow "x2" or "x3" badge showing count
- Click on adjacent vertices to **queue** movement
- Click "Pick Up (5)" button to **queue** pickup action
- Click "Drop Off" button to **queue** drop-off action
- Click "Step" to **execute** all queued actions and advance time by 1 tick

**Important**: In manual mode, time ONLY advances when you click "Step". Queue multiple actions per firefighter!

**Visual Guide:**
- Blue numbers = occupant count (only for visited rooms - fog of war!)
- Gray "?" = unvisited room
- Red percentages = smoke level (e.g., "45%")
- Gray overlay = smoke (darker = more dangerous)
- Red circles = burned rooms
- Dashed red lines = blocked corridors
- Orange circles = firefighters
- Yellow outline = selected firefighter
- Yellow "x2" badge = multiple firefighters at same location (click to cycle)
- Status bar shows "Pending: X actions" when actions are queued

### 3. Auto Mode with AI

Watch a simple AI model control the firefighters:

```bash
python3 demo_visualizer.py auto
```

The greedy AI will automatically:
1. Move to nearest unvisited rooms
2. Pick up occupants
3. Return to exits to rescue them

Use this to test and compare against your own decision models.

### 4. Running Different Building Scenarios

Use the scenario launcher to test different building types:

```bash
# List available scenarios
python3 run_scenario.py list

# Run simple office building (manual mode)
python3 run_scenario.py office manual

# Run realistic apartment (auto mode)
python3 run_scenario.py apartment auto
```

**Available Scenarios:**
- **office**: Simple 6-room office (2 exits, easy layout)
- **apartment**: Realistic 13-space apartment (1 exit, complex layout with stairwell)

### 5. Converting Your Own Floor Plans

Analyze a floor plan image and create a configuration:

```bash
# Edit analyze_floorplan.py with your floor plan details
python3 analyze_floorplan.py

# This generates a new config JSON file
# Then test it:
python3 test_realistic_apartment.py
```

See `FLOORPLAN_CONVERSION.md` for details on the conversion process.

## Configuration Format

Buildings are defined in JSON format. See `config_example.json` for the structure:

```json
{
  "vertices": [
    {
      "id": "office_1",
      "type": "room",
      "room_type": "office",
      "capacity": 20,
      "priority": 2,
      "sweep_time": 2,
      "area": 100.0
    }
  ],
  "edges": [
    {
      "id": "e1",
      "vertex_a": "office_1",
      "vertex_b": "hallway_1",
      "max_flow": 5,
      "base_burn_rate": 0.0001
    }
  ],
  "occupancy_probabilities": {
    "office_1": 0.05
  },
  "fire_params": {
    "origin": "office_1"
  }
}
```

## Creating Your Own Decision Model

To create a custom AI model:

```python
class MyModel:
    def get_actions(self, state):
        """
        Generate actions based on current state.

        Args:
            state: Dict with 'tick', 'graph', 'firefighters', 'discovered_occupants'

        Returns:
            Dict: {firefighter_id: [actions]}
            Action format: {'type': 'move'|'pick_up'|'drop_off', ...}
        """
        actions = {}

        for ff_id, ff_state in state['firefighters'].items():
            # Your decision logic here
            ff_actions = [
                {'type': 'move', 'target': 'some_vertex'},
                {'type': 'pick_up', 'count': 5}
            ]
            actions[ff_id] = ff_actions

        return actions
```

Then run it:

```python
from visualizer import EvacuationVisualizer
from simulator import Simulation
import json

with open('config_example.json') as f:
    config = json.load(f)

sim = Simulation(config, num_firefighters=2, fire_origin='office_bottom_center', seed=42)
model = MyModel()

viz = EvacuationVisualizer(manual_mode=False)
viz.run(sim, model)
```

## Simulator API

### Key Methods

**Simulation.update(actions)** - Execute one tick
```python
actions = {
    'ff_0': [
        {'type': 'move', 'target': 'hallway_left'},
        {'type': 'pick_up', 'count': 5}
    ],
    'ff_1': [
        {'type': 'drop_off'}
    ]
}
results = sim.update(actions)
```

**Simulation.read()** - Get observable state
```python
state = sim.read()
# Returns: {tick, graph, firefighters, discovered_occupants, fire_origin}
```

**Simulation.get_stats()** - Get performance metrics
```python
stats = sim.get_stats()
# Returns: {tick, rescued, dead, remaining, total_initial, time_minutes}
```

## Features

### Simulator Features
- Graph-based building representation
- Flow-constrained movement (max people per corridor)
- Stochastic fire spread (edges deleted, rooms burn down)
- Smoke accumulation and smoke-related deaths
- Room type variations (office, daycare, warehouse)
- Seed-based reproducibility

### Visualizer Features
- Real-time graph visualization
- Manual control mode (play as firefighter commander)
- Auto mode (test AI models)
- Visual indicators for smoke, fire, occupants
- Statistics tracking
- Adjustable simulation speed
- Pause/step controls

## Next Steps

1. Create more building layouts (multi-floor, complex geometries)
2. Implement advanced decision models (A*, reinforcement learning, etc.)
3. Add comparison/replay mode
4. Build layout editor tool
5. Analyze optimal strategies for different building types

## Tips for Competition

- Test multiple building layouts (1-story office, multi-floor, daycare, etc.)
- Vary number of firefighters to find optimal count
- Consider redundancy strategies (multiple sweeps of same room)
- Prioritize high-value rooms (daycare > office)
- Account for dynamic hazards (fire spread predictions)
- Compare against manual control to demonstrate model effectiveness

Good luck with HiMCM 2025!
