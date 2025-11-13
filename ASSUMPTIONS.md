
## 1. Building Representation

### 1.1 Graph Model
- **Buildings can be represented as graphs** where vertices are spaces (rooms, hallways, exits) and edges are connections (doorways, corridors)
- **Unit length**: Long hallways are splitted such that each edge represents 1 meter of distance
- **Visual positions**: Vertex coordinates are stored for visualization fire spreading and spatial understanding, but the simulation operates on the graph topology

### 1.2 Vertex (Space) Properties
- **Types**: rooms, hallways, intersections, stairwells, exits, window_exits
- **Area**: Measured in square meters (m²), affects:
  - Visual representation size
  - Room volume calculation (area × ceiling height)
  - Smoke concentration 

- **Ceiling height**: Default 3.0 meters for all spaces (TBD)
- **Capacity**: Maximum occupants the space can hold
- **Priority**: TBD, related to weighting

- **Sweep time**: TBD, can be related to size, can be related to type

### 1.3 Edge (Connection) Properties
- **Max flow**: Maximum number of people that can traverse per tick
- **Width**: Corridor width in meters (default 2.0m), affects:
  - Fire spread resistance (wider = harder to spread)
- **Base burn rate**: Probability per second that the edge burns (default 0.0001)
- **Destructibility**: Edges can burn and become impassable

---

## 2. Time and Movement

### 2.1 Temporal Model
- **Tick duration**: 1 seconds per tick 
- **Movement**: All entities move discretely between vertices
- **Actions per tick**: Firefighters can perform 2 actions (or more) per tick
- **Movement speed**: 2.0 m/s through hazardous conditions
  - Realistic for emergency movement through fire/smoke
  - Slower than normal walking (2 m/s)
  - Appropriate for carrying equipment or helping occupants

### 2.2 Movement Constraints
- **Graph topology**: Movement is constrained to edges
- **No diagonal movement**: Movement follows defined corridors only
- **Edge capacity**: Edges enforce max_flow constraints
- **Blocked edges**: Burned edges are impassable

---

## 3. Occupants

### 3.1 Occupant Types
- **Capable occupants**: Can walk independently once instructed
- **Incapable occupants**: Must be carried by firefighters (infants, elderly, disabled)
- **Instructed occupants**: Capable people given evacuation instructions

### 3.2 Occupant Distribution
- **Probabilistic placement**: Occupants placed based on room-specific probabilities
- **Initial location**: All occupants start in rooms (not hallways)
- **Room capacity constraints**: Cannot exceed room capacity

### 3.3 Occupant Behavior
- **Uninstructed capable**: Remain stationary until firefighter provides instructions
- **Instructed capable**: Autonomously move toward exits
- **Incapable**: Must be physically carried to exits
- **No panic or  irrational behavior**: TBD
- **Perfect pathfinding**: Instructed occupants take "optimal" paths to exits

---

## 4. Firefighters

### 4.1 Capabilities
- **Actions per tick**: 2 movement/action points
- **Movement speed**: 2 units per tick = 2.0 m/s (with 2s tick duration)
- **Carrying capacity**: Can carry multiple incapable occupants simultaneously
- **Instruction**: Can instruct all capable occupants in current vertex in one action
- **Perfect graph information**: Know the graph structure
- **Fog of war**: Only discover actual occupant counts upon visiting rooms

### 4.2 Spawn and Positioning
- **Initial placement**: Firefighters can start at exit vertices in the graph
  - Default: spawn at exit vertices (distributed evenly)
  - Custom: can specify any specific exits
  - No constraints on initial positioning

- **Configurable count**: 1-20 firefighters

- **Post-rescue flexibility**: After dropping off occupants at exits, firefighters are free to:
  - Re-enter the building from any position
  - Be repositioned by the control model
  - Continue evacuation operations
  - No "return to base" requirement

- **Strategic implications**: Initial placement and post-rescue repositioning are optimization variables controlled by the external decision model

### 4.3 Actions
1. **Move**: Traverse one edge to adjacent vertex (costs 1 action)
2. **Instruct**: Give evacuation instructions to all capable occupants in current vertex (costs 1 action)
3. **Pick up**: Carry one or more incapable occupants (costs 1 action per person)
4. **Drop off**: Release carried occupants at exit (costs 1 action, rescues them)

---

## 5. Fire Dynamics

### 5.1 Fire Origin
- **Single origin**: Fire starts at one specified vertex
- **Initial smoke**: 30% of room volume filled with smoke initially
- **No spontaneous ignition**: Fire only spreads from origin

### 5.2 Fire Spread (Edges/Corridors)
- **Probabilistic burning**: Edges burn based on:
  - Time elapsed (fire gr\
  ows over time)
  - Physical distance from fire origin (closer = higher probability)
  - Corridor width (wider = more resistant)
  - Base burn rate

- **Burn probability formula**:
  ```
  P = base_burn_rate × time_factor × distance_factor × width_factor × tick_duration

  where:
    time_factor = 1 + (time_in_seconds / 100)
    distance_factor = 1 / (1 + distance_to_fire / 10)
    width_factor = 2.0 / max(0.5, width_in_meters)
  ```

- **Irreversible**: Once burned, edges remain impassable
- **Binary state**: Edges are either intact or destroyed (no partial damage)

### 5.3 Room Burning
- **Ignition**: Rooms burn when fire intensity reaches threshold
- **Irreversible**: Burned rooms remain destroyed
- **Occupant deaths**: All occupants in room die when it burns

---

## 6. Smoke Dynamics

### 6.1 Smoke Generation
- **Sources**:
  - Burned rooms generate smoke continuously
  - Adjacent to fire origin generates smoke

- **Generation rate**:
  ```
  smoke_per_tick = 0.5 m³/s × tick_duration × fire_intensity
  ```

### 6.2 Smoke Accumulation
- **Volume-based**: Smoke measured in cubic meters
- **Concentration**: smoke_amount / room_volume
- **No dispersion**: Smoke doesn't spread between rooms
- **Monotonic increase**: Smoke only accumulates, never decreases

### 6.3 Smoke Deaths
- **Threshold-based**: Death probability based on smoke concentration
- **Death rates** (per person per tick):
  - smoke_level < 0.3: 0% chance
  - 0.3 ≤ smoke_level < 0.5: 2% chance
  - 0.5 ≤ smoke_level < 0.7: 5% chance
  - smoke_level ≥ 0.7: 15% chance

- **Independent events**: Each occupant's survival is independent
- **No rescue from smoke**: Once dead, occupants cannot be saved

---

## 7. Physics and Environment

### 7.1 Spatial Model
- **2D representation**: No vertical movement within floors
- **Stairwells**: Represented as special vertices (inter-floor connections)
- **Euclidean distances**: Used for visual layout and fire spread only
- **Graph distances**: Used for actual pathfinding

### 7.2 Environmental Constraints
- **No external factors**: No weather, temperature variations, or structural collapse
- **Constant ceiling height**: 3.0 meters throughout
- **No visibility impairment**: Smoke doesn't affect pathfinding (only causes death)
- **Instant communication**: All firefighters can coordinate perfectly

---

## 8. Decision Making

### 8.1 Firefighter Control
- **Perfect execution**: Commands execute exactly as intended
- **No fatigue**: Firefighters never slow down or become incapacitated
- **No resource limits**: No oxygen tanks, equipment degradation, etc.
- **No positional constraints**: External model has full control over firefighter positioning
  - Can start any exit
  - Can be moved to any exit after rescue operations
  - Firefighters are simply agents that can be commanded to any valid vertex

### 8.2 Information Model
- **Partial observability**:
  - Graph structure and blocked paths is known
  - Occupant counts only revealed upon room visit
  - Fire spread is observable
  - Smoke levels are observable

- **No uncertainty**: Once discovered, information is perfect

---

## 9. Optimization Objectives

### 9.1 Primary Metrics
- **Rescued count**: Occupants successfully brought to exits
- **Vulnerable rescued count**: Occupants Inable to move themselves (usually children and elders) successfully brought to exits
- **Death count**: Occupants who died (fire or smoke)
- **Survival rate**: rescued / (rescued + dead)

### 9.2 Secondary Metrics
- **Time to complete**: Total simulation ticks until no occupants remain

---

## 10. Stochastic Elements

### 10.1 Randomness Sources
- **Occupant placement**: Based on room probabilities
- **Fire spread**: Probabilistic edge burning
- **Smoke deaths**: Probabilistic survival checks
- **Seed-based**: All randomness can be reproduced with same seed

### 10.2 Distribution Assumptions
- **Uniform random**: Used for basic probability checks
- **Independent events**: Fire spread and smoke deaths are independent
- **Memoryless**: Probabilities don't depend on history (except time)

---

## 11. Simplifying Assumptions

### 11.1 Human Behavior
- **Perfect compliance**: Instructed occupants always follow directions
- **No panic**: Occupants don't make irrational decisions
- **No injuries**: Occupants are either healthy, incapable, or dead

### 11.2 Firefighter Operations
- **Unlimited operation**: Firefighters can continue operating indefinitely
- **No procedural constraints**: Unlike real-world operations, there are no standard operating procedures that limit where firefighters can be moved

### 11.3 Fire Science
- **Simplified spread**: Fire spreads probabilistically, not based on fuel load or oxygen
- **No flashover**: Rooms burn individually, not catastrophically
- **No backdraft**: Opening doors doesn't affect fire behavior
- **Constant oxygen**: No asphyxiation model beyond smoke

### 11.4 Building Structure
- **Rigid structure**: No structural damage or collapse
- **Perfect barriers**: Walls are impermeable (smoke doesn't leak between rooms except through corridors)
- **Instant transitions**: Movement between spaces is instantaneous (no "in-between" states)

---

## 12. Validation Assumptions

### 12.1 Realism Benchmarks
- **Movement speed**: 2.0 m/s matches emergency evacuation research
- **Smoke death rates**: Calibrated to approximate real-world toxicity data
- **Fire spread times**: Order of magnitude realistic for building fires

### 12.2 Graph Validity
- **Connectedness**: All rooms must initially have path to at least one exit
- **Positive values**: Areas, capacities, and rates must be positive
- **Unique IDs**: All vertices and edges must have unique identifiers

---

## 13. Extensibility Assumptions

### 13.1 Future Enhancements
The model is designed to support (but currently doesn't implement):
- Multiple fire origins
- Variable ceiling heights affecting smoke stratification
- Sprinkler systems and fire suppression
- Window exits as alternative escape routes
- Multi-floor buildings with stairwell delays
- Variable movement speeds based on smoke density and/or firefighter capability

### 13.2 Compatibility
- **Graph format**: JSON configuration files
- **Unit system**: SI units (meters, seconds, square meters)
- **Coordinate system**: Cartesian (x, y) for visualization

---

## 14. Methodological Assumptions

### 14.1 Model Scope
- **Single building**: Simulation focuses on one building
- **Single event**: One fire per simulation run
- **Fixed building**: No dynamic reconfiguration during simulation
- **Complete information**: Building layout is known in advance

### 14.2 Analysis Approach
- **Monte Carlo**: Multiple runs with different seeds to understand statistical behavior
- **Comparative analysis**: Test different strategies on same building
- **Sensitivity analysis**: Vary parameters to understand impact
- **Validation**: Compare against simplified analytical models where possible