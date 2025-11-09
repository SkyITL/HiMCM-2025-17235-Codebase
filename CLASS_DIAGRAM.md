# Emergency Evacuation Simulator - Class Diagram & Model Summary

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                     │
│                                                              │
│  ┌──────────────────┐          ┌─────────────────────────┐ │
│  │  Manual Control  │          │   Auto Mode with AI     │ │
│  │   Visualizer     │          │   Model (Greedy/etc)    │ │
│  └────────┬─────────┘          └───────────┬─────────────┘ │
│           │                                  │                │
└───────────┼──────────────────────────────────┼────────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   VISUALIZATION LAYER                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           EvacuationVisualizer                         │ │
│  │  - Pygame window management                            │ │
│  │  - User input handling                                 │ │
│  │  - Action queuing (manual mode)                        │ │
│  │  - Statistics display                                  │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
│  ┌──────────────────▼─────────────────────────────────────┐ │
│  │           LayoutVisualizer                             │ │
│  │  - Graph layout calculation                            │ │
│  │  - Vertex positioning (manual/automatic)               │ │
│  │  - Edge/vertex rendering                               │ │
│  │  - Firefighter rendering                               │ │
│  │  - Smoke/fire visualization                            │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   SIMULATION ENGINE                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  Simulation                            │ │
│  │  - Main game loop orchestrator                         │ │
│  │  - Time management (tick-based)                        │ │
│  │  - Action execution and validation                     │ │
│  │  - Random event generation                             │ │
│  │  - Statistics tracking                                 │ │
│  └──┬──────────────┬──────────────┬──────────────────────┘ │
│     │              │              │                         │
│  ┌──▼────┐   ┌─────▼────┐   ┌────▼──────┐                 │
│  │ Graph │   │Firefighte│   │  Events   │                 │
│  │       │   │  rs      │   │ & Physics │                 │
│  └───────┘   └──────────┘   └───────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Core Classes

### 1. **Vertex** (Graph Node)
Represents a physical space in the building.

```python
@dataclass
class Vertex:
    # Identity
    id: str                    # Unique identifier
    type: str                  # 'room', 'hallway', 'exit', 'window_exit', 'stairwell'
    room_type: str             # 'bedroom', 'office', 'living_room', 'none'

    # Occupancy
    occupant_count: int        # Current people in this space
    capacity: int              # Maximum capacity

    # Evacuation properties
    priority: int              # Sweep priority (3=high, 1=low)
    sweep_time: int            # Seconds to sweep this space

    # Hazard state
    smoke_level: float         # 0.0 to 1.0
    is_burned: bool            # Destroyed by fire

    # Physical
    area: float                # Square meters
    visual_position: dict      # {x: 0.0-1.0, y: 0.0-1.0} for rendering

    # Methods
    apply_smoke_deaths(rng) → int      # Apply casualties from smoke
    burn_down() → int                   # Destroy room, kill occupants
```

### 2. **Edge** (Connection/Corridor)
Represents a doorway or passage between vertices.

```python
@dataclass
class Edge:
    # Identity
    id: str                    # Unique identifier
    vertex_a: str              # First endpoint
    vertex_b: str              # Second endpoint

    # Flow constraints
    max_flow: int              # Max people per tick

    # Hazard
    base_burn_rate: float      # Base probability of blocking
    exists: bool               # Still passable?
    distance_to_fire: float    # Computed from fire origin

    # Methods
    get_burn_probability(tick) → float  # Dynamic burn chance
```

### 3. **Firefighter** (Responder)
Represents a firefighter/responder agent.

```python
@dataclass
class Firefighter:
    # Identity
    id: str                    # Unique identifier
    position: str              # Current vertex_id

    # Capabilities
    movement_points_per_tick: int  # Actions per tick (usually 5)
    capacity: int              # Max people to escort
    escorting_count: int       # Currently escorting

    # Knowledge
    visited_vertices: set      # Discovered locations

    # Methods
    pick_up(n, vertex) → bool          # Pick up n people
    drop_off(vertex) → int             # Drop off at vertex
    mark_visited(vertex_id)            # Mark as discovered
```

### 4. **Simulation** (Main Engine)
Orchestrates the entire simulation.

```python
class Simulation:
    # State
    tick: int                  # Current time step
    vertices: Dict[str, Vertex]
    edges: Dict[str, Edge]
    adjacency: Dict[str, List]  # Graph structure
    firefighters: Dict[str, Firefighter]

    # Statistics
    rescued_count: int
    dead_count: int

    # Configuration
    fire_origin: str           # Where fire started
    rng: Random                # Seeded random generator

    # Methods
    __init__(config, num_firefighters, fire_origin, seed)
    update(actions) → results      # Execute one tick
    read() → state                 # Get observable state
    get_stats() → statistics       # Get performance metrics

    # Private methods
    _build_graph(config)           # Create graph from config
    _initialize_occupants(probs)   # Spawn people
    _initialize_firefighters(n)    # Create responders
    _execute_action(ff, action)    # Perform single action
    _apply_random_events()         # Fire spread, casualties
    _update_smoke()                # Smoke diffusion
```

### 5. **EvacuationVisualizer** (UI)
Pygame-based interactive visualizer.

```python
class EvacuationVisualizer:
    # Display
    screen: pygame.Surface
    width, height: int
    layout: LayoutVisualizer

    # Mode
    manual_mode: bool          # Manual vs auto control
    paused: bool               # Time paused?
    tick_speed: int            # Ticks per second

    # Manual mode state
    selected_firefighter: str  # Currently selected
    pending_actions: Dict      # Queued actions

    # UI
    buttons: List[Button]

    # Methods
    run(sim, model)                # Main loop
    draw_stats(screen, sim)        # Render UI
    _do_simulation_step(sim, model)  # Execute tick
    _manual_move(sim, target)      # Queue movement
    _manual_action(sim, type, count)  # Queue action
```

### 6. **LayoutVisualizer** (Rendering)
Handles graph visualization and rendering.

```python
class LayoutVisualizer:
    # State
    width, height: int
    vertex_positions: Dict[str, Tuple[float, float]]
    layout_calculated: bool

    # Methods
    calculate_layout(sim)              # Position vertices
    _try_manual_layout(sim) → bool     # Use config positions
    _automatic_layout(sim)             # Auto-generate layout

    draw_edge(screen, edge_id, sim)    # Render corridor
    draw_vertex(screen, vertex_id, sim, selected, show_all, visited)
    draw_firefighter(screen, ff_id, sim, selected, at_same_pos)

    get_vertex_at_position(pos) → vertex_id  # Click detection
```

## Data Flow

### Read Flow (Observation)
```
Simulation
    ↓ read()
Observable State
    ├─ Complete graph structure
    ├─ Firefighter positions/states
    ├─ Discovered occupant counts
    ├─ Edge existence (blocked/open)
    └─ Current tick
    ↓
Model / User
    ↓ decide actions
Action Dictionary
```

### Write Flow (Action Execution)
```
Model / User
    ↓ generate actions
Action Dictionary:
{
    'ff_0': [
        {'type': 'move', 'target': 'room_1'},
        {'type': 'pick_up', 'count': 5}
    ],
    'ff_1': [
        {'type': 'drop_off'}
    ]
}
    ↓ update(actions)
Simulation
    ├─ Validate actions
    ├─ Execute movements
    ├─ Update escorting
    ├─ Apply random events
    ├─ Update smoke/fire
    └─ Track casualties
    ↓ results
Results Dictionary:
{
    'tick': 42,
    'action_results': {...},
    'events': [...],
    'rescued_this_tick': 5,
    'dead_this_tick': 2
}
```

## State Machine

### Simulation State
```
INITIALIZING
    ↓ __init__()
READY
    ↓ update() called
PROCESSING ACTIONS
    ├─ Validate
    ├─ Execute
    └─ Record results
    ↓
APPLYING EVENTS
    ├─ Random edge deletion
    ├─ Random room burndown
    └─ Smoke deaths
    ↓
UPDATING PHYSICS
    ├─ Smoke diffusion
    └─ Fire spread probabilities
    ↓
READY (next tick)
```

### Firefighter State
```
AT_POSITION
    ↓ move action
MOVING
    ↓ arrive
AT_POSITION
    ↓ pick_up action
ESCORTING
    ↓ move to exit
AT_EXIT
    ↓ drop_off action
RESCUED_PEOPLE
    ↓
AT_POSITION (empty hands)
```

### Vertex State
```
CLEAR
    ↓ smoke spreads
SMOKY
    ↓ fire reaches
BURNING
    ↓
DESTROYED
```

## Configuration Format

### JSON Structure
```json
{
  "description": "Building description",
  "dimensions": {
    "width_m": 15.0,
    "height_m": 9.0,
    "total_area_sqm": 135.0
  },
  "vertices": [
    {
      "id": "room_1",
      "type": "room",
      "room_type": "bedroom",
      "capacity": 4,
      "priority": 3,
      "sweep_time": 3,
      "area": 13.7,
      "visual_position": {"x": 0.15, "y": 0.15}
    }
  ],
  "edges": [
    {
      "id": "e_1",
      "vertex_a": "room_1",
      "vertex_b": "hallway_west",
      "max_flow": 5,
      "base_burn_rate": 0.0002
    }
  ],
  "occupancy_probabilities": {
    "room_1": 0.15
  },
  "fire_params": {
    "origin": "room_5",
    "initial_smoke_level": 0.3
  }
}
```

## Key Algorithms

### 1. Smoke Diffusion
```python
for each vertex:
    new_smoke = vertex.smoke * 0.95  # Slight decay
    for each neighbor:
        if edge.exists:
            new_smoke += neighbor.smoke * 0.1
    if vertex == fire_origin:
        new_smoke += 0.05
    vertex.smoke = min(1.0, new_smoke)
```

### 2. Smoke Deaths
```python
death_probability = smoke_level³ × 0.02
for each occupant:
    if random() < death_probability:
        deaths += 1
```

### 3. Fire Spread (Edge)
```python
time_factor = 1 + tick / 100
distance_factor = 1 / (1 + distance_to_fire / 10)
burn_prob = base_burn_rate × time_factor × distance_factor
```

### 4. Layout Calculation
```python
# Try config positions first
if vertices have visual_position:
    use config positions
else:
    # Automatic grid-based layout
    place exits on sides
    place hallways in center
    place rooms in grid around hallways
```

## Fog of War (Information Hiding)

### Manual Mode
- **Hidden**: Occupant counts in unvisited rooms (show "?")
- **Visible**: Graph structure, smoke levels, firefighter positions
- **Discovered**: Room occupants after first visit

### Auto Mode
- **All information visible** for AI testing

## Performance Metrics

### Tracked Statistics
- **rescued**: People safely evacuated
- **dead**: Casualties (smoke + fire)
- **remaining**: Still inside building
- **total_initial**: Starting population
- **tick**: Time elapsed
- **time_minutes**: Real-world time estimate
- **survival_rate**: rescued / total_initial

## Extension Points

### Adding New Room Types
1. Add to `room_type` enum
2. Define in config with priority/sweep_time
3. Update `analyze_floorplan.py` logic

### Adding New AI Models
1. Implement `get_actions(state) → actions`
2. Pass to `visualizer.run(sim, model)`

### Adding New Hazards
1. Add property to Vertex/Edge
2. Update `_apply_random_events()`
3. Update rendering in LayoutVisualizer

### Multi-Floor Support
1. Use `stairwell` type vertices
2. Add `floor` property to vertices
3. Update layout to stack floors vertically
4. Restrict movement to same-floor or via stairs

## File Dependencies

```
simulator.py
    ↑
visualizer.py ─→ demo_visualizer.py (SimpleGreedyModel)
    ↑
run_scenario.py

config_example.json ←─ analyze_floorplan.py
config_realistic_apartment.json ←┘

test_simulator.py ─→ simulator.py
test_realistic_apartment.py ─→ simulator.py + demo_visualizer.py
```

## Summary

The system uses a **graph-based** representation where:
- **Vertices** = Physical spaces (rooms, hallways, exits)
- **Edges** = Connections (doorways, corridors)
- **Firefighters** = Agents that move on graph
- **Simulation** = Discrete-time step processor
- **Visualizer** = Interactive UI with manual/auto modes

Key design principles:
- ✅ **Separation of concerns** (simulation ≠ visualization)
- ✅ **Observable state** (model can't cheat)
- ✅ **Reproducible** (seeded random)
- ✅ **Extensible** (easy to add buildings/models)
- ✅ **Turn-based** (strategic planning)
- ✅ **Realistic physics** (smoke, fire, flow constraints)
