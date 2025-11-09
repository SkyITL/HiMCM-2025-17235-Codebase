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
    occupant_count: int = 0
    capacity: int = 100
    priority: int = 1  # Higher = more important to check first
    sweep_time: int = 2  # Time in ticks to sweep this room
    smoke_level: float = 0.0  # 0.0 to 1.0
    is_burned: bool = False
    area: float = 100.0  # For occupancy probability calculations
    visual_position: dict = field(default_factory=dict)  # Optional position hint for visualizer

    def apply_smoke_deaths(self, rng: random.Random) -> int:
        """
        Apply smoke-related deaths based on current smoke level.
        Returns number of deaths this tick.
        """
        if self.occupant_count == 0 or self.is_burned:
            return 0

        # Death probability increases with smoke level - reduced from original
        # At smoke_level=0.5, ~0.2% death rate per tick
        # At smoke_level=1.0, ~2% death rate per tick
        death_probability = self.smoke_level ** 3 * 0.02  # Much more forgiving

        deaths = 0
        for _ in range(self.occupant_count):
            if rng.random() < death_probability:
                deaths += 1

        self.occupant_count -= deaths
        return deaths

    def burn_down(self) -> int:
        """
        Burn down this vertex, killing all occupants.
        Returns number of deaths.
        """
        deaths = self.occupant_count
        self.occupant_count = 0
        self.is_burned = True
        self.smoke_level = 1.0
        return deaths


@dataclass
class Edge:
    """Represents a corridor/connection between vertices"""
    id: str
    vertex_a: str
    vertex_b: str
    max_flow: int = 5  # Max people that can traverse per tick
    base_burn_rate: float = 0.0001  # Base probability of burning per tick
    exists: bool = True
    distance_to_fire: float = float('inf')  # Will be calculated

    def get_burn_probability(self, tick: int) -> float:
        """
        Calculate current burn probability based on time elapsed and distance to fire.
        Probability increases over time and decreases with distance.
        """
        if not self.exists or self.distance_to_fire == float('inf'):
            return 0.0

        # Fire spreads over time, inversely proportional to distance
        time_factor = 1 + tick / 100.0  # Increases over time
        distance_factor = 1.0 / (1.0 + self.distance_to_fire / 10.0)

        return self.base_burn_rate * time_factor * distance_factor


@dataclass
class Firefighter:
    """Represents a firefighter/responder"""
    id: str
    position: str  # Current vertex ID
    movement_points_per_tick: int = 1  # 1 action per tick (1 tick = 1 second)
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

        # Create edges
        for e_config in config.get('edges', []):
            edge = Edge(
                id=e_config['id'],
                vertex_a=e_config['vertex_a'],
                vertex_b=e_config['vertex_b'],
                max_flow=e_config.get('max_flow', 5),
                base_burn_rate=e_config.get('base_burn_rate', 0.0001)
            )
            self.edges[edge.id] = edge

            # Build adjacency list (undirected graph)
            self.adjacency[edge.vertex_a].append((edge.vertex_b, edge.id))
            self.adjacency[edge.vertex_b].append((edge.vertex_a, edge.id))

    def _initialize_occupants(self, occupancy_probs: Dict[str, float]):
        """
        Randomly generate initial occupants based on probabilities.
        occupancy_probs: {vertex_id: probability_per_sqm}
        """
        for vertex_id, prob_per_sqm in occupancy_probs.items():
            if vertex_id in self.vertices:
                vertex = self.vertices[vertex_id]
                # Generate occupants based on area and probability
                expected_occupants = vertex.area * prob_per_sqm
                # Use Poisson-like distribution
                vertex.occupant_count = max(0, int(self.rng.gauss(expected_occupants, math.sqrt(expected_occupants))))
                vertex.occupant_count = min(vertex.occupant_count, vertex.capacity)

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
                movement_points_per_tick=1  # 1 action per second
            )
            ff.mark_visited(exit_position)
            self.firefighters[ff.id] = ff

    def update(self, actions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Execute one simulation tick.

        Args:
            actions: {firefighter_id: [{'type': 'move'|'push', ...}, ...]}
                - move: {'type': 'move', 'target': vertex_id} - move to adjacent vertex (costs 1 pt)
                - push: {'type': 'push', 'target': vertex_id, 'count': n} - push n people to adjacent vertex (costs 1 pt, respects max_flow)

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

                # Check if people were rescued (push action to exit)
                if action.get('type') == 'push' and success:
                    rescued = action.get('rescued', 0)
                    if rescued > 0:
                        results['rescued_this_tick'] += rescued

            results['action_results'][ff_id] = ff_results

        # Apply random events
        events = self._apply_random_events()
        results['events'].extend(events)
        results['dead_this_tick'] += sum(e.get('deaths', 0) for e in events)

        # Update smoke levels
        self._update_smoke()

        # Apply smoke deaths
        for vertex in self.vertices.values():
            deaths = vertex.apply_smoke_deaths(self.rng)
            if deaths > 0:
                self.dead_count += deaths
                results['dead_this_tick'] += deaths
                results['events'].append({
                    'type': 'smoke_deaths',
                    'vertex': vertex.id,
                    'deaths': deaths
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

            # Move
            ff.position = target_vertex
            ff.mark_visited(target_vertex)
            return True, 'moved', 1

        elif action_type == 'push':
            # Push occupants from current vertex to adjacent vertex
            target_vertex = action.get('target')
            count = action.get('count', 0)

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

            # Get vertices
            current_vertex = self.vertices[ff.position]
            target_vertex_obj = self.vertices[target_vertex]

            # Calculate actual push amount (limited by max_flow and available people)
            available_people = current_vertex.occupant_count
            actual_push = min(count, edge.max_flow, available_people)

            if actual_push > 0:
                # Move people from current to target
                current_vertex.occupant_count -= actual_push

                # Check if target is an exit - if so, rescue them
                if target_vertex_obj.type in ['exit', 'window_exit']:
                    self.rescued_count += actual_push
                    action['rescued'] = actual_push
                else:
                    target_vertex_obj.occupant_count += actual_push
                    action['rescued'] = 0

                return True, f'pushed_{actual_push}', 1
            else:
                return False, 'no_people_to_push', 1

        else:
            return False, 'unknown_action', 0

    def _apply_random_events(self) -> List[Dict[str, Any]]:
        """Apply random fire spread events"""
        events = []

        # Edge deletion (corridor blocking)
        for edge in self.edges.values():
            if edge.exists:
                burn_prob = edge.get_burn_probability(self.tick)
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
                # Probability based on proximity to fire
                if self.fire_origin in self.vertices:
                    # Simple distance-based probability
                    # Rooms closer to fire have higher probability
                    base_prob = 0.0005  # 0.05% per tick base rate
                    # This could be improved with actual distance calculation
                    if self.rng.random() < base_prob:
                        deaths = vertex.burn_down()
                        self.dead_count += deaths
                        events.append({
                            'type': 'room_burned',
                            'vertex_id': vertex.id,
                            'deaths': deaths
                        })

        return events

    def _update_smoke(self):
        """Update smoke levels - simple diffusion model"""
        # Smoke increases near fire and spreads
        new_smoke_levels = {}

        for vertex_id, vertex in self.vertices.items():
            if vertex.is_burned:
                new_smoke_levels[vertex_id] = 1.0
            else:
                # Smoke diffuses from neighbors
                smoke_contribution = vertex.smoke_level * 0.95  # Slight decay
                neighbor_count = 0

                for neighbor_id, edge_id in self.adjacency[vertex_id]:
                    edge = self.edges[edge_id]
                    if edge.exists:
                        neighbor = self.vertices[neighbor_id]
                        smoke_contribution += neighbor.smoke_level * 0.1
                        neighbor_count += 1

                # Fire origin produces smoke
                if vertex_id == self.fire_origin:
                    smoke_contribution = min(1.0, smoke_contribution + 0.05)

                new_smoke_levels[vertex_id] = min(1.0, smoke_contribution)

        # Update all vertices
        for vertex_id, smoke_level in new_smoke_levels.items():
            self.vertices[vertex_id].smoke_level = smoke_level

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
                    'is_burned': v.is_burned
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
                'visited_vertices': list(ff.visited_vertices)
            }

            # Discovered occupants (for all visited vertices)
            for v_id in ff.visited_vertices:
                if v_id in self.vertices:
                    vertex = self.vertices[v_id]
                    # Include all visited vertices (rooms, hallways, etc) except exits
                    if vertex.type not in ['exit', 'window_exit']:
                        discovered_occupants[v_id] = vertex.occupant_count

        return {
            'tick': self.tick,
            'graph': graph_structure,
            'firefighters': firefighter_states,
            'discovered_occupants': discovered_occupants,
            'fire_origin': self.fire_origin
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return performance statistics"""
        total_occupants = sum(v.occupant_count for v in self.vertices.values())

        return {
            'tick': self.tick,
            'rescued': self.rescued_count,
            'dead': self.dead_count,
            'remaining': total_occupants,
            'total_initial': self.rescued_count + self.dead_count + total_occupants,
            'time_minutes': self.tick / 60.0  # Assuming 1 tick = 1 second
        }
