"""
Emergency Evacuation Simulator
A graph-based simulator for modeling building evacuations during emergencies.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import random
import math


@dataclass
class Vertex:
    """Represents a node in the building graph (room, hallway, exit, etc.)"""
    id: str
    type: str  # 'room', 'hallway', 'exit', 'window_exit'
    room_type: str  # 'office', 'daycare', 'warehouse', 'none'

    # Occupant tracking - two types
    capable_count: int = 0  # People who can walk (uninstructed)
    incapable_count: int = 0  # People who need to be carried (infants, elderly)
    instructed_capable_count: int = 0  # Capable people instructed and moving to exit

    capacity: int = 100
    priority: int = 1  # Higher = more important to check first
    sweep_time: int = 2  # Time in ticks to sweep this room
    ceiling_height: float = 3.0  # Ceiling height in meters (default 3m)
    smoke_amount: float = 0.0  # Smoke volume in cubic meters
    fire_intensity: float = 0.0  # Fire intensity level (0.0 to 1.0)
    is_burned: bool = False
    area: float = 100.0  # Area in square meters
    visual_position: dict = field(default_factory=dict)  # Optional position hint for visualizer

    # For instructed people pathfinding
    instructed_target_exit: Optional[str] = None  # Which exit instructed people are heading to

    @property
    def volume(self) -> float:
        """Calculate room volume (area × height)"""
        return self.area * self.ceiling_height

    @property
    def smoke_level(self) -> float:
        """Calculate smoke concentration as a fraction (0.0 to 1.0) for death calculations"""
        if self.volume == 0:
            return 0.0
        return min(1.0, self.smoke_amount / self.volume)

    def apply_smoke_deaths(self, rng: random.Random, tick_duration: float = 1.0) -> Dict[str, int]:
        """
        Apply smoke-related deaths based on current smoke level.
        Returns dict with deaths by type: {'capable': X, 'incapable': Y, 'instructed': Z}

        Args:
            rng: Random number generator
            tick_duration: How many seconds this tick represents (scales probability)
        """
        total_occupants = self.capable_count + self.incapable_count + self.instructed_capable_count
        if total_occupants == 0 or self.is_burned:
            return {'capable': 0, 'incapable': 0, 'instructed': 0}

        # Death probability increases with smoke level
        # Base rate: 0.02 per second at smoke_level=1.0
        death_probability_per_second = self.smoke_level ** 3 * 0.02
        death_probability = death_probability_per_second * tick_duration

        deaths = {'capable': 0, 'incapable': 0, 'instructed': 0}

        # Apply deaths to capable (uninstructed)
        for _ in range(self.capable_count):
            if rng.random() < death_probability:
                deaths['capable'] += 1
        self.capable_count -= deaths['capable']

        # Apply deaths to incapable
        for _ in range(self.incapable_count):
            if rng.random() < death_probability:
                deaths['incapable'] += 1
        self.incapable_count -= deaths['incapable']

        # Apply deaths to instructed capable
        for _ in range(self.instructed_capable_count):
            if rng.random() < death_probability:
                deaths['instructed'] += 1
        self.instructed_capable_count -= deaths['instructed']

        return deaths

    def burn_down(self) -> int:
        """
        Burn down this vertex, killing all occupants.
        Returns number of deaths.
        """
        deaths = self.capable_count + self.incapable_count + self.instructed_capable_count
        self.capable_count = 0
        self.incapable_count = 0
        self.instructed_capable_count = 0
        self.is_burned = True
        self.smoke_amount = self.volume  # Fill room completely with smoke
        return deaths


@dataclass
class Edge:
    """Represents a corridor/connection between vertices"""
    id: str
    vertex_a: str
    vertex_b: str
    max_flow: int = 5  # Max people that can traverse per tick
    base_burn_rate: float = 0.0001  # Base probability of burning per second
    width: float = 2.0  # Width in meters (default 2m corridor)
    exists: bool = True
    distance_to_fire: float = float('inf')  # Will be calculated

    # Note: All edges have unit length (1.0).
    # Physical length is defined by Simulation.UNIT_LENGTH (5m per unit)

    def get_burn_probability(self, tick: int, tick_duration: float = 1.0) -> float:
        """
        Calculate current burn probability based on time elapsed, distance to fire, and width.
        Probability increases over time and decreases with distance and width.
        Wider corridors are harder to burn down completely.

        Args:
            tick: Current tick number
            tick_duration: How many seconds per tick (scales probability)
        """
        if not self.exists or self.distance_to_fire == float('inf'):
            return 0.0

        # Calculate time in seconds
        time_seconds = tick * tick_duration

        # Fire spreads over time, inversely proportional to distance
        time_factor = 1 + time_seconds / 100.0  # Increases over time
        distance_factor = 1.0 / (1.0 + self.distance_to_fire / 10.0)

        # Width factor: wider corridors are harder to burn (inversely proportional)
        # Reference: 2m width = 1.0 factor, 4m width = 0.5 factor
        width_factor = 2.0 / max(0.5, self.width)

        # Scale by tick_duration: longer ticks = higher probability per tick
        return self.base_burn_rate * time_factor * distance_factor * width_factor * tick_duration


@dataclass
class Firefighter:
    """Represents a firefighter/responder"""
    id: str
    position: str  # Current vertex ID
    movement_points_per_tick: float = 50.0  # Distance budget in meters per tick (firefighter speed × TICK_DURATION)
    carrying_incapable: int = 0  # Number of incapable people being carried (0 to max_carry_capacity)
    max_carry_capacity: int = 3  # Maximum number of incapable people can carry (default: 3 for trained firefighters)
    visited_vertices: set = field(default_factory=set)  # For discovery tracking

    def mark_visited(self, vertex_id: str):
        """Mark a vertex as visited/discovered"""
        self.visited_vertices.add(vertex_id)

    def clear_visited(self):
        """Clear visited vertices (for re-exploration after dropping off)"""
        # Keep track of exits so they remain known
        exits_visited = {v for v in self.visited_vertices if v.startswith('exit')}
        self.visited_vertices = exits_visited


class Simulation:
    """Main simulation class for emergency evacuation"""

    # Time scaling: How many seconds does 1 tick represent?
    # With 1m unit length and 1s tick duration, firefighters move quickly
    # Firefighters take 2 actions per tick with TICK_DURATION=1
    TICK_DURATION = 1  # seconds per tick

    # Distance scaling: How many meters does 1 unit edge length represent?
    # Firefighters can traverse 2 unit edges per tick
    # This gives travel speed = 2 units / 1 second = 2.0 units/sec
    # With UNIT_LENGTH = 1m: speed = 2.0 m/s (realistic for trained firefighters)
    # Note: 2.0 m/s appropriate for firefighters in clear areas, fast walking pace
    UNIT_LENGTH = 1.0  # meters per unit edge length

    def __init__(
        self,
        config: Dict[str, Any],
        num_firefighters: int,
        fire_origin: str,
        seed: int = 42
    ):
        """
        Initialize simulation from configuration.

        Args:
            config: Dictionary with 'vertices', 'edges', 'occupancy_probabilities'
            num_firefighters: Number of firefighters to deploy
            fire_origin: Vertex ID where fire starts
            seed: Random seed for reproducibility
        """
        self.rng = random.Random(seed)
        self.tick = 0
        self.fire_origin = fire_origin
        self.rescued_count = 0
        self.dead_count = 0

        # Build graph
        self.vertices: Dict[str, Vertex] = {}
        self.edges: Dict[str, Edge] = {}
        self.adjacency: Dict[str, List[Tuple[str, str]]] = {}  # vertex_id -> [(neighbor_id, edge_id), ...]

        self._build_graph(config)
        self._initialize_occupants(config.get('occupancy_probabilities', {}))
        self._calculate_distances_to_fire()

        # Initialize fire at origin
        if self.fire_origin in self.vertices:
            self.vertices[self.fire_origin].fire_intensity = 0.3  # Start with initial fire

        # Initialize firefighters at exits
        self.firefighters: Dict[str, Firefighter] = {}
        self._initialize_firefighters(num_firefighters)

    def _build_graph(self, config: Dict[str, Any]):
        """Build graph structure from configuration"""
        # Create vertices
        for v_config in config.get('vertices', []):
            vertex = Vertex(
                id=v_config['id'],
                type=v_config.get('type', 'room'),
                room_type=v_config.get('room_type', 'none'),
                capacity=v_config.get('capacity', 100),
                priority=v_config.get('priority', 1),
                sweep_time=v_config.get('sweep_time', 2),
                area=v_config.get('area', 100.0),
                visual_position=v_config.get('visual_position', {})
            )
            self.vertices[vertex.id] = vertex
            self.adjacency[vertex.id] = []

        # Create edges (all unit length by definition)
        for e_config in config.get('edges', []):
            edge = Edge(
                id=e_config['id'],
                vertex_a=e_config['vertex_a'],
                vertex_b=e_config['vertex_b'],
                max_flow=e_config.get('max_flow', 5),
                base_burn_rate=e_config.get('base_burn_rate', 0.0001),
                width=e_config.get('width', 2.0)  # Default 2m width
            )
            self.edges[edge.id] = edge

            # Build adjacency list (undirected graph)
            self.adjacency[edge.vertex_a].append((edge.vertex_b, edge.id))
            self.adjacency[edge.vertex_b].append((edge.vertex_a, edge.id))

    def _initialize_occupants(self, occupancy_probs: Dict[str, Any]):
        """
        Randomly generate initial occupants based on configuration.

        Supports two formats:
        1. Probability format (legacy): {"capable": prob_per_sqm, "incapable": prob_per_sqm}
        2. Range format (new): {"capable": {"min": 2, "max": 5}, "incapable": {"min": 0, "max": 0}}

        occupancy_probs: {vertex_id: config}
        """
        for vertex_id, prob_config in occupancy_probs.items():
            if vertex_id not in self.vertices:
                continue

            vertex = self.vertices[vertex_id]

            # Handle old format (single float) - legacy compatibility
            if isinstance(prob_config, (int, float)):
                capable_prob = prob_config
                incapable_prob = 0.0
                # Generate using Gaussian distribution
                expected_capable = vertex.area * capable_prob
                if expected_capable > 0:
                    vertex.capable_count = max(0, int(self.rng.gauss(expected_capable, math.sqrt(expected_capable))))
                    vertex.capable_count = min(vertex.capable_count, vertex.capacity)
                continue

            if not isinstance(prob_config, dict):
                continue

            # Process capable occupants
            capable_config = prob_config.get('capable', 0.0)
            if isinstance(capable_config, dict) and 'min' in capable_config and 'max' in capable_config:
                # New range format: uniform random selection between min and max
                min_capable = capable_config['min']
                max_capable = capable_config['max']
                vertex.capable_count = self.rng.randint(min_capable, max_capable)
                vertex.capable_count = min(vertex.capable_count, vertex.capacity)
            elif isinstance(capable_config, (int, float)):
                # Old probability format: Gaussian distribution around expected value
                expected_capable = vertex.area * capable_config
                if expected_capable > 0:
                    vertex.capable_count = max(0, int(self.rng.gauss(expected_capable, math.sqrt(expected_capable))))
                    vertex.capable_count = min(vertex.capable_count, vertex.capacity)

            # Process incapable occupants
            incapable_config = prob_config.get('incapable', 0.0)
            remaining_capacity = vertex.capacity - vertex.capable_count

            if isinstance(incapable_config, dict) and 'min' in incapable_config and 'max' in incapable_config:
                # New range format: uniform random selection between min and max
                min_incapable = incapable_config['min']
                max_incapable = incapable_config['max']
                vertex.incapable_count = self.rng.randint(min_incapable, max_incapable)
                vertex.incapable_count = min(vertex.incapable_count, remaining_capacity)
            elif isinstance(incapable_config, (int, float)):
                # Old probability format: Gaussian distribution around expected value
                expected_incapable = vertex.area * incapable_config
                if expected_incapable > 0:
                    vertex.incapable_count = max(0, int(self.rng.gauss(expected_incapable, math.sqrt(expected_incapable))))
                    vertex.incapable_count = min(vertex.incapable_count, remaining_capacity)

    def _calculate_distances_to_fire(self):
        """Calculate shortest path distances from fire origin to all edges (BFS)"""
        if self.fire_origin not in self.vertices:
            return

        # BFS to find distances
        distances = {self.fire_origin: 0}
        queue = [self.fire_origin]

        while queue:
            current = queue.pop(0)
            current_dist = distances[current]

            for neighbor, edge_id in self.adjacency[current]:
                if neighbor not in distances:
                    distances[neighbor] = current_dist + 1
                    queue.append(neighbor)

        # Assign distances to edges (average of endpoints)
        for edge in self.edges.values():
            dist_a = distances.get(edge.vertex_a, float('inf'))
            dist_b = distances.get(edge.vertex_b, float('inf'))
            edge.distance_to_fire = (dist_a + dist_b) / 2.0

    def _get_spatial_distance(self, vertex_a_id: str, vertex_b_id: str) -> float:
        """
        Calculate Euclidean distance between two vertices using visual_position.
        Returns distance in unit lengths, or infinity if positions not available.

        Args:
            vertex_a_id: ID of first vertex
            vertex_b_id: ID of second vertex

        Returns:
            Euclidean distance in unit lengths, or float('inf') if no positions
        """
        vertex_a = self.vertices.get(vertex_a_id)
        vertex_b = self.vertices.get(vertex_b_id)

        if not vertex_a or not vertex_b:
            return float('inf')

        pos_a = vertex_a.visual_position
        pos_b = vertex_b.visual_position

        # If either vertex lacks position data, fall back to graph distance
        if not pos_a or not pos_b or 'x' not in pos_a or 'x' not in pos_b:
            return float('inf')

        # Euclidean distance in unit lengths
        dx = pos_a['x'] - pos_b['x']
        dy = pos_a['y'] - pos_b['y']
        return (dx * dx + dy * dy) ** 0.5

    def _initialize_firefighters(self, num_firefighters: int):
        """Initialize firefighters at exit locations"""
        exits = [v_id for v_id, v in self.vertices.items() if v.type in ['exit', 'window_exit']]

        if not exits:
            raise ValueError("No exits found in building layout")

        for i in range(num_firefighters):
            # Distribute firefighters across exits
            exit_position = exits[i % len(exits)]
            ff = Firefighter(
                id=f"ff_{i}",
                position=exit_position,
                movement_points_per_tick=50.0,  # 50 meters per tick (distance budget)
                carrying_incapable=0,
                max_carry_capacity=3  # Default: can carry up to 3 incapable people
            )
            ff.mark_visited(exit_position)
            self.firefighters[ff.id] = ff

    def update(self, actions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Execute one simulation tick.

        Args:
            actions: {firefighter_id: [action_dict, ...]}
                Actions:
                - move: {'type': 'move', 'target': vertex_id} - move to adjacent vertex (1 pt)
                - instruct: {'type': 'instruct'} - instruct all capable people at current vertex (1 pt)
                - pick_up_incapable: {'type': 'pick_up_incapable'} - pick up 1 incapable person (1 pt)
                - drop_off: {'type': 'drop_off'} - drop off carried person at current vertex (1 pt)

        Returns:
            Dictionary with action results and events
        """
        results = {
            'tick': self.tick,
            'action_results': {},
            'events': [],
            'rescued_this_tick': 0,
            'dead_this_tick': 0
        }

        # Execute firefighter actions
        for ff_id, ff_actions in actions.items():
            if ff_id not in self.firefighters:
                continue

            ff = self.firefighters[ff_id]
            ff_results = []
            movement_points_used = 0

            for action in ff_actions:
                if movement_points_used >= ff.movement_points_per_tick:
                    ff_results.append({'action': action, 'success': False, 'reason': 'no_movement_points'})
                    continue

                success, reason, points_used = self._execute_action(ff, action)
                movement_points_used += points_used
                ff_results.append({'action': action, 'success': success, 'reason': reason})

                # Check if people were rescued (drop_off action at exit)
                if action.get('type') == 'drop_off' and success:
                    rescued = action.get('rescued', 0)
                    if rescued > 0:
                        results['rescued_this_tick'] += rescued

            results['action_results'][ff_id] = ff_results

        # Move instructed capable people toward exits
        instructed_results = self._move_instructed_people()
        results['events'].extend(instructed_results['events'])
        results['rescued_this_tick'] += instructed_results['rescued']

        # Apply random events
        events = self._apply_random_events()
        results['events'].extend(events)
        results['dead_this_tick'] += sum(e.get('deaths', 0) for e in events)

        # Update fire intensity
        self._update_fire_intensity()

        # Update smoke levels
        self._update_smoke()

        # Apply smoke deaths
        for vertex in self.vertices.values():
            deaths_dict = vertex.apply_smoke_deaths(self.rng, self.TICK_DURATION)
            total_deaths = deaths_dict['capable'] + deaths_dict['incapable'] + deaths_dict['instructed']
            if total_deaths > 0:
                self.dead_count += total_deaths
                results['dead_this_tick'] += total_deaths
                results['events'].append({
                    'type': 'smoke_deaths',
                    'vertex': vertex.id,
                    'deaths': total_deaths,
                    'deaths_by_type': deaths_dict
                })

        self.tick += 1
        return results

    def _execute_action(self, ff: Firefighter, action: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Execute a single firefighter action.
        Returns (success, reason, movement_points_used)
        """
        action_type = action.get('type')

        if action_type == 'move':
            target_vertex = action.get('target')
            if target_vertex not in self.vertices:
                return False, 'invalid_target', 0

            # Check if adjacent
            neighbors = [n for n, _ in self.adjacency[ff.position]]
            if target_vertex not in neighbors:
                return False, 'not_adjacent', 0

            # Find the edge
            edge_id = None
            for neighbor, e_id in self.adjacency[ff.position]:
                if neighbor == target_vertex:
                    edge_id = e_id
                    break

            edge = self.edges[edge_id]
            if not edge.exists:
                return False, 'edge_blocked', 0

            # Calculate movement cost with node weights and carrying penalty
            # Cost = (node_weight_current + edge_weight + node_weight_target) * carrying_penalty
            # We traverse THROUGH current vertex and ENTER target vertex

            current_vertex = self.vertices[ff.position]
            target_vertex_obj = self.vertices[target_vertex]

            # Node weights: diagonal traversal = sqrt(2 * area)
            current_node_weight = (2.0 * current_vertex.area) ** 0.5
            target_node_weight = (2.0 * target_vertex_obj.area) ** 0.5
            edge_weight = 1.0  # Unit edge length

            # Apply carrying penalty (halve speed = double cost)
            if ff.carrying_incapable > 0:
                carrying_multiplier = 2.0
            else:
                carrying_multiplier = 1.0

            # Total movement cost: traverse current + edge + enter target
            movement_cost = (current_node_weight + edge_weight + target_node_weight) * carrying_multiplier

            # Move
            ff.position = target_vertex
            ff.mark_visited(target_vertex)
            return True, 'moved', movement_cost

        elif action_type == 'instruct':
            # Instruct ALL capable people at current vertex to evacuate
            current_vertex = self.vertices[ff.position]

            if current_vertex.capable_count == 0:
                return False, 'no_capable_people', 1

            # Find nearest exit using BFS
            target_exit = self._find_nearest_exit(ff.position)
            if not target_exit:
                return False, 'no_exit_found', 1

            # Convert capable to instructed
            instructed_count = current_vertex.capable_count
            current_vertex.capable_count = 0
            current_vertex.instructed_capable_count += instructed_count
            current_vertex.instructed_target_exit = target_exit

            action['instructed_count'] = instructed_count
            return True, f'instructed_{instructed_count}', 1

        elif action_type == 'pick_up_incapable':
            # Pick up incapable person(s)
            current_vertex = self.vertices[ff.position]

            # Get count parameter (default: 1)
            count = action.get('count', 1)

            if ff.carrying_incapable >= ff.max_carry_capacity:
                return False, 'already_carrying', 1

            if current_vertex.incapable_count == 0:
                return False, 'no_incapable_people', 1

            # Pick up as many as possible (limited by capacity, availability, and requested count)
            can_carry_more = ff.max_carry_capacity - ff.carrying_incapable
            available = current_vertex.incapable_count
            actual_pickup = min(count, can_carry_more, available)

            if actual_pickup <= 0:
                return False, 'cannot_pickup', 1

            current_vertex.incapable_count -= actual_pickup
            ff.carrying_incapable += actual_pickup
            return True, f'picked_up_{actual_pickup}_incapable', 1

        elif action_type == 'drop_off':
            # Drop off carried incapable person(s)
            if ff.carrying_incapable == 0:
                return False, 'not_carrying', 1

            current_vertex = self.vertices[ff.position]

            # Get count parameter (default: 'all')
            count = action.get('count', 'all')
            if count == 'all':
                drop_count = ff.carrying_incapable
            else:
                drop_count = min(count, ff.carrying_incapable)

            if drop_count <= 0:
                return False, 'nothing_to_drop', 1

            # Check if at exit
            if current_vertex.type in ['exit', 'window_exit']:
                self.rescued_count += drop_count
                action['rescued'] = drop_count
                ff.carrying_incapable -= drop_count
                return True, f'dropped_off_{drop_count}_rescued', 1
            else:
                # Drop off at non-exit (e.g., safer location)
                current_vertex.incapable_count += drop_count
                ff.carrying_incapable -= drop_count
                return True, f'dropped_off_{drop_count}_room', 1

        else:
            return False, 'unknown_action', 0

    def _move_instructed_people(self) -> Dict[str, Any]:
        """
        Move all instructed capable people one step toward their target exits.
        Returns dict with events and rescued count.
        """
        from collections import deque

        results = {
            'events': [],
            'rescued': 0
        }

        # IMPORTANT: Snapshot vertices with instructed people BEFORE moving
        # This prevents people from moving multiple times in one tick
        vertices_to_process = []
        for vertex_id, vertex in self.vertices.items():
            if vertex.instructed_capable_count > 0:
                vertices_to_process.append({
                    'vertex_id': vertex_id,
                    'count': vertex.instructed_capable_count,
                    'target_exit': vertex.instructed_target_exit
                })

        # Track movements to respect max_flow constraints
        edge_flow_used = {}  # edge_id -> people moved

        for item in vertices_to_process:
            vertex_id = item['vertex_id']
            vertex = self.vertices[vertex_id]
            target_exit = item['target_exit']
            # Use the snapshotted count, not the current count
            people_count = item['count']

            if not target_exit:
                continue

            # Check if already at exit
            if vertex.type in ['exit', 'window_exit']:
                # Rescue everyone (use snapshotted count)
                self.rescued_count += people_count
                results['rescued'] += people_count
                vertex.instructed_capable_count -= people_count
                continue

            # Find path to exit using BFS
            path = self._bfs_path_to_exit(vertex_id, target_exit)

            if not path or len(path) < 2:
                # Trapped - no path available, stay in place
                results['events'].append({
                    'type': 'instructed_trapped',
                    'vertex': vertex_id,
                    'count': people_count
                })
                continue

            # Move toward exit (next vertex in path)
            next_vertex_id = path[1]

            # Find the edge
            edge_id = None
            for neighbor, e_id in self.adjacency[vertex_id]:
                if neighbor == next_vertex_id:
                    edge_id = e_id
                    break

            if not edge_id:
                continue

            edge = self.edges[edge_id]

            # Calculate how many can move (respect max_flow)
            flow_already_used = edge_flow_used.get(edge_id, 0)
            available_flow = edge.max_flow - flow_already_used
            people_to_move = min(people_count, available_flow)

            if people_to_move > 0:
                # Move people
                vertex.instructed_capable_count -= people_to_move
                next_vertex = self.vertices[next_vertex_id]
                next_vertex.instructed_capable_count += people_to_move
                next_vertex.instructed_target_exit = target_exit

                edge_flow_used[edge_id] = flow_already_used + people_to_move

                results['events'].append({
                    'type': 'instructed_moved',
                    'from': vertex_id,
                    'to': next_vertex_id,
                    'count': people_to_move
                })

        return results

    def _bfs_path_to_exit(self, start: str, target_exit: str) -> Optional[List[str]]:
        """Find path from start to target_exit using BFS (only through existing edges)"""
        from collections import deque

        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == target_exit:
                return path

            for neighbor, edge_id in self.adjacency[current]:
                edge = self.edges[edge_id]
                if edge.exists and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        return None  # No path exists

    def _find_nearest_exit(self, start_vertex: str) -> Optional[str]:
        """Find nearest exit from given vertex using BFS"""
        from collections import deque

        queue = deque([start_vertex])
        visited = {start_vertex}

        while queue:
            current = queue.popleft()
            vertex = self.vertices[current]

            # Found an exit
            if vertex.type in ['exit', 'window_exit']:
                return current

            # Explore neighbors (only through existing edges)
            for neighbor, edge_id in self.adjacency[current]:
                edge = self.edges[edge_id]
                if edge.exists and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return None  # No exit found

    def _apply_random_events(self) -> List[Dict[str, Any]]:
        """Apply random fire spread events"""
        events = []

        # Edge deletion (corridor blocking)
        for edge in self.edges.values():
            if edge.exists:
                burn_prob = edge.get_burn_probability(self.tick, self.TICK_DURATION)
                if self.rng.random() < burn_prob:
                    edge.exists = False
                    events.append({
                        'type': 'edge_deleted',
                        'edge_id': edge.id,
                        'vertices': (edge.vertex_a, edge.vertex_b)
                    })

        # Room burndown (smaller probability)
        for vertex in self.vertices.values():
            if not vertex.is_burned and vertex.type == 'room':
                # Probability based on proximity to fire and room size
                if self.fire_origin in self.vertices:
                    # Base probability
                    base_prob_per_second = 0.0005  # 0.05% per second base rate

                    # Area factor: larger rooms are harder to burn down completely
                    # Reference: 15 sqm = 1.0 factor, 30 sqm = 0.5 factor
                    area_factor = 15.0 / max(5.0, vertex.area)

                    # Scale by tick duration
                    burn_prob = base_prob_per_second * area_factor * self.TICK_DURATION

                    if self.rng.random() < burn_prob:
                        deaths = vertex.burn_down()
                        self.dead_count += deaths
                        events.append({
                            'type': 'room_burned',
                            'vertex_id': vertex.id,
                            'deaths': deaths
                        })

        return events

    def _update_fire_intensity(self):
        """
        Update fire intensity levels for all vertices.
        Fire intensity grows over time and spreads to adjacent rooms.
        """
        new_intensities = {}

        for vertex_id, vertex in self.vertices.items():
            if vertex.is_burned:
                # Burned rooms maintain high fire intensity
                new_intensities[vertex_id] = 0.9
                continue

            current_intensity = vertex.fire_intensity

            # Fire grows over time in burning rooms
            if current_intensity > 0:
                # Two-component growth model based on NIST/UL research:
                # 1. Intrinsic growth: slow cold-start (3-5 min to flashover for isolated room)
                # 2. Preheating acceleration: adjacent burning rooms speed up growth

                # Intrinsic growth rate (cold start)
                # At 0.001 per tick: 0.3 → 1.0 takes ~70 ticks = 700 sec = 11.7 minutes
                # With spread/preheating feedback, actual time will be 3-4 min (realistic range)
                intrinsic_growth = 0.001 * self.TICK_DURATION

                # Preheating bonus from adjacent burning rooms
                # Research: "smoke spread accelerates preheating and combustion speed"
                preheating_bonus = 0.0
                for neighbor_id, edge_id in self.adjacency[vertex_id]:
                    neighbor = self.vertices[neighbor_id]
                    edge = self.edges[edge_id]

                    if neighbor.fire_intensity > 0 and edge.exists:
                        # Each burning neighbor contributes to preheating via:
                        # - Radiant heat flux through corridor
                        # - Hot smoke accumulation
                        # - Convective heat transfer

                        # Width factor: wider corridors = more heat/smoke transfer
                        width_factor = edge.width / 2.0  # Normalized to 2m reference

                        # Spatial distance factor: radiant heat decays with distance
                        # Even if connected through hallway, farther rooms contribute less
                        spatial_distance = self._get_spatial_distance(vertex_id, neighbor_id)
                        if spatial_distance != float('inf'):
                            # Inverse square law approximation for radiant heat
                            # At 1 unit: 1.0× effect, at 2 units: 0.5× effect, at 3 units: 0.33× effect
                            distance_factor = 1.0 / max(1.0, spatial_distance)
                        else:
                            # No position data: use graph connectivity only
                            distance_factor = 1.0

                        preheating_bonus += neighbor.fire_intensity * 0.005 * width_factor * distance_factor

                # Total growth = intrinsic + preheating acceleration
                # Example: room with 2 adjacent burning neighbors (1 unit apart) at 100% intensity through 2m corridors:
                # growth = 0.015 + 2*(1.0*0.005*1.0*1.0) = 0.015 + 0.010 = 0.025 per tick
                # Room far from fire (2 units away) gets: 0.015 + (1.0*0.005*1.0*0.5) = 0.0175 per tick
                # Spatial distance realistically reduces preheating effect
                growth_rate = intrinsic_growth + (preheating_bonus * self.TICK_DURATION)
                current_intensity = min(1.0, current_intensity + growth_rate)

            # Fire spreads from adjacent burning rooms (ignition mechanism)
            # This mechanism is for IGNITION only, not continuous growth
            for neighbor_id, edge_id in self.adjacency[vertex_id]:
                neighbor = self.vertices[neighbor_id]
                edge = self.edges[edge_id]

                # Fire spreads if neighbor is burning and corridor exists
                if neighbor.fire_intensity > 0 and edge.exists:
                    # Fire spread rate depends on corridor width
                    # Narrower corridors = faster spread (easier to fully ignite)
                    # All edges have unit length, physical distance = UNIT_LENGTH
                    width_factor = 2.0 / max(0.5, edge.width)  # Narrower = more spread (2m reference)

                    # Ignition taper: spread is strong for unignited rooms, weakens as room ignites
                    # At 0% fire: 1.0× spread (full ignition effect)
                    # At 30% fire: 0.7× spread (partial)
                    # At 50%+ fire: minimal spread (growth via preheating instead)
                    # This prevents continuous feedback loop while preserving 30-sec ignition
                    ignition_taper = max(0.0, 1.0 - current_intensity)

                    spread_amount = neighbor.fire_intensity * 0.01 * width_factor * ignition_taper * self.TICK_DURATION
                    current_intensity = min(1.0, current_intensity + spread_amount)

            new_intensities[vertex_id] = current_intensity

        # Apply new intensities
        for vertex_id, intensity in new_intensities.items():
            self.vertices[vertex_id].fire_intensity = intensity

    def _update_smoke(self):
        """
        Update smoke amounts using volume-based diffusion model.
        Smoke is now in cubic meters, spreads based on corridor width.
        """
        new_smoke_amounts = {}

        for vertex_id, vertex in self.vertices.items():
            if vertex.is_burned:
                # Burned rooms are completely filled with smoke
                new_smoke_amounts[vertex_id] = vertex.volume
            else:
                # Start with 85% of current smoke (15% dissipates)
                smoke_amount = vertex.smoke_amount * 0.85

                # Smoke diffuses from neighbors based on corridor width
                for neighbor_id, edge_id in self.adjacency[vertex_id]:
                    neighbor = self.vertices[neighbor_id]
                    edge = self.edges[edge_id]

                    # Calculate concentration difference (drives diffusion)
                    my_concentration = vertex.smoke_amount / vertex.volume if vertex.volume > 0 else 0
                    neighbor_concentration = neighbor.smoke_amount / neighbor.volume if neighbor.volume > 0 else 0
                    concentration_diff = neighbor_concentration - my_concentration

                    if concentration_diff > 0:
                        # Smoke flows from high to low concentration
                        # Diffusion rate scales with corridor width (wider = more flow)
                        # All edges have unit length, physical distance = UNIT_LENGTH
                        # Base diffusion coefficient: 0.45 (balanced for moderate spread)
                        width_factor = edge.width / 2.0  # Normalized to 2m reference
                        diffusion_coefficient = 0.45 * width_factor

                        # Amount of smoke that diffuses through this corridor
                        smoke_flow = concentration_diff * diffusion_coefficient * min(vertex.volume, neighbor.volume)
                        smoke_amount += smoke_flow

                # Burning rooms generate smoke based on fire intensity
                if vertex.fire_intensity > 0:
                    # Generate smoke in cubic meters per second, scaled by fire intensity
                    # Reduced rate for more realistic smoke buildup timing
                    # Base rate: 2.5 m³/second at full intensity
                    # Low intensity fire (0.3) → 0.75 m³/s
                    # Full intensity fire (1.0) → 2.5 m³/s
                    base_smoke_rate = 2.5  # m³/second at full intensity (reduced from 5.0)
                    smoke_generation_rate = base_smoke_rate * vertex.fire_intensity
                    smoke_generated = smoke_generation_rate * self.TICK_DURATION
                    smoke_amount += smoke_generated

                # Cap smoke at room volume
                new_smoke_amounts[vertex_id] = min(vertex.volume, smoke_amount)

        # Update all vertices
        for vertex_id, smoke_amount in new_smoke_amounts.items():
            self.vertices[vertex_id].smoke_amount = smoke_amount

    def read(self) -> Dict[str, Any]:
        """
        Return observable state for external model.
        Model knows: building layout, current positions, discovered occupants, events
        """
        # Graph structure (always known from blueprints)
        graph_structure = {
            'vertices': {
                v_id: {
                    'type': v.type,
                    'room_type': v.room_type,
                    'capacity': v.capacity,
                    'priority': v.priority,
                    'sweep_time': v.sweep_time,
                    'is_burned': v.is_burned,
                    'area': v.area
                }
                for v_id, v in self.vertices.items()
            },
            'edges': {
                e_id: {
                    'vertex_a': e.vertex_a,
                    'vertex_b': e.vertex_b,
                    'max_flow': e.max_flow,
                    'exists': e.exists
                }
                for e_id, e in self.edges.items()
            }
        }

        # Firefighter states
        firefighter_states = {}
        discovered_occupants = {}

        for ff_id, ff in self.firefighters.items():
            firefighter_states[ff_id] = {
                'position': ff.position,
                'carrying_incapable': ff.carrying_incapable,
                'max_carry_capacity': ff.max_carry_capacity,
                'visited_vertices': list(ff.visited_vertices)
            }

            # Discovered occupants (for all visited vertices)
            for v_id in ff.visited_vertices:
                if v_id in self.vertices:
                    vertex = self.vertices[v_id]
                    # Include all visited vertices (rooms, hallways, etc) except exits
                    if vertex.type not in ['exit', 'window_exit']:
                        discovered_occupants[v_id] = {
                            'capable': vertex.capable_count,
                            'incapable': vertex.incapable_count,
                            'instructed': vertex.instructed_capable_count
                        }

        return {
            'tick': self.tick,
            'graph': graph_structure,
            'firefighters': firefighter_states,
            'discovered_occupants': discovered_occupants,
            'fire_origin': self.fire_origin
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return performance statistics"""
        # Count all occupants (capable, incapable, instructed) + those being carried
        total_occupants = sum(
            v.capable_count + v.incapable_count + v.instructed_capable_count
            for v in self.vertices.values()
        )
        total_carrying = sum(ff.carrying_incapable for ff in self.firefighters.values())

        return {
            'tick': self.tick,
            'rescued': self.rescued_count,
            'dead': self.dead_count,
            'remaining': total_occupants + total_carrying,
            'total_initial': self.rescued_count + self.dead_count + total_occupants + total_carrying,
            'time_minutes': (self.tick * self.TICK_DURATION) / 60.0  # Convert to minutes
        }
