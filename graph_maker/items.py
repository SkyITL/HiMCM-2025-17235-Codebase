#!/usr/bin/env python3
"""
Visual items for graph maker canvas.

Provides NodeItem and EdgeItem for displaying vertices and edges.
"""

from typing import Optional, Dict
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QStyle
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QColor, QPen, QBrush, QFont


class NodeItem(QGraphicsEllipseItem):
    """Visual representation of a vertex in the graph."""

    # Color scheme by vertex type
    TYPE_COLORS = {
        'room': QColor(200, 220, 255),      # Light blue
        'hallway': QColor(220, 220, 220),   # Light gray
        'intersection': QColor(255, 220, 150), # Light orange
        'stairwell': QColor(230, 230, 200), # Light yellow
        'exit': QColor(100, 255, 100)       # Light green
    }

    SELECTED_COLOR = QColor(255, 200, 100)  # Orange for selection
    FIRE_ORIGIN_COLOR = QColor(255, 100, 100)  # Red for fire origin

    def __init__(self, vertex_id: str, vertex_data: Dict, x: float, y: float):
        """
        Initialize node item.

        Args:
            vertex_id: Unique identifier for the vertex
            vertex_data: Dictionary containing vertex properties
            x: X coordinate on canvas
            y: Y coordinate on canvas
        """
        self.vertex_id = vertex_id
        self.vertex_data = vertex_data
        self.is_fire_origin = False

        # Calculate radius from area
        radius = self.calculate_radius(vertex_data)

        # Initialize with calculated radius
        super().__init__(-radius, -radius, radius * 2, radius * 2)

        # Set position
        self.setPos(x, y)

        # Enable interaction
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)

        # Create label
        self.label = QGraphicsTextItem(self.get_label_text(), self)
        self.label.setDefaultTextColor(Qt.black)
        font = QFont("Arial", 8)
        self.label.setFont(font)
        self.center_label()

        # Update appearance
        self.update_appearance()

    @staticmethod
    def calculate_radius(vertex_data: Dict) -> float:
        """Calculate node radius based on area."""
        area = vertex_data.get('area', 100.0)
        vertex_type = vertex_data.get('type', 'room')

        # Scale radius with square root of area (so visual area scales linearly with actual area)
        # Base: 100 m² -> 30 pixel radius (increased for more visibility)
        base_area = 100.0
        base_radius = 30.0

        if vertex_type in ['exit', 'hallway', 'intersection', 'stairwell']:
            # Smaller base for non-rooms
            base_radius = 12.0

        # radius = base_radius * sqrt(area / base_area)
        import math
        radius = base_radius * math.sqrt(area / base_area)

        # Clamp to wider range for more dramatic variation
        # Min: 5 pixels (very small rooms), Max: 80 pixels (very large rooms)
        return max(5.0, min(80.0, radius))

    def get_label_text(self) -> str:
        """Get display label for the node."""
        # Use short name or ID
        vertex_type = self.vertex_data.get('type', 'room')
        if vertex_type == 'exit':
            return 'EXIT'
        elif vertex_type == 'intersection':
            return 'X'  # Short label for intersections
        else:
            # Use last part of ID if it has underscores
            parts = self.vertex_id.split('_')
            if len(parts) > 2:
                return '_'.join(parts[-2:])
            return self.vertex_id[:8]  # Limit length

    def center_label(self):
        """Center the label within the node."""
        label_rect = self.label.boundingRect()
        x = -label_rect.width() / 2
        y = -label_rect.height() / 2
        self.label.setPos(x, y)

    def update_appearance(self):
        """Update visual appearance based on state."""
        # Determine color
        if self.isSelected():
            color = self.SELECTED_COLOR
        elif self.is_fire_origin:
            color = self.FIRE_ORIGIN_COLOR
        else:
            vertex_type = self.vertex_data.get('type', 'room')
            color = self.TYPE_COLORS.get(vertex_type, QColor(200, 200, 200))

        # Set brush and pen
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(50, 50, 50), 2))

    def set_fire_origin(self, is_origin: bool):
        """Mark this node as the fire origin."""
        self.is_fire_origin = is_origin
        self.update_appearance()

    def update_data(self, vertex_data: Dict):
        """Update vertex data and refresh appearance."""
        self.vertex_data = vertex_data

        # Always recalculate radius based on current area
        new_radius = self.calculate_radius(vertex_data)
        self.setRect(-new_radius, -new_radius, new_radius * 2, new_radius * 2)

        self.label.setPlainText(self.get_label_text())
        self.center_label()
        self.update_appearance()

    def itemChange(self, change, value):
        """Handle item changes (for detecting selection and position)."""
        if change == QGraphicsEllipseItem.ItemSelectedChange:
            self.update_appearance()
        elif change == QGraphicsEllipseItem.ItemPositionHasChanged:
            # Update model position
            pos = self.pos()
            model_x = pos.x() / 100
            model_y = pos.y() / 100
            self.vertex_data['visual_position'] = {'x': model_x, 'y': model_y}

        return super().itemChange(change, value)

    def mouseMoveEvent(self, event):
        """Handle mouse move (for dragging)."""
        super().mouseMoveEvent(event)
        # Notify connected edges to update
        scene = self.scene()
        if scene and hasattr(scene, 'update_edges_for_node'):
            scene.update_edges_for_node(self.vertex_id)

    def get_center(self) -> QPointF:
        """Get the center point of this node in scene coordinates."""
        return self.pos()


class EdgeItem(QGraphicsLineItem):
    """Visual representation of an edge in the graph."""

    def __init__(self, edge_id: str, edge_data: Dict, node_a: NodeItem, node_b: NodeItem):
        """
        Initialize edge item.

        Args:
            edge_id: Unique identifier for the edge
            edge_data: Dictionary containing edge properties
            node_a: First node item
            node_b: Second node item
        """
        super().__init__()

        self.edge_id = edge_id
        self.edge_data = edge_data
        self.node_a = node_a
        self.node_b = node_b

        # Set drawing order (behind nodes)
        self.setZValue(-1)

        # Enable selection
        self.setFlag(QGraphicsLineItem.ItemIsSelectable, True)

        # Create label for edge width
        self.label = QGraphicsTextItem()
        self.label.setDefaultTextColor(QColor(100, 100, 100))
        font = QFont("Arial", 7)
        self.label.setFont(font)
        self.label.setZValue(-0.5)  # Above edge line, below nodes

        # Update line and label
        self.update_line()
        self.update_appearance()

    def update_line(self):
        """Update line position based on node positions."""
        # Get node centers
        p1 = self.node_a.get_center()
        p2 = self.node_b.get_center()

        # Set line
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())

        # Update label position
        mid_x = (p1.x() + p2.x()) / 2
        mid_y = (p1.y() + p2.y()) / 2

        # Position label slightly offset from midpoint
        label_rect = self.label.boundingRect()
        self.label.setPos(mid_x - label_rect.width() / 2, mid_y - label_rect.height() / 2 - 5)

    def update_appearance(self):
        """Update visual appearance based on state."""
        # Get width from edge data
        width = self.edge_data.get('width', 2.0)

        # Line thickness scales with width
        pen_width = max(2, int(width * 2))

        # Color based on selection
        if self.isSelected():
            color = QColor(255, 150, 50)  # Orange for selection
        else:
            color = QColor(100, 100, 100)  # Gray for normal

        self.setPen(QPen(color, pen_width))

        # Update label text
        self.label.setPlainText(f"w={width:.1f}")

    def update_data(self, edge_data: Dict):
        """Update edge data and refresh appearance."""
        self.edge_data = edge_data
        self.update_appearance()

    def itemChange(self, change, value):
        """Handle item changes (for detecting selection)."""
        if change == QGraphicsLineItem.ItemSelectedChange:
            self.update_appearance()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        """Custom paint to handle selection differently."""
        # Remove default selection rectangle
        option.state &= ~QStyle.State_Selected
        super().paint(painter, option, widget)
