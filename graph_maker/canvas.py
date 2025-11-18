#!/usr/bin/env python3
"""
Canvas view for graph maker.

Provides interactive canvas for creating and editing building graphs.
"""

from typing import Optional, Dict, List, Tuple
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QMenu, QAction,
                              QInputDialog, QMessageBox, QGraphicsRectItem,
                              QGraphicsLineItem, QGraphicsTextItem)
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QRectF, QEvent
from PyQt5.QtGui import QPixmap, QPainter, QTransform, QPen, QColor, QBrush, QFont, QMouseEvent

from .models import GraphModel
from .items import NodeItem, EdgeItem


class GraphCanvas(QGraphicsView):
    """Interactive canvas for editing building evacuation graphs."""

    # Signals for updating UI
    selection_changed = pyqtSignal(object)  # Emits selected item (NodeItem/EdgeItem or None)
    graph_modified = pyqtSignal()  # Emits when graph is modified
    node_position_changed = pyqtSignal(str)  # Emits vertex_id when node position changes

    def __init__(self, model: GraphModel):
        """
        Initialize canvas.

        Args:
            model: GraphModel instance to edit
        """
        super().__init__()

        self.model = model
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Item tracking
        self.node_items: Dict[str, NodeItem] = {}  # vertex_id -> NodeItem
        self.edge_items: Dict[str, EdgeItem] = {}  # edge_id -> EdgeItem
        self.background_pixmap_item = None

        # Edge creation state
        self.edge_creation_mode = False
        self.edge_creation_start_node: Optional[NodeItem] = None
        self.temp_edge_line = None


        # Measurement tool state
        self.measurement_mode = None  # None, 'box', or 'line'
        self.measurement_start_pos = None
        self.measurement_item = None
        self.measurement_label = None
        self.pixels_per_meter = 20.0  # Default scale: 20 pixels = 1 meter

        # Smart hallway generation between intersections
        self.hallway_gen_start_intersection: Optional[NodeItem] = None

        # Visual reference ruler for measurement scale calibration
        self.scale_reference_line = None
        self.scale_reference_label = None
        self.scale_reference_visible = False

        # Configure view
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # Context menu setup
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Track selection changes
        self.scene.selectionChanged.connect(self.on_selection_changed)

        # Initial refresh
        self.refresh_from_model()

    # ========== Model Synchronization ==========

    def refresh_from_model(self):
        """Rebuild canvas from model data."""
        # Clear existing items
        self.scene.clear()
        self.node_items.clear()
        self.edge_items.clear()

        # Reload background if exists
        if self.model.background_image_path:
            self.load_background_image(self.model.background_image_path, self.model.background_opacity)

        # Create node items
        for vertex_id, vertex_data in self.model.vertices.items():
            pos = vertex_data.get('visual_position', {'x': 0, 'y': 0})
            x = pos.get('x', 0) * 100  # Scale to canvas coordinates
            y = pos.get('y', 0) * 100

            node_item = NodeItem(vertex_id, vertex_data, x, y)

            # Mark fire origin
            if vertex_id == self.model.fire_origin:
                node_item.set_fire_origin(True)

            self.scene.addItem(node_item)
            self.node_items[vertex_id] = node_item

        # Create edge items
        for edge_id, edge_data in self.model.edges.items():
            vertex_a_id = edge_data['vertex_a']
            vertex_b_id = edge_data['vertex_b']

            node_a = self.node_items.get(vertex_a_id)
            node_b = self.node_items.get(vertex_b_id)

            if node_a and node_b:
                edge_item = EdgeItem(edge_id, edge_data, node_a, node_b)
                self.scene.addItem(edge_item)
                self.scene.addItem(edge_item.label)
                self.edge_items[edge_id] = edge_item

    def refresh_for_floor(self, floor: int):
        """
        Refresh canvas to show only nodes/edges on specified floor.

        Args:
            floor: Floor number to display (1-indexed)
        """
        # Clear existing items
        self.scene.clear()
        self.node_items.clear()
        self.edge_items.clear()

        # Reload background if exists
        if self.model.background_image_path:
            self.load_background_image(self.model.background_image_path, self.model.background_opacity)

        # Get vertices on this floor
        floor_vertices = self.model.get_vertices_on_floor(floor)

        # Create node items for this floor only
        for vertex_id, vertex_data in floor_vertices.items():
            pos = vertex_data.get('visual_position', {'x': 0, 'y': 0})
            x = pos.get('x', 0) * 100  # Scale to canvas coordinates
            y = pos.get('y', 0) * 100

            node_item = NodeItem(vertex_id, vertex_data, x, y)

            # Mark fire origin
            if vertex_id == self.model.fire_origin:
                node_item.set_fire_origin(True)

            self.scene.addItem(node_item)
            self.node_items[vertex_id] = node_item

        # Create edge items (only edges where both endpoints are on this floor)
        for edge_id, edge_data in self.model.edges.items():
            vertex_a_id = edge_data['vertex_a']
            vertex_b_id = edge_data['vertex_b']

            # Check if both endpoints are on this floor
            node_a = self.node_items.get(vertex_a_id)
            node_b = self.node_items.get(vertex_b_id)

            if node_a and node_b:
                edge_item = EdgeItem(edge_id, edge_data, node_a, node_b)
                self.scene.addItem(edge_item)
                self.scene.addItem(edge_item.label)
                self.edge_items[edge_id] = edge_item

    def sync_node_position(self, vertex_id: str):
        """Update model when node is moved."""
        node_item = self.node_items.get(vertex_id)
        if not node_item:
            return

        # Convert canvas coordinates to model coordinates
        pos = node_item.pos()
        model_x = pos.x() / 100
        model_y = pos.y() / 100

        # Update model
        vertex_data = self.model.get_vertex(vertex_id)
        if vertex_data:
            vertex_data['visual_position'] = {'x': model_x, 'y': model_y}
            self.graph_modified.emit()

    def update_edges_for_node(self, vertex_id: str):
        """Update all edges connected to a node."""
        for edge_id, edge_item in self.edge_items.items():
            if edge_item.node_a.vertex_id == vertex_id or edge_item.node_b.vertex_id == vertex_id:
                edge_item.update_line()

        # Sync position to model
        self.sync_node_position(vertex_id)

        # Emit signal to update property panel
        self.node_position_changed.emit(vertex_id)

    # ========== Background Image ==========

    def load_background_image(self, image_path: str, opacity: float = 0.5):
        """
        Load a background image for reference.

        Args:
            image_path: Path to image file
            opacity: Opacity level (0.0-1.0)
        """
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                return

            # Remove old background if exists
            if self.background_pixmap_item:
                self.scene.removeItem(self.background_pixmap_item)

            # Add new background
            self.background_pixmap_item = self.scene.addPixmap(pixmap)
            self.background_pixmap_item.setOpacity(opacity)
            self.background_pixmap_item.setZValue(-100)  # Behind everything

            # Center on background
            self.setSceneRect(self.background_pixmap_item.boundingRect())

            # Update model
            self.model.background_image_path = image_path
            self.model.background_opacity = opacity
            self.graph_modified.emit()

        except Exception as e:
            pass  # Silently fail

    def set_background_opacity(self, opacity: float):
        """Change background image opacity."""
        if self.background_pixmap_item:
            self.background_pixmap_item.setOpacity(opacity)
            self.model.background_opacity = opacity
            self.graph_modified.emit()

    # ========== Context Menu ==========

    def show_context_menu(self, position):
        """Show context menu at cursor position."""
        # Map to scene coordinates
        scene_pos = self.mapToScene(position)

        # Check what's under cursor
        item = self.scene.itemAt(scene_pos, QTransform())

        # If item is a child (e.g., label), get the parent
        if item and item.parentItem():
            parent = item.parentItem()
            if isinstance(parent, NodeItem):
                item = parent
            elif isinstance(parent, EdgeItem):
                item = parent

        menu = QMenu(self)

        if isinstance(item, NodeItem):
            self.show_node_context_menu(menu, item)
        elif isinstance(item, EdgeItem):
            self.show_edge_context_menu(menu, item)
        else:
            self.show_canvas_context_menu(menu, scene_pos)

        menu.exec_(self.mapToGlobal(position))

    def show_node_context_menu(self, menu: QMenu, node_item: NodeItem):
        """Context menu for node items."""
        # Set as fire origin
        if not node_item.is_fire_origin:
            action = QAction("Set as Fire Origin", menu)
            action.triggered.connect(lambda: self.set_fire_origin(node_item.vertex_id))
            menu.addAction(action)
        else:
            action = QAction("Clear Fire Origin", menu)
            action.triggered.connect(lambda: self.set_fire_origin(None))
            menu.addAction(action)

        menu.addSeparator()

        # Create edge from this node
        action = QAction("Create Edge from Here", menu)
        action.triggered.connect(lambda: self.start_edge_creation(node_item))
        menu.addAction(action)

        # Smart hallway generation for intersections
        if node_item.vertex_data.get('type') == 'intersection':
            menu.addSeparator()

            if not self.hallway_gen_start_intersection:
                action = QAction("Generate Hallways from Here", menu)
                action.triggered.connect(lambda: self.start_hallway_generation(node_item))
                menu.addAction(action)
            elif self.hallway_gen_start_intersection.vertex_id != node_item.vertex_id:
                action = QAction(f"Generate Hallways to Here from {self.hallway_gen_start_intersection.vertex_id}", menu)
                action.triggered.connect(lambda: self.complete_hallway_generation(node_item))
                menu.addAction(action)

                action = QAction("Cancel Hallway Generation", menu)
                action.triggered.connect(lambda: self.cancel_hallway_generation())
                menu.addAction(action)

        menu.addSeparator()

        # Delete node
        action = QAction("Delete Node", menu)
        action.triggered.connect(lambda: self.delete_node(node_item.vertex_id))
        menu.addAction(action)

    def show_edge_context_menu(self, menu: QMenu, edge_item: EdgeItem):
        """Context menu for edge items."""
        # Delete edge
        action = QAction("Delete Edge", menu)
        action.triggered.connect(lambda: self.delete_edge(edge_item.edge_id))
        menu.addAction(action)

    def show_canvas_context_menu(self, menu: QMenu, scene_pos: QPointF):
        """Context menu for empty canvas."""
        # Add node submenu
        add_menu = menu.addMenu("Add Node")

        action = QAction("Room", add_menu)
        action.triggered.connect(lambda: self.add_node(scene_pos, 'room'))
        add_menu.addAction(action)

        action = QAction("Hallway", add_menu)
        action.triggered.connect(lambda: self.add_node(scene_pos, 'hallway'))
        add_menu.addAction(action)

        action = QAction("Intersection", add_menu)
        action.triggered.connect(lambda: self.add_node(scene_pos, 'intersection'))
        add_menu.addAction(action)

        action = QAction("Stairwell", add_menu)
        action.triggered.connect(lambda: self.add_node(scene_pos, 'stairwell'))
        add_menu.addAction(action)

        action = QAction("Exit", add_menu)
        action.triggered.connect(lambda: self.add_node(scene_pos, 'exit'))
        add_menu.addAction(action)

    # ========== Node Operations ==========

    def add_node(self, scene_pos: QPointF, node_type: str):
        """Add a new node at the specified position."""
        # Find the next available number for this node type
        counter = 1
        while f"{node_type}_{counter}" in self.model.vertices:
            counter += 1

        # Get node ID from user with auto-serialized default
        vertex_id, ok = QInputDialog.getText(
            self, "Add Node", "Enter node ID:",
            text=f"{node_type}_{counter}"
        )

        if not ok or not vertex_id:
            return

        # Check if ID already exists
        if vertex_id in self.model.vertices:
            return

        # Create vertex data
        model_x = scene_pos.x() / 100
        model_y = scene_pos.y() / 100

        vertex_data = {
            'id': vertex_id,
            'type': node_type,
            'room_type': 'office' if node_type == 'room' else 'none',
            'capacity': 20 if node_type == 'room' else 50,
            'priority': 2 if node_type == 'room' else (0 if node_type == 'exit' else 1),
            'sweep_time': 2 if node_type == 'room' else (0 if node_type == 'exit' else 1),
            'area': 100.0 if node_type == 'room' else (10.0 if node_type == 'exit' else 30.0),
            'visual_position': {'x': model_x, 'y': model_y}
        }

        # Add to model
        if self.model.add_vertex(vertex_id, vertex_data):
            # Get vertex data from model (model creates a new dict, so we need its reference)
            model_vertex_data = self.model.get_vertex(vertex_id)

            # Add to scene with model's vertex data reference
            node_item = NodeItem(vertex_id, model_vertex_data, scene_pos.x(), scene_pos.y())
            self.scene.addItem(node_item)
            self.node_items[vertex_id] = node_item

            self.graph_modified.emit()

    def delete_node(self, vertex_id: str):
        """Delete a node and its connected edges."""
        # Remove from scene
        node_item = self.node_items.get(vertex_id)
        if node_item:
            self.scene.removeItem(node_item)
            del self.node_items[vertex_id]

        # Remove connected edges from scene
        edges_to_delete = self.model.get_edges_for_vertex(vertex_id)
        for edge_id in edges_to_delete:
            edge_item = self.edge_items.get(edge_id)
            if edge_item:
                self.scene.removeItem(edge_item.label)
                self.scene.removeItem(edge_item)
                del self.edge_items[edge_id]

        # Remove from model
        self.model.delete_vertex(vertex_id)
        self.graph_modified.emit()

    def set_fire_origin(self, vertex_id: Optional[str]):
        """Set or clear the fire origin."""
        # Clear previous fire origin
        if self.model.fire_origin:
            old_node = self.node_items.get(self.model.fire_origin)
            if old_node:
                old_node.set_fire_origin(False)

        # Set new fire origin
        self.model.set_fire_origin(vertex_id)

        if vertex_id:
            new_node = self.node_items.get(vertex_id)
            if new_node:
                new_node.set_fire_origin(True)

        self.graph_modified.emit()

    # ========== Edge Operations ==========

    def start_edge_creation(self, start_node: NodeItem):
        """Start creating an edge from a node."""
        self.edge_creation_mode = True
        self.edge_creation_start_node = start_node

    def mousePressEvent(self, event):
        """Handle mouse press for edge creation, measurement tools, and panning."""
        scene_pos = self.mapToScene(event.pos())

        # Handle middle mouse button for panning
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.ClosedHandCursor)
            # Create a fake left button event to start dragging
            fake_event = QMouseEvent(
                event.type(),
                event.pos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mousePressEvent(fake_event)
            return

        # Handle measurement mode
        if self.measurement_mode and event.button() == Qt.LeftButton:
            self.measurement_start_pos = scene_pos
            return

        # Handle edge creation mode
        if self.edge_creation_mode and event.button() == Qt.LeftButton:
            # Check if clicked on a node
            item = self.scene.itemAt(scene_pos, QTransform())

            # If item is a child (e.g., label), get the parent
            if item and item.parentItem():
                parent = item.parentItem()
                if isinstance(parent, NodeItem):
                    item = parent

            if isinstance(item, NodeItem) and item != self.edge_creation_start_node:
                # Create edge
                self.create_edge(self.edge_creation_start_node.vertex_id, item.vertex_id)
                self.edge_creation_mode = False
                self.edge_creation_start_node = None
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for measurement tools."""
        if self.measurement_mode and self.measurement_start_pos:
            scene_pos = self.mapToScene(event.pos())

            # Remove old measurement items
            if self.measurement_item:
                self.scene.removeItem(self.measurement_item)
            if self.measurement_label:
                self.scene.removeItem(self.measurement_label)

            if self.measurement_mode == 'box':
                # Draw box
                rect = QRectF(self.measurement_start_pos, scene_pos).normalized()
                self.measurement_item = QGraphicsRectItem(rect)
                self.measurement_item.setPen(QPen(QColor(255, 100, 0), 2, Qt.DashLine))
                self.measurement_item.setBrush(QBrush(QColor(255, 150, 0, 50)))
                self.scene.addItem(self.measurement_item)

                # Calculate dimensions
                width_pixels = abs(rect.width())
                height_pixels = abs(rect.height())
                width_meters = width_pixels / self.pixels_per_meter
                height_meters = height_pixels / self.pixels_per_meter
                area = width_meters * height_meters

                # Add label
                label_text = f"{width_meters:.2f}m × {height_meters:.2f}m\nArea: {area:.2f}m²"
                self.measurement_label = QGraphicsTextItem(label_text)
                self.measurement_label.setDefaultTextColor(QColor(255, 100, 0))
                self.measurement_label.setFont(QFont("Arial", 10, QFont.Bold))
                self.measurement_label.setPos(rect.center())
                self.scene.addItem(self.measurement_label)

            elif self.measurement_mode == 'line':
                # Draw line
                self.measurement_item = QGraphicsLineItem(
                    self.measurement_start_pos.x(), self.measurement_start_pos.y(),
                    scene_pos.x(), scene_pos.y()
                )
                self.measurement_item.setPen(QPen(QColor(0, 150, 255), 3))
                self.scene.addItem(self.measurement_item)

                # Calculate length
                dx = scene_pos.x() - self.measurement_start_pos.x()
                dy = scene_pos.y() - self.measurement_start_pos.y()
                length_pixels = (dx**2 + dy**2)**0.5
                length_meters = length_pixels / self.pixels_per_meter

                # Add label
                label_text = f"{length_meters:.2f}m"
                self.measurement_label = QGraphicsTextItem(label_text)
                self.measurement_label.setDefaultTextColor(QColor(0, 150, 255))
                self.measurement_label.setFont(QFont("Arial", 10, QFont.Bold))
                mid_x = (self.measurement_start_pos.x() + scene_pos.x()) / 2
                mid_y = (self.measurement_start_pos.y() + scene_pos.y()) / 2
                self.measurement_label.setPos(mid_x, mid_y - 20)
                self.scene.addItem(self.measurement_label)

            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release for measurement tools and panning."""
        # Handle middle mouse button release (end panning)
        if event.button() == Qt.MiddleButton:
            # Create fake left button release event
            fake_event = QMouseEvent(
                event.type(),
                event.pos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mouseReleaseEvent(fake_event)
            # Restore drag mode and cursor
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setCursor(Qt.ArrowCursor)
            return

        if self.measurement_mode and event.button() == Qt.LeftButton and self.measurement_start_pos:
            # Measurement complete
            if self.measurement_mode == 'box':
                self.apply_box_measurement()
            elif self.measurement_mode == 'line':
                self.apply_line_measurement()
            return

        super().mouseReleaseEvent(event)

    def create_edge(self, vertex_a_id: str, vertex_b_id: str):
        """Create an edge between two nodes."""
        # Generate edge ID
        edge_id = f"e_{vertex_a_id}_{vertex_b_id}"

        # Check if edge already exists
        if edge_id in self.model.edges:
            return

        # Add to model
        if self.model.add_edge(edge_id, vertex_a_id, vertex_b_id):
            # Add to scene
            node_a = self.node_items[vertex_a_id]
            node_b = self.node_items[vertex_b_id]
            edge_data = self.model.get_edge(edge_id)

            edge_item = EdgeItem(edge_id, edge_data, node_a, node_b)
            self.scene.addItem(edge_item)
            self.scene.addItem(edge_item.label)
            self.edge_items[edge_id] = edge_item

            self.graph_modified.emit()

    def delete_edge(self, edge_id: str):
        """Delete an edge."""
        # Remove from scene
        edge_item = self.edge_items.get(edge_id)
        if edge_item:
            self.scene.removeItem(edge_item.label)
            self.scene.removeItem(edge_item)
            del self.edge_items[edge_id]

        # Remove from model
        self.model.delete_edge(edge_id)
        self.graph_modified.emit()

    # ========== Measurement Tools ==========

    def set_measurement_scale(self):
        """Set the pixels-per-meter scale for measurements."""
        value, ok = QInputDialog.getDouble(
            self, "Set Measurement Scale",
            "Enter pixels per meter:\n(e.g., if 100 pixels = 5 meters, enter 20)",
            value=self.pixels_per_meter,
            min=0.1,
            max=1000.0,
            decimals=2
        )
        if ok:
            self.pixels_per_meter = value

    def start_box_measurement(self):
        """Start box measurement mode for area estimation."""
        self.measurement_mode = 'box'
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.CrossCursor)

    def start_line_measurement(self):
        """Start line measurement mode for width estimation."""
        self.measurement_mode = 'line'
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.CrossCursor)

    def cancel_measurement(self):
        """Cancel measurement mode and clear measurement items."""
        self.measurement_mode = None
        self.measurement_start_pos = None
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setCursor(Qt.ArrowCursor)

        if self.measurement_item:
            self.scene.removeItem(self.measurement_item)
            self.measurement_item = None

        if self.measurement_label:
            self.scene.removeItem(self.measurement_label)
            self.measurement_label = None

    def apply_box_measurement(self):
        """Apply box measurement to selected node."""
        if not self.measurement_item or self.measurement_mode != 'box':
            return

        rect = self.measurement_item.rect()
        width_pixels = abs(rect.width())
        height_pixels = abs(rect.height())

        width_meters = width_pixels / self.pixels_per_meter
        height_meters = height_pixels / self.pixels_per_meter
        area = width_meters * height_meters

        # Check if node is selected
        selected = self.get_selected_item()
        if isinstance(selected, NodeItem):
            vertex_data = self.model.get_vertex(selected.vertex_id)
            if vertex_data:
                vertex_data['area'] = area
                selected.update_data(vertex_data)
                self.graph_modified.emit()
                # Re-emit selection to refresh property panel
                self.selection_changed.emit(selected)

        self.cancel_measurement()

    def apply_line_measurement(self):
        """Apply line measurement to selected edge."""
        if not self.measurement_item or self.measurement_mode != 'line':
            return

        line = self.measurement_item.line()
        length_pixels = ((line.x2() - line.x1())**2 + (line.y2() - line.y1())**2)**0.5
        length_meters = length_pixels / self.pixels_per_meter

        # Check if edge is selected
        selected = self.get_selected_item()
        if isinstance(selected, EdgeItem):
            edge_data = self.model.get_edge(selected.edge_id)
            if edge_data:
                edge_data['width'] = length_meters
                selected.update_data(edge_data)
                self.graph_modified.emit()
                # Re-emit selection to refresh property panel
                self.selection_changed.emit(selected)

        self.cancel_measurement()

    # ========== Auto-Hallway Generation ==========

    def auto_generate_hallway_segments(self):
        """
        Automatically generate hallway segments between intersection nodes.

        This tool:
        1. Identifies all edges connecting hallway/exit/stairwell nodes
        2. Calculates the distance between connected nodes
        3. Creates intermediate hallway nodes along long edges
        4. Splits edges into 1-meter segments
        """
        segments_created = 0
        edges_processed = 0

        # Get all edges to process
        edges_to_process = list(self.model.edges.items())

        for edge_id, edge_data in edges_to_process:
            vertex_a_id = edge_data['vertex_a']
            vertex_b_id = edge_data['vertex_b']

            # Get vertices
            vertex_a = self.model.get_vertex(vertex_a_id)
            vertex_b = self.model.get_vertex(vertex_b_id)

            if not vertex_a or not vertex_b:
                continue

            # Only process hallway-type connections
            type_a = vertex_a.get('type', '')
            type_b = vertex_b.get('type', '')

            if type_a not in ['hallway', 'exit', 'stairwell'] or type_b not in ['hallway', 'exit', 'stairwell']:
                continue

            # Get positions
            pos_a = vertex_a.get('visual_position', {})
            pos_b = vertex_b.get('visual_position', {})

            if 'x' not in pos_a or 'x' not in pos_b:
                continue

            # Calculate distance in grid units
            dx = pos_b['x'] - pos_a['x']
            dy = pos_b['y'] - pos_a['y']
            distance = (dx**2 + dy**2)**0.5

            # If distance > 1 unit, create intermediate nodes
            if distance > 1.5:  # Allow some tolerance
                edges_processed += 1

                # Calculate number of segments for 1m spacing
                # visual_position distance is in model units
                # For 1m per edge (vs old 5m), create 5x more segments
                num_segments = max(2, round(distance * 5))

                # Delete original edge
                self.model.delete_edge(edge_id)
                if edge_id in self.edge_items:
                    self.scene.removeItem(self.edge_items[edge_id].label)
                    self.scene.removeItem(self.edge_items[edge_id])
                    del self.edge_items[edge_id]

                # Create intermediate nodes
                prev_vertex_id = vertex_a_id

                for i in range(1, num_segments):
                    # Calculate intermediate position
                    t = i / num_segments
                    inter_x = pos_a['x'] + dx * t
                    inter_y = pos_a['y'] + dy * t

                    # Create intermediate hallway node
                    inter_id = f"hallway_{vertex_a_id}_{vertex_b_id}_{i}"
                    counter = 1
                    while inter_id in self.model.vertices:
                        inter_id = f"hallway_{vertex_a_id}_{vertex_b_id}_{i}_{counter}"
                        counter += 1

                    inter_data = {
                        'type': 'hallway',
                        'room_type': 'none',
                        'capacity': 50,
                        'priority': 1,
                        'sweep_time': 1,
                        'area': 30.0,
                        'visual_position': {'x': inter_x, 'y': inter_y}
                    }

                    self.model.add_vertex(inter_id, inter_data)

                    # Get vertex data from model (model creates a new dict, so we need its reference)
                    model_inter_data = self.model.get_vertex(inter_id)

                    # Create visual node with model's vertex data reference
                    node_item = NodeItem(inter_id, model_inter_data, inter_x * 100, inter_y * 100)
                    self.scene.addItem(node_item)
                    self.node_items[inter_id] = node_item

                    # Create edge from previous to this
                    new_edge_id = f"e_{prev_vertex_id}_{inter_id}"
                    new_edge_data = {
                        'vertex_a': prev_vertex_id,
                        'vertex_b': inter_id,
                        'max_flow': edge_data.get('max_flow', 10),
                        'base_burn_rate': edge_data.get('base_burn_rate', 0.0001),
                        'width': edge_data.get('width', 2.5)
                    }

                    self.model.add_edge(new_edge_id, prev_vertex_id, inter_id, new_edge_data)

                    # Create visual edge
                    node_a = self.node_items[prev_vertex_id]
                    node_b = self.node_items[inter_id]
                    edge_item = EdgeItem(new_edge_id, new_edge_data, node_a, node_b)
                    self.scene.addItem(edge_item)
                    self.scene.addItem(edge_item.label)
                    self.edge_items[new_edge_id] = edge_item

                    segments_created += 1
                    prev_vertex_id = inter_id

                # Create final edge to vertex_b
                final_edge_id = f"e_{prev_vertex_id}_{vertex_b_id}"
                final_edge_data = {
                    'vertex_a': prev_vertex_id,
                    'vertex_b': vertex_b_id,
                    'max_flow': edge_data.get('max_flow', 10),
                    'base_burn_rate': edge_data.get('base_burn_rate', 0.0001),
                    'width': edge_data.get('width', 2.5)
                }

                self.model.add_edge(final_edge_id, prev_vertex_id, vertex_b_id, final_edge_data)

                # Create visual edge
                node_a = self.node_items[prev_vertex_id]
                node_b = self.node_items[vertex_b_id]
                edge_item = EdgeItem(final_edge_id, final_edge_data, node_a, node_b)
                self.scene.addItem(edge_item)
                self.scene.addItem(edge_item.label)
                self.edge_items[final_edge_id] = edge_item

                segments_created += 1

        self.graph_modified.emit()
        print(f"Auto-Generate Complete: Processed {edges_processed} long edges, created {segments_created} hallway segments")

    def start_hallway_generation(self, node_item: NodeItem):
        """Start smart hallway generation from this intersection."""
        self.hallway_gen_start_intersection = node_item
        print(f"Hallway generation started from '{node_item.vertex_id}'. Right-click another intersection to complete.")

    def cancel_hallway_generation(self):
        """Cancel smart hallway generation."""
        self.hallway_gen_start_intersection = None

    def complete_hallway_generation(self, end_node: NodeItem):
        """Generate hallways between two intersections with manual hallway placement option."""
        if not self.hallway_gen_start_intersection:
            return

        start_node = self.hallway_gen_start_intersection
        self.hallway_gen_start_intersection = None

        # Get positions
        start_vertex = self.model.get_vertex(start_node.vertex_id)
        end_vertex = self.model.get_vertex(end_node.vertex_id)

        start_pos = start_vertex.get('visual_position', {})
        end_pos = end_vertex.get('visual_position', {})

        if 'x' not in start_pos or 'x' not in end_pos:
            QMessageBox.warning(self, "Error", "Missing position data")
            return

        # Calculate distance
        dx = end_pos['x'] - start_pos['x']
        dy = end_pos['y'] - start_pos['y']
        distance = (dx**2 + dy**2)**0.5

        # Ask for hallway width
        width, ok = QInputDialog.getDouble(
            self, "Hallway Width",
            "Enter hallway width (meters):",
            value=2.5, min=0.5, max=10.0, decimals=1
        )
        if not ok:
            return

        # Auto-generate intermediate nodes
        print(f"Generating hallway: distance = {distance:.2f} grid units")
        # For 1m per edge (vs old 5m), create proportionally more segments
        # Multiply by 5 to match 1m unit length
        num_segments = max(2, round(distance * 5))

        # Create intermediate hallway nodes
        prev_vertex_id = start_node.vertex_id

        for i in range(1, num_segments):
            # Calculate intermediate position
            t = i / num_segments
            inter_x = start_pos['x'] + dx * t
            inter_y = start_pos['y'] + dy * t

            # Create intermediate hallway node
            inter_id = f"hallway_{start_node.vertex_id}_{end_node.vertex_id}_{i}"
            counter = 1
            while inter_id in self.model.vertices:
                inter_id = f"hallway_{start_node.vertex_id}_{end_node.vertex_id}_{i}_{counter}"
                counter += 1

            inter_data = {
                'type': 'hallway',
                'room_type': 'none',
                'capacity': 50,
                'priority': 1,
                'sweep_time': 1,
                'area': 30.0,
                'visual_position': {'x': inter_x, 'y': inter_y}
            }

            self.model.add_vertex(inter_id, inter_data)

            # Create visual node
            node_item = NodeItem(inter_id, inter_data, inter_x * 100, inter_y * 100)
            self.scene.addItem(node_item)
            self.node_items[inter_id] = node_item

            # Create edge from previous to this
            new_edge_id = f"e_{prev_vertex_id}_{inter_id}"
            new_edge_data = {
                'vertex_a': prev_vertex_id,
                'vertex_b': inter_id,
                'max_flow': 10,
                'base_burn_rate': 0.0001,
                'width': width
            }

            self.model.add_edge(new_edge_id, prev_vertex_id, inter_id, new_edge_data)

            # Create visual edge
            node_a = self.node_items[prev_vertex_id]
            node_b = self.node_items[inter_id]
            edge_item = EdgeItem(new_edge_id, new_edge_data, node_a, node_b)
            self.scene.addItem(edge_item)
            self.scene.addItem(edge_item.label)
            self.edge_items[new_edge_id] = edge_item

            prev_vertex_id = inter_id

        # Create final edge to end intersection
        final_edge_id = f"e_{prev_vertex_id}_{end_node.vertex_id}"
        final_edge_data = {
            'vertex_a': prev_vertex_id,
            'vertex_b': end_node.vertex_id,
            'max_flow': 10,
            'base_burn_rate': 0.0001,
            'width': width
        }

        self.model.add_edge(final_edge_id, prev_vertex_id, end_node.vertex_id, final_edge_data)

        # Create visual edge
        node_a = self.node_items[prev_vertex_id]
        node_b = self.node_items[end_node.vertex_id]
        edge_item = EdgeItem(final_edge_id, final_edge_data, node_a, node_b)
        self.scene.addItem(edge_item)
        self.scene.addItem(edge_item.label)
        self.edge_items[final_edge_id] = edge_item

        self.graph_modified.emit()

    # ========== Selection ==========

    def on_selection_changed(self):
        """Handle selection changes."""
        selected_items = self.scene.selectedItems()

        if selected_items:
            item = selected_items[0]
            if isinstance(item, NodeItem) or isinstance(item, EdgeItem):
                self.selection_changed.emit(item)
            else:
                self.selection_changed.emit(None)
        else:
            self.selection_changed.emit(None)

    def get_selected_item(self):
        """Get currently selected item (NodeItem or EdgeItem)."""
        selected_items = self.scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            if isinstance(item, NodeItem) or isinstance(item, EdgeItem):
                return item
        return None

    # ========== Visual Scale Reference ==========

    def show_scale_reference(self):
        """Show visual reference ruler for measurement scale calibration."""
        self.scale_reference_visible = True
        self.update_scale_reference()

    def hide_scale_reference(self):
        """Hide visual reference ruler."""
        self.scale_reference_visible = False
        if self.scale_reference_line:
            self.scene.removeItem(self.scale_reference_line)
            self.scale_reference_line = None
        if self.scale_reference_label:
            self.scene.removeItem(self.scale_reference_label)
            self.scale_reference_label = None

    def update_scale_reference(self):
        """Update the visual reference ruler based on current measurement scale."""
        if not self.scale_reference_visible:
            return

        # Remove old reference
        if self.scale_reference_line:
            self.scene.removeItem(self.scale_reference_line)
        if self.scale_reference_label:
            self.scene.removeItem(self.scale_reference_label)

        # Calculate reference lengths
        # Show multiple reference lines: 1m, 5m, 10m
        reference_lengths = [1, 5, 10]  # meters

        # Get viewport center in scene coordinates
        viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        center_x = viewport_rect.center().x()
        center_y = viewport_rect.center().y()

        # Starting position for ruler (top-left of viewport)
        start_x = viewport_rect.left() + 50
        start_y = viewport_rect.top() + 50

        # Create ruler background
        from PyQt5.QtWidgets import QGraphicsRectItem
        ruler_height = 80
        ruler_width = 400

        ruler_bg = QGraphicsRectItem(start_x - 10, start_y - 10, ruler_width + 20, ruler_height + 20)
        ruler_bg.setBrush(QBrush(QColor(255, 255, 255, 230)))
        ruler_bg.setPen(QPen(QColor(100, 100, 100), 2))
        ruler_bg.setZValue(1000)  # Very high z-index
        self.scene.addItem(ruler_bg)

        # Store reference to remove later
        self.scale_reference_line = ruler_bg

        # Add title
        title = QGraphicsTextItem("Measurement Scale Reference", ruler_bg)
        title.setDefaultTextColor(QColor(0, 0, 0))
        title.setFont(QFont("Arial", 10, QFont.Bold))
        title.setPos(start_x, start_y - 5)

        # Draw reference lines
        y_pos = start_y + 25
        for length_meters in reference_lengths:
            length_pixels = length_meters * self.pixels_per_meter

            # Draw line
            line = QGraphicsLineItem(start_x, y_pos, start_x + length_pixels, y_pos, ruler_bg)
            line.setPen(QPen(QColor(255, 100, 0), 3))

            # Draw tick marks at ends
            tick_height = 8
            start_tick = QGraphicsLineItem(start_x, y_pos - tick_height, start_x, y_pos + tick_height, ruler_bg)
            start_tick.setPen(QPen(QColor(255, 100, 0), 2))

            end_tick = QGraphicsLineItem(start_x + length_pixels, y_pos - tick_height,
                                         start_x + length_pixels, y_pos + tick_height, ruler_bg)
            end_tick.setPen(QPen(QColor(255, 100, 0), 2))

            # Add label
            label = QGraphicsTextItem(f"{length_meters}m = {length_pixels:.0f}px", ruler_bg)
            label.setDefaultTextColor(QColor(0, 0, 0))
            label.setFont(QFont("Arial", 8))
            label.setPos(start_x + length_pixels + 10, y_pos - 10)

            y_pos += 20

    # ========== View Controls ==========

    def wheelEvent(self, event):
        """Handle mouse wheel for panning (vertical scroll)."""
        # Get scroll delta with reduced sensitivity
        delta = event.angleDelta()

        # Reduce sensitivity (divide by 3 for smoother scrolling)
        pan_amount = 15  # pixels per scroll tick

        # Vertical scrolling (up/down)
        if delta.y() != 0:
            # Pan vertically
            scroll_amount = delta.y() / 120.0 * pan_amount  # 120 units per "notch"
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(scroll_amount)
            )

        # Horizontal scrolling (if supported, e.g., Shift+Wheel or touchpad)
        if delta.x() != 0:
            scroll_amount = delta.x() / 120.0 * pan_amount
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(scroll_amount)
            )
