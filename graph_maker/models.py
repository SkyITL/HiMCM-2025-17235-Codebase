#!/usr/bin/env python3
"""
Data models for graph maker tool.

Manages vertices, edges, occupancy probabilities, and fire parameters.
"""

from typing import Dict, List, Optional, Tuple
import json


class GraphModel:
    """Data model for evacuation building graph."""

    def __init__(self):
        """Initialize empty graph model."""
        self.vertices: Dict[str, Dict] = {}
        self.edges: Dict[str, Dict] = {}
        self.occupancy_probabilities: Dict[str, Dict[str, float]] = {}
        self.fire_origin: Optional[str] = None
        self.num_firefighters: int = 3
        self.firefighter_spawn_vertices: List[str] = []  # Empty = spawn at exits
        self.background_image_path: Optional[str] = None
        self.background_opacity: float = 0.5
        self.description: str = ""

    # ========== Vertex Management ==========

    def add_vertex(self, vertex_id: str, vertex_data: Dict) -> bool:
        """
        Add a new vertex to the graph.

        Args:
            vertex_id: Unique identifier for the vertex
            vertex_data: Dictionary containing vertex properties

        Returns:
            True if added successfully, False if ID already exists
        """
        if vertex_id in self.vertices:
            return False

        # Set defaults for missing fields
        defaults = {
            'id': vertex_id,
            'type': 'room',
            'room_type': 'office',
            'capacity': 20,
            'priority': 2,
            'sweep_time': 2,
            'area': 100.0,
            'visual_position': {'x': 0, 'y': 0}
        }

        # Merge with provided data
        vertex = {**defaults, **vertex_data}
        vertex['id'] = vertex_id  # Ensure ID matches

        self.vertices[vertex_id] = vertex
        return True

    def update_vertex(self, vertex_id: str, vertex_data: Dict) -> bool:
        """
        Update an existing vertex.

        Args:
            vertex_id: ID of vertex to update
            vertex_data: Dictionary with updated properties

        Returns:
            True if updated successfully, False if vertex doesn't exist
        """
        if vertex_id not in self.vertices:
            return False

        # Update fields, preserving ID
        self.vertices[vertex_id].update(vertex_data)
        self.vertices[vertex_id]['id'] = vertex_id
        return True

    def delete_vertex(self, vertex_id: str) -> bool:
        """
        Delete a vertex and all connected edges.

        Args:
            vertex_id: ID of vertex to delete

        Returns:
            True if deleted successfully, False if vertex doesn't exist
        """
        if vertex_id not in self.vertices:
            return False

        # Remove vertex
        del self.vertices[vertex_id]

        # Remove connected edges
        edges_to_delete = []
        for edge_id, edge_data in self.edges.items():
            if edge_data['vertex_a'] == vertex_id or edge_data['vertex_b'] == vertex_id:
                edges_to_delete.append(edge_id)

        for edge_id in edges_to_delete:
            del self.edges[edge_id]

        # Remove occupancy probability if exists
        if vertex_id in self.occupancy_probabilities:
            del self.occupancy_probabilities[vertex_id]

        # Clear fire origin if this was it
        if self.fire_origin == vertex_id:
            self.fire_origin = None

        return True

    def get_vertex(self, vertex_id: str) -> Optional[Dict]:
        """Get vertex data by ID."""
        return self.vertices.get(vertex_id)

    # ========== Edge Management ==========

    def add_edge(self, edge_id: str, vertex_a: str, vertex_b: str, edge_data: Optional[Dict] = None) -> bool:
        """
        Add a new edge between two vertices.

        Args:
            edge_id: Unique identifier for the edge
            vertex_a: ID of first vertex
            vertex_b: ID of second vertex
            edge_data: Optional dictionary containing edge properties

        Returns:
            True if added successfully, False if ID exists or vertices don't exist
        """
        if edge_id in self.edges:
            return False

        if vertex_a not in self.vertices or vertex_b not in self.vertices:
            return False

        # Set defaults
        defaults = {
            'id': edge_id,
            'vertex_a': vertex_a,
            'vertex_b': vertex_b,
            'max_flow': 10,
            'base_burn_rate': 0.0002,
            'width': 2.0
        }

        # Merge with provided data
        edge = {**defaults, **(edge_data or {})}
        edge['id'] = edge_id
        edge['vertex_a'] = vertex_a
        edge['vertex_b'] = vertex_b

        self.edges[edge_id] = edge
        return True

    def update_edge(self, edge_id: str, edge_data: Dict) -> bool:
        """
        Update an existing edge.

        Args:
            edge_id: ID of edge to update
            edge_data: Dictionary with updated properties

        Returns:
            True if updated successfully, False if edge doesn't exist
        """
        if edge_id not in self.edges:
            return False

        # Update fields, preserving ID and vertex connections
        vertex_a = self.edges[edge_id]['vertex_a']
        vertex_b = self.edges[edge_id]['vertex_b']

        self.edges[edge_id].update(edge_data)
        self.edges[edge_id]['id'] = edge_id
        self.edges[edge_id]['vertex_a'] = vertex_a
        self.edges[edge_id]['vertex_b'] = vertex_b

        return True

    def delete_edge(self, edge_id: str) -> bool:
        """
        Delete an edge.

        Args:
            edge_id: ID of edge to delete

        Returns:
            True if deleted successfully, False if edge doesn't exist
        """
        if edge_id not in self.edges:
            return False

        del self.edges[edge_id]
        return True

    def get_edge(self, edge_id: str) -> Optional[Dict]:
        """Get edge data by ID."""
        return self.edges.get(edge_id)

    def get_edges_for_vertex(self, vertex_id: str) -> List[str]:
        """Get list of edge IDs connected to a vertex."""
        connected_edges = []
        for edge_id, edge_data in self.edges.items():
            if edge_data['vertex_a'] == vertex_id or edge_data['vertex_b'] == vertex_id:
                connected_edges.append(edge_id)
        return connected_edges

    # ========== Occupancy Management ==========

    def set_occupancy_range(self, vertex_id: str, capable_min: int, capable_max: int,
                           incapable_min: int, incapable_max: int) -> bool:
        """
        Set occupancy ranges for a vertex.

        Args:
            vertex_id: ID of vertex
            capable_min: Minimum number of capable occupants
            capable_max: Maximum number of capable occupants
            incapable_min: Minimum number of incapable occupants
            incapable_max: Maximum number of incapable occupants

        Returns:
            True if set successfully, False if vertex doesn't exist or invalid values
        """
        if vertex_id not in self.vertices:
            return False

        if capable_min < 0 or capable_max < capable_min:
            return False
        if incapable_min < 0 or incapable_max < incapable_min:
            return False

        self.occupancy_probabilities[vertex_id] = {
            'capable': {'min': capable_min, 'max': capable_max},
            'incapable': {'min': incapable_min, 'max': incapable_max}
        }
        return True

    def get_occupancy_range(self, vertex_id: str) -> Optional[Dict]:
        """Get occupancy ranges for a vertex."""
        config = self.occupancy_probabilities.get(vertex_id)
        if not config:
            return None

        # Handle both old probability format and new range format
        capable = config.get('capable', 0)
        incapable = config.get('incapable', 0)

        # If already in range format, return as-is
        if isinstance(capable, dict) and 'min' in capable:
            return config

        # Convert old probability format to range format for display (backward compatibility)
        # This is just for display - the actual simulation will handle probabilities
        return {
            'capable': {'min': 0, 'max': 0},  # Can't convert probabilities to ranges meaningfully
            'incapable': {'min': 0, 'max': 0}
        }

    def clear_occupancy_probability(self, vertex_id: str) -> bool:
        """Clear occupancy probabilities for a vertex."""
        if vertex_id in self.occupancy_probabilities:
            del self.occupancy_probabilities[vertex_id]
            return True
        return False

    # ========== Fire Parameters ==========

    def set_fire_origin(self, vertex_id: Optional[str]) -> bool:
        """
        Set the fire origin vertex.

        Args:
            vertex_id: ID of vertex, or None to clear

        Returns:
            True if set successfully, False if vertex doesn't exist
        """
        if vertex_id is not None and vertex_id not in self.vertices:
            return False

        self.fire_origin = vertex_id
        return True

    # ========== Validation ==========

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the graph model.

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Check for at least one vertex
        if not self.vertices:
            errors.append("Graph must have at least one vertex")

        # Check for at least one exit
        has_exit = any(v.get('type') == 'exit' for v in self.vertices.values())
        if not has_exit:
            errors.append("Graph must have at least one exit")

        # Validate edges reference existing vertices
        for edge_id, edge_data in self.edges.items():
            vertex_a = edge_data.get('vertex_a')
            vertex_b = edge_data.get('vertex_b')

            if vertex_a not in self.vertices:
                errors.append(f"Edge '{edge_id}' references non-existent vertex '{vertex_a}'")

            if vertex_b not in self.vertices:
                errors.append(f"Edge '{edge_id}' references non-existent vertex '{vertex_b}'")

        # Check visual positions
        for vertex_id, vertex_data in self.vertices.items():
            pos = vertex_data.get('visual_position')
            if not pos or 'x' not in pos or 'y' not in pos:
                errors.append(f"Vertex '{vertex_id}' missing valid visual_position")

        # Check fire origin if set
        if self.fire_origin and self.fire_origin not in self.vertices:
            errors.append(f"Fire origin '{self.fire_origin}' does not exist")

        # Validate occupancy probabilities
        for vertex_id, probs in self.occupancy_probabilities.items():
            if vertex_id not in self.vertices:
                errors.append(f"Occupancy probability set for non-existent vertex '{vertex_id}'")

            capable = probs.get('capable', 0)
            incapable = probs.get('incapable', 0)

            if not (0.0 <= capable <= 1.0):
                errors.append(f"Invalid capable probability for '{vertex_id}': {capable}")

            if not (0.0 <= incapable <= 1.0):
                errors.append(f"Invalid incapable probability for '{vertex_id}': {incapable}")

        return (len(errors) == 0, errors)

    # ========== Serialization ==========

    def to_config(self) -> Dict:
        """
        Export model to config dictionary (matches config_example.json format).

        Returns:
            Dictionary suitable for JSON serialization
        """
        config = {
            'description': self.description,
            'vertices': list(self.vertices.values()),
            'edges': list(self.edges.values()),
            'occupancy_probabilities': self.occupancy_probabilities,
            'fire_params': {
                'origin': self.fire_origin if self.fire_origin else 'office_bottom_center',
                'initial_smoke_level': 0.3
            },
            'firefighter_params': {
                'num_firefighters': self.num_firefighters,
                'spawn_vertices': self.firefighter_spawn_vertices
            }
        }

        return config

    def from_config(self, config: Dict) -> bool:
        """
        Load model from config dictionary.

        Args:
            config: Dictionary from JSON config file

        Returns:
            True if loaded successfully, False on error
        """
        try:
            # Clear existing data
            self.vertices.clear()
            self.edges.clear()
            self.occupancy_probabilities.clear()
            self.fire_origin = None

            # Load description
            self.description = config.get('description', '')

            # Load vertices
            for vertex_data in config.get('vertices', []):
                vertex_id = vertex_data['id']
                self.vertices[vertex_id] = vertex_data

            # Load edges
            for edge_data in config.get('edges', []):
                edge_id = edge_data['id']
                self.edges[edge_id] = edge_data

            # Load occupancy probabilities
            self.occupancy_probabilities = config.get('occupancy_probabilities', {})

            # Load fire parameters
            fire_params = config.get('fire_params', {})
            self.fire_origin = fire_params.get('origin')

            # Load firefighter parameters
            firefighter_params = config.get('firefighter_params', {})
            self.num_firefighters = firefighter_params.get('num_firefighters', 3)
            self.firefighter_spawn_vertices = firefighter_params.get('spawn_vertices', [])

            return True

        except Exception as e:
            print(f"Error loading config: {e}")
            return False

    def save_to_file(self, filepath: str) -> bool:
        """
        Save model to JSON file.

        Args:
            filepath: Path to save file

        Returns:
            True if saved successfully, False on error
        """
        try:
            config = self.to_config()
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving to file: {e}")
            return False

    def load_from_file(self, filepath: str) -> bool:
        """
        Load model from JSON file.

        Args:
            filepath: Path to load file

        Returns:
            True if loaded successfully, False on error
        """
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            return self.from_config(config)
        except Exception as e:
            print(f"Error loading from file: {e}")
            return False

    # ========== Statistics ==========

    def get_stats(self) -> Dict:
        """Get statistics about the graph."""
        num_vertices = len(self.vertices)
        num_edges = len(self.edges)

        # Count by type
        vertex_types = {}
        for vertex_data in self.vertices.values():
            vtype = vertex_data.get('type', 'unknown')
            vertex_types[vtype] = vertex_types.get(vtype, 0) + 1

        # Estimate expected occupants
        expected_occupants = 0.0
        for vertex_id, probs in self.occupancy_probabilities.items():
            vertex = self.vertices.get(vertex_id)
            if vertex:
                capable_config = probs.get('capable', 0.0)
                incapable_config = probs.get('incapable', 0.0)

                # Handle both old probability format and new range format
                if isinstance(capable_config, dict):
                    # New range format: use average of min and max
                    capable_avg = (capable_config.get('min', 0) + capable_config.get('max', 0)) / 2.0
                else:
                    # Old probability format
                    capable_avg = capable_config * vertex.get('capacity', 20)

                if isinstance(incapable_config, dict):
                    # New range format: use average of min and max
                    incapable_avg = (incapable_config.get('min', 0) + incapable_config.get('max', 0)) / 2.0
                else:
                    # Old probability format
                    incapable_avg = incapable_config * vertex.get('capacity', 20)

                expected_occupants += capable_avg + incapable_avg

        return {
            'num_vertices': num_vertices,
            'num_edges': num_edges,
            'vertex_types': vertex_types,
            'expected_occupants': expected_occupants,
            'has_fire_origin': self.fire_origin is not None
        }
