# Model Assumptions

## Overview

This document comprehensively lists all assumptions made in the HiMCM 2025 evacuation simulator. These assumptions simplify the real-world problem while maintaining realistic behavior for emergency evacuation scenarios.

---

## 1. Occupant Behavior

### 1.1 Mobility States

**Binary classification**:
- **Capable**: Can self-evacuate when instructed (elderly, adults, older children)
- **Incapable**: Require physical assistance (infants, wheelchair users, unconscious)

**Assumptions**:
- No intermediate states (injured but mobile, disoriented, etc.)
- State doesn't change during simulation (capable don't become incapable from smoke)
- Perfect binary classification (no uncertainty about capability)

### 1.2 Health States

**Binary health model**:
- **Healthy**: Functional and able to perform role (move or be carried)
- **Dead**: Removed from simulation

**No modeled states**:
- Injuries or impairment (smoke inhalation damage, burns, trauma)
- Panic or psychological effects
- Fatigue or exhaustion

### 1.3 Compliance and Decision-Making

**Perfect compliance**:
- All occupants follow instructions immediately
- No hesitation, denial, or refusal to evacuate
- No attempts to rescue others or retrieve belongings
- No re-entry to building

**Perfect knowledge post-instruction**:
- Instructed occupants know optimal path to assigned exit
- No confusion about directions
- No getting lost or taking wrong turns

**Autonomous movement**:
- Instructed capable people move automatically toward exit
- No need for continuous guidance
- Movement continues even without firefighter presence

### 1.4 Group Behavior

**No social dynamics**:
- No family groups (parents waiting for children)
- No helping behaviors between occupants
- No crowding or jamming at bottlenecks (max_flow handled algorithmically)
- No trampling or pushing

---

## 2. Responder Capabilities

### 2.1 Movement and Speed

**Constant movement speed**:
- Firefighters move at 2.0 m/s in clear areas (2 edges per tick, 1m per edge, 1s per tick)
- Speed **does not decrease** when:
  - Carrying multiple people (up to k=3)
  - Moving through smoke
  - Fatigued or injured
  - Wearing protective equipment

**Perfect pathfinding**:
- Firefighters know all shortest paths
- Can compute paths even through unvisited areas (blueprints)
- **Know routes even when edges burn** (assumption: radio contact, maps)

### 2.2 Physical Capacity

**Configurable carry capacity**:
- Default k=3 incapable people simultaneously
- No weight or size limitations (can carry 3 adults or 3 children equally)
- No consideration of:
  - Firefighter's physical strength or size
  - Rescued person's weight or mobility aids
  - Equipment burden

**Unlimited endurance**:
- No fatigue from carrying multiple people
- Can operate indefinitely (no oxygen tank limits)
- No need for rest or medical attention

### 2.3 Information and Communication

**Perfect information after discovery**:
- Once room is visited, firefighter knows exact occupant counts forever
- Information shared instantly among all firefighters
- No need to recheck rooms

**Instant action execution**:
- Pickup: Instantaneous (0 time cost, but uses 1 action point)
- Dropoff: Instantaneous
- Instruction: Instantaneous (all capable people at location instructed at once)

**No communication delays**:
- Model can coordinate all firefighters instantly
- No radio failures or miscommunication
- Perfect command and control

---

## 3. Building Graph Structure

### 3.1 Graph Representation

**Accurate layout**:
- Graph represents building blueprint exactly
- Edge lengths in meters (1m per unit edge)
- Visual positions used for spatial calculations (fire spread)

**Node types**:
- Rooms: Occupy space, have area and capacity
- Hallways/Intersections: Connective passages
- Exits: Designated safe evacuation points
- Window exits: Alternative evacuation routes (treated as regular exits)

**Edge properties**:
- Width: Corridor width in meters (affects smoke volume)
- Max flow: People per tick (default 5, prevents bottlenecks)
- Exists: Boolean (burned edges become non-existent)

### 3.2 Static Properties

**No structural changes** (except edge burning):
- Walls don't collapse
- Ceilings don't fall
- Doors don't jam or lock
- No debris blocking paths (except burned edges)

**Barriers and obstacles**:
- **Intra-room barriers ignored**: Movement within room is instantaneous
- **Inter-room barriers respected**: Must follow graph edges
- No partial blockages (edge either exists or doesn't)

### 3.3 Occupancy

**Probabilistic initial placement**:
- Occupants placed according to configured ranges (min-max uniform distribution)
- Placement is random but deterministic (seed-based)
- **Counts not in blueprint**: Must be discovered by firefighters

**Static during simulation**:
- Occupants don't move between rooms (except when instructed or carried)
- No spontaneous evacuation
- No hiding or seeking shelter in different rooms

---

## 4. Fire Dynamics

### 4.1 Spreading Model

**Spherical radial spread**:
- Fire spreads outward from origin at constant rate in all directions
- Distance measured using visual_position (Euclidean)
- **Ignores barriers**: Fire spreads through walls as if building is transparent

**Probabilistic edge burning**:
- Burn probability based on distance to fire origin
- Closer edges burn first (exponential decay model)
- Random events each tick (seed-based determinism)

**No airflow or oxygen effects**:
- Spread rate unaffected by ventilation
- No oxygen depletion slowing fire
- No wind or HVAC spreading fire faster

### 4.2 Room Burndown

**Complete room destruction**:
- Rooms burn when fire_intensity reaches 1.0
- `is_burned = True` (permanent)
- All remaining occupants die instantly

**No partial damage**:
- Room either intact or completely burned
- No smoke damage to structure
- No weakening before collapse

### 4.3 Edge Burning

**Binary edge state**:
- Edge either exists or is destroyed
- Once burned, edge is impassable permanently
- **No repairs or alternative routes created**

---

## 5. Smoke Behavior

### 5.1 Accumulation

**Volume-based model**:
- Smoke accumulates in rooms based on volume (area × ceiling_height)
- Larger rooms dilute smoke (lower smoke_level for same smoke_amount)
- Smoke level: 0.0 (clear) to 1.0 (dense)

**Diffusion**:
- Smoke spreads between connected rooms
- Simplified diffusion model (not full fluid dynamics)
- No consideration of:
  - Temperature (hot smoke rising)
  - Pressure differentials
  - Ventilation systems

### 5.2 Lethality

**Threshold-based deaths**:
- Occupants die when smoke_level > 0.8 at their location
- **Instant death** (no gradual impairment)
- Death check happens each tick

**No smoke effects on movement**:
- Firefighters not slowed by smoke
- Visibility not reduced
- No coughing or breathing difficulties modeled

### 5.3 Persistence

**No smoke clearing**:
- Smoke persists until simulation end
- No ventilation or dissipation
- No firefighter smoke clearing actions

---

## 6. Optimization Algorithm (Phase 2)

### 6.1 Phase Transition

**Trigger conditions**:
- All rooms visited at least once by any firefighter
- All capable occupants instructed to evacuate

**Complete information assumption**:
- Optimization assumes perfect knowledge of all incapable locations
- No uncertainty about occupant counts or locations
- Building layout fully known (from blueprints)

### 6.2 Static Snapshot

**One-time optimization**:
- Algorithm runs once at phase transition
- Uses occupant snapshot at that moment
- **No replanning** if situation changes:
  - If edges burn during Phase 2 execution
  - If new occupants discovered (shouldn't happen - all rooms visited)
  - If occupants die from smoke

**Rationale**:
- Incapable people can't move on their own
- Optimization window assumed short relative to fire spread
- Computational cost of continuous replanning too high

### 6.3 Item Execution

**Precomputed paths**:
- Full paths computed during optimization
- Firefighters follow paths exactly
- No dynamic obstacle avoidance

**Sequential item execution**:
- Firefighters complete one item before starting next
- No interrupting plans mid-execution
- No swapping tasks between firefighters

### 6.4 Linear Constraints

**Strict resource limits**:
- Cannot rescue more people than exist in room
- Items assigned exclusively (no double-counting)
- Capacity constraints enforced absolutely

**Greedy vs LP**:
- Greedy: Fast, near-optimal (5-15% gap typically)
- LP: Optimal (continuous relaxation), slower
- **Greedy used by default** for real-time performance

---

## 7. Simulation Mechanics

### 7.1 Time Model

**Discrete time steps**:
- Tick duration: 1 second (TICK_DURATION constant)
- All events within tick happen simultaneously
- No sub-tick resolution

**Action budget**:
- Each firefighter: 2 actions per tick
- Each action costs exactly 1 point
- Failed actions may still cost points (instruct, pickup, dropoff)

### 7.2 State Visibility

**No intra-tick observation**:
- Model sees state at tick start
- All actions planned before tick execution
- Results visible only at next tick

**Perfect state snapshot**:
- `sim.read()` provides complete observable state
- No delays in information propagation
- All firefighters share knowledge

### 7.3 Determinism

**Seed-based randomness**:
- Given same seed, simulation is fully reproducible
- Random events: edge burning, room burndown, occupant placement
- **No non-deterministic behavior**

---

## 8. Limitations and Simplifications

### 8.1 Not Modeled

**Human factors**:
- Panic, fear, denial
- Physical disabilities beyond binary capable/incapable
- Psychological trauma
- Communication difficulties (language, hearing)

**Environmental hazards**:
- Extreme heat (burns)
- Toxic gases (CO, cyanide)
- Visibility reduction
- Structural collapse (except edge burning)

**Resource constraints**:
- Equipment limitations (oxygen tanks, stretchers)
- Medical supplies
- Communication equipment batteries
- Personnel fatigue

**Organizational factors**:
- Command structure
- Incident command decisions
- Resource allocation to other tasks (firefighting)
- Multiple simultaneous incidents

### 8.2 Idealized Assumptions

**Perfect knowledge**:
- Building layout known exactly
- Occupant locations known after discovery
- No fog of war after initial exploration

**Perfect execution**:
- No mistakes or errors
- No equipment failures
- No accidents or setbacks

**Perfect coordination**:
- Instant communication
- No conflicts or confusion
- Optimal task allocation

---

## 9. Validation Against Reality

### 9.1 Realistic Aspects

✓ **Fire spread**: Probabilistic, distance-based
✓ **Smoke accumulation**: Volume-based, lethal at high levels
✓ **Movement speed**: 2.0 m/s reasonable for trained firefighters
✓ **Carry capacity**: k=3 realistic for professional rescuers
✓ **Graph structure**: Accurate representation of buildings
✓ **Prioritization**: High-value rooms (daycares) vs low-value (warehouses)

### 9.2 Limitations Acknowledged

⚠ **No panic**: Real evacuations involve chaos, hesitation, poor decisions
⚠ **Perfect compliance**: Real people don't always follow instructions
⚠ **Binary health**: Real injuries create spectrum of mobility impairment
⚠ **No structural collapse**: Real fires cause building failures
⚠ **Simplified smoke**: Real smoke is complex fluid with temperature, toxicity, visibility effects

### 9.3 Model Scope

This model is designed for:
- **Comparative analysis**: Evaluating different evacuation strategies
- **Optimization research**: Testing rescue coordination algorithms
- **Educational purposes**: Understanding evacuation dynamics
- **What-if scenarios**: Exploring building design impacts

This model is **NOT** designed for:
- Precise prediction of real emergency outcomes
- Safety certification or code compliance
- Training simulations for actual firefighters
- Forensic reconstruction of real incidents

---

## 10. Assumption Justification

### 10.1 Why These Assumptions?

**Computational tractability**:
- Simplified physics enables real-time simulation
- Discrete time allows step-by-step analysis
- Perfect information enables optimization algorithms

**Focus on core problem**:
- Evacuation routing and coordination
- Resource allocation (firefighters to rooms)
- Time-critical decision-making

**Reproducibility**:
- Deterministic behavior enables scientific comparison
- Seed-based randomness provides variability with control

### 10.2 Sensitivity Analysis (Recommended)

Users should test sensitivity to key assumptions:

**Vary k (carry capacity)**: 1, 2, 3
**Vary movement speed**: 1.0, 1.5, 2.0 m/s
**Vary fire spread rate**: Adjust probabilistic parameters
**Vary occupancy**: Different min-max ranges per room
**Vary building layout**: Different graph topologies

---

## 11. Future Model Enhancements

### Proposed Relaxations

1. **Dynamic replanning**: Reoptimize when edges burn during Phase 2
2. **Probabilistic fire prediction**: Account for expected burn times in optimization
3. **Partial injuries**: Occupants with reduced but non-zero mobility
4. **Communication delays**: Lag between discovery and sharing information
5. **Equipment constraints**: Limited oxygen, stretchers, etc.
6. **Multi-objective optimization**: Balance time vs risk vs firefighter safety

### Implementation Priority

**High**: Dynamic replanning (critical for realism)
**Medium**: Fire prediction, communication delays
**Low**: Partial injuries, equipment (complex, marginal impact)

---

## References

- HiMCM 2025 Problem Statement: Emergency Evacuation Optimization
- NFPA 101: Life Safety Code
- SFPE Handbook of Fire Protection Engineering
- Emergency Evacuation Literature (Kuligowski, Gwynne, etc.)
