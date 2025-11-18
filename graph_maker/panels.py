#!/usr/bin/env python3
"""
Property panels for graph maker.

Provides PropertyPanel, OccupancyPanel, and StatsPanel for editing and viewing graph data.
"""

from typing import Optional, Dict
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
                              QComboBox, QDoubleSpinBox, QSpinBox, QPushButton,
                              QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QScrollArea, QFrame, QSlider)
from PyQt5.QtCore import Qt, pyqtSignal

from .models import GraphModel
from .items import NodeItem, EdgeItem
from .widgets import RangeControl


class PropertyPanel(QWidget):
    """Panel for editing vertex and edge properties."""

    property_changed = pyqtSignal()  # Emits when properties are modified

    def __init__(self, model: GraphModel):
        """Initialize property panel."""
        super().__init__()

        self.model = model
        self.current_item = None  # NodeItem or EdgeItem

        # Create UI
        self.init_ui()

    def init_ui(self):
        """Initialize UI elements."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title label
        self.title_label = QLabel("<b>Properties</b>")
        layout.addWidget(self.title_label)

        # Vertex properties group
        self.vertex_group = QGroupBox("Vertex Properties")
        self.vertex_form = QFormLayout()
        self.vertex_group.setLayout(self.vertex_form)
        layout.addWidget(self.vertex_group)

        # Vertex fields
        self.vertex_id_label = QLabel("")
        self.vertex_form.addRow("ID:", self.vertex_id_label)

        self.vertex_type_combo = QComboBox()
        self.vertex_type_combo.addItems(['room', 'hallway', 'intersection', 'stairwell', 'exit'])
        self.vertex_type_combo.currentTextChanged.connect(self.on_vertex_property_changed)
        self.vertex_form.addRow("Type:", self.vertex_type_combo)

        self.room_type_edit = QLineEdit()
        self.room_type_edit.textChanged.connect(self.on_vertex_property_changed)
        self.vertex_form.addRow("Room Type:", self.room_type_edit)

        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 10000)
        self.capacity_spin.valueChanged.connect(self.on_vertex_property_changed)
        self.vertex_form.addRow("Capacity:", self.capacity_spin)

        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 10)
        self.priority_spin.valueChanged.connect(self.on_vertex_property_changed)
        self.vertex_form.addRow("Priority:", self.priority_spin)

        self.sweep_time_spin = QSpinBox()
        self.sweep_time_spin.setRange(0, 100)
        self.sweep_time_spin.valueChanged.connect(self.on_vertex_property_changed)
        self.vertex_form.addRow("Sweep Time:", self.sweep_time_spin)

        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(1.0, 10000.0)
        self.area_spin.setSingleStep(10.0)
        self.area_spin.valueChanged.connect(self.on_vertex_property_changed)
        self.vertex_form.addRow("Area (m²):", self.area_spin)

        self.floor_spin = QSpinBox()
        self.floor_spin.setRange(1, 100)
        self.floor_spin.valueChanged.connect(self.on_vertex_property_changed)
        self.vertex_form.addRow("Floor:", self.floor_spin)

        # Position display (read-only)
        self.position_label = QLabel("")
        self.vertex_form.addRow("Position:", self.position_label)

        # Edge properties group
        self.edge_group = QGroupBox("Edge Properties")
        self.edge_form = QFormLayout()
        self.edge_group.setLayout(self.edge_form)
        layout.addWidget(self.edge_group)

        # Edge fields
        self.edge_id_label = QLabel("")
        self.edge_form.addRow("ID:", self.edge_id_label)

        self.edge_vertices_label = QLabel("")
        self.edge_form.addRow("Connects:", self.edge_vertices_label)

        self.max_flow_spin = QSpinBox()
        self.max_flow_spin.setRange(1, 1000)
        self.max_flow_spin.valueChanged.connect(self.on_edge_property_changed)
        self.edge_form.addRow("Max Flow:", self.max_flow_spin)

        self.burn_rate_spin = QDoubleSpinBox()
        self.burn_rate_spin.setRange(0.0001, 0.1)
        self.burn_rate_spin.setSingleStep(0.0001)
        self.burn_rate_spin.setDecimals(4)
        self.burn_rate_spin.valueChanged.connect(self.on_edge_property_changed)
        self.edge_form.addRow("Burn Rate:", self.burn_rate_spin)

        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.5, 10.0)
        self.width_spin.setSingleStep(0.5)
        self.width_spin.valueChanged.connect(self.on_edge_property_changed)
        self.edge_form.addRow("Width (m):", self.width_spin)

        # Initially hide both groups
        self.vertex_group.hide()
        self.edge_group.hide()

        layout.addStretch()

    def set_item(self, item):
        """
        Set the current item to edit.

        Args:
            item: NodeItem, EdgeItem, or None
        """
        self.current_item = item

        # Hide all groups initially
        self.vertex_group.hide()
        self.edge_group.hide()

        if isinstance(item, NodeItem):
            self.load_vertex_properties(item)
            self.vertex_group.show()
            self.title_label.setText(f"<b>Node: {item.vertex_id}</b>")

        elif isinstance(item, EdgeItem):
            self.load_edge_properties(item)
            self.edge_group.show()
            self.title_label.setText(f"<b>Edge: {item.edge_id}</b>")

        else:
            self.title_label.setText("<b>Properties</b>")

    def load_vertex_properties(self, node_item: NodeItem):
        """Load vertex properties into form."""
        data = node_item.vertex_data

        # Block signals while loading
        self.vertex_type_combo.blockSignals(True)
        self.room_type_edit.blockSignals(True)
        self.capacity_spin.blockSignals(True)
        self.priority_spin.blockSignals(True)
        self.sweep_time_spin.blockSignals(True)
        self.area_spin.blockSignals(True)
        self.floor_spin.blockSignals(True)

        self.vertex_id_label.setText(node_item.vertex_id)
        self.vertex_type_combo.setCurrentText(data.get('type', 'room'))
        self.room_type_edit.setText(data.get('room_type', 'office'))
        self.capacity_spin.setValue(data.get('capacity', 20))
        self.priority_spin.setValue(data.get('priority', 2))
        self.sweep_time_spin.setValue(data.get('sweep_time', 2))
        self.area_spin.setValue(data.get('area', 100.0))
        self.floor_spin.setValue(data.get('floor', 1))

        pos = data.get('visual_position', {})
        pos_text = f"({pos.get('x', 0):.2f}, {pos.get('y', 0):.2f})"
        self.position_label.setText(pos_text)

        # Unblock signals
        self.vertex_type_combo.blockSignals(False)
        self.room_type_edit.blockSignals(False)
        self.capacity_spin.blockSignals(False)
        self.priority_spin.blockSignals(False)
        self.sweep_time_spin.blockSignals(False)
        self.area_spin.blockSignals(False)
        self.floor_spin.blockSignals(False)

    def update_position_display(self):
        """Update only the position label for current item."""
        if isinstance(self.current_item, NodeItem):
            data = self.current_item.vertex_data
            pos = data.get('visual_position', {})
            pos_text = f"({pos.get('x', 0):.2f}, {pos.get('y', 0):.2f})"
            self.position_label.setText(pos_text)

    def load_edge_properties(self, edge_item: EdgeItem):
        """Load edge properties into form."""
        data = edge_item.edge_data

        # Block signals while loading
        self.max_flow_spin.blockSignals(True)
        self.burn_rate_spin.blockSignals(True)
        self.width_spin.blockSignals(True)

        self.edge_id_label.setText(edge_item.edge_id)
        self.edge_vertices_label.setText(f"{data['vertex_a']} ↔ {data['vertex_b']}")
        self.max_flow_spin.setValue(data.get('max_flow', 10))
        self.burn_rate_spin.setValue(data.get('base_burn_rate', 0.0002))
        self.width_spin.setValue(data.get('width', 2.0))

        # Unblock signals
        self.max_flow_spin.blockSignals(False)
        self.burn_rate_spin.blockSignals(False)
        self.width_spin.blockSignals(False)

    def on_vertex_property_changed(self):
        """Handle vertex property changes."""
        if not isinstance(self.current_item, NodeItem):
            return

        # Update vertex data
        vertex_id = self.current_item.vertex_id
        vertex_data = self.model.get_vertex(vertex_id)

        if not vertex_data:
            return

        vertex_data['type'] = self.vertex_type_combo.currentText()
        vertex_data['room_type'] = self.room_type_edit.text()
        vertex_data['capacity'] = self.capacity_spin.value()
        vertex_data['priority'] = self.priority_spin.value()
        vertex_data['sweep_time'] = self.sweep_time_spin.value()
        vertex_data['area'] = self.area_spin.value()
        vertex_data['floor'] = self.floor_spin.value()

        # Update visual item
        self.current_item.update_data(vertex_data)

        self.property_changed.emit()

    def on_edge_property_changed(self):
        """Handle edge property changes."""
        if not isinstance(self.current_item, EdgeItem):
            return

        # Update edge data
        edge_id = self.current_item.edge_id
        edge_data = self.model.get_edge(edge_id)

        if not edge_data:
            return

        edge_data['max_flow'] = self.max_flow_spin.value()
        edge_data['base_burn_rate'] = self.burn_rate_spin.value()
        edge_data['width'] = self.width_spin.value()

        # Update visual item
        self.current_item.update_data(edge_data)

        self.property_changed.emit()


class OccupancyPanel(QWidget):
    """Panel for editing occupancy ranges with dual-range sliders."""

    occupancy_changed = pyqtSignal()  # Emits when occupancy is modified

    def __init__(self, model: GraphModel):
        """Initialize occupancy panel."""
        super().__init__()

        self.model = model
        self.room_widgets = {}  # Store widget references for each room

        # Create UI
        self.init_ui()

    def init_ui(self):
        """Initialize UI elements."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Title
        title = QLabel("<b>Occupancy Ranges</b>")
        main_layout.addWidget(title)

        # Description
        desc = QLabel("Set min-max occupant ranges per room. Each simulation run will randomly select a value within the range (uniform distribution).")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Auto-calculate button
        auto_btn = QPushButton("Auto-Calculate Defaults (Based on Room Area)")
        auto_btn.clicked.connect(self.auto_calculate_defaults)
        main_layout.addWidget(auto_btn)

        # Scroll area for room settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        self.rooms_layout = QVBoxLayout()
        scroll_widget.setLayout(self.rooms_layout)
        scroll.setWidget(scroll_widget)

        main_layout.addWidget(scroll)

        # Refresh button
        refresh_btn = QPushButton("Refresh from Model")
        refresh_btn.clicked.connect(self.refresh_all)
        main_layout.addWidget(refresh_btn)

    def refresh_all(self):
        """Rebuild the entire panel with current model data."""
        # Clear existing widgets
        while self.rooms_layout.count():
            child = self.rooms_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.room_widgets.clear()

        # Get all rooms sorted by ID
        rooms = sorted([(vid, vdata) for vid, vdata in self.model.vertices.items()
                       if vdata.get('type') == 'room'],
                      key=lambda x: x[0])

        # Create widget for each room
        for vertex_id, vertex_data in rooms:
            room_widget = self.create_room_widget(vertex_id, vertex_data)
            self.rooms_layout.addWidget(room_widget)

        # Add stretch at the end
        self.rooms_layout.addStretch()

    def create_room_widget(self, vertex_id: str, vertex_data: dict) -> QWidget:
        """Create a widget for editing one room's occupancy."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box | QFrame.Raised)
        widget.setLineWidth(1)

        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Room header
        area = vertex_data.get('area', 100.0)
        capacity = vertex_data.get('capacity', 50)
        header = QLabel(f"<b>{vertex_id}</b> ({area:.1f} m², capacity: {capacity})")
        layout.addWidget(header)

        # Get current ranges
        ranges = self.model.get_occupancy_range(vertex_id)
        if ranges:
            capable_min = ranges['capable']['min']
            capable_max = ranges['capable']['max']
            incapable_min = ranges['incapable']['min']
            incapable_max = ranges['incapable']['max']
        else:
            capable_min = capable_max = 0
            incapable_min = incapable_max = 0

        # Capable occupants section
        capable_label = QLabel("Capable occupants (count range):")
        layout.addWidget(capable_label)

        capable_control = RangeControl(minimum=0, maximum=capacity)
        capable_control.setRange(capable_min, capable_max)
        layout.addWidget(capable_control)

        # Incapable occupants section
        incapable_label = QLabel("Incapable occupants (count range):")
        layout.addWidget(incapable_label)

        incapable_control = RangeControl(minimum=0, maximum=capacity)
        incapable_control.setRange(incapable_min, incapable_max)
        layout.addWidget(incapable_control)

        # Store references
        self.room_widgets[vertex_id] = {
            'capable_control': capable_control,
            'incapable_control': incapable_control,
            'area': area,
            'capacity': capacity
        }

        # Connect change handlers (use functools.partial to avoid lambda capture issues)
        from functools import partial
        capable_control.rangeChanged.connect(partial(self.on_range_changed, vertex_id))
        incapable_control.rangeChanged.connect(partial(self.on_range_changed, vertex_id))

        return widget

    def on_range_changed(self, vertex_id: str, min_val=None, max_val=None):
        """Handle range changes."""
        # Get current values
        widgets = self.room_widgets.get(vertex_id)
        if not widgets:
            return

        capable_min = widgets['capable_control'].minValue()
        capable_max = widgets['capable_control'].maxValue()
        incapable_min = widgets['incapable_control'].minValue()
        incapable_max = widgets['incapable_control'].maxValue()

        # Update model
        self.model.set_occupancy_range(
            vertex_id,
            capable_min, capable_max,
            incapable_min, incapable_max
        )
        self.occupancy_changed.emit()

    def auto_calculate_defaults(self):
        """Auto-calculate default ranges based on room areas."""
        print("DEBUG: auto_calculate_defaults called")

        # Ask for confirmation
        try:
            print("DEBUG: Showing confirmation dialog")
            reply = QMessageBox.question(
                self,
                "Auto-Calculate Defaults",
                "This will set occupancy ranges based on room areas:\n\n"
                "• Capable: scaled by area (e.g., 10m² → 0-1, 50m² → 1-4, 100m² → 3-8)\n"
                "• Incapable: set to 0-0 (no incapable occupants)\n\n"
                "Formula: ~12-30 m² per person (conservative occupancy)\n\n"
                "This will overwrite existing values. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            print(f"DEBUG: Dialog result: {reply}")

            if reply != QMessageBox.Yes:
                print("DEBUG: User cancelled")
                return

            # Calculate and apply defaults
            print(f"DEBUG: Processing {len(self.room_widgets)} rooms")

            for i, (vertex_id, widgets) in enumerate(self.room_widgets.items()):
                print(f"DEBUG: Processing room {i+1}/{len(self.room_widgets)}: {vertex_id}")

                try:
                    area = widgets['area']
                    capacity = widgets['capacity']
                    print(f"  Area: {area}, Capacity: {capacity}")

                    # Calculate capable range based on area
                    # Formula: conservative occupancy ~12-30 m² per person
                    # min = area / 30 (sparse), max = area / 12 (moderate density)
                    capable_min = max(0, int(area / 30))
                    capable_max = min(capacity, max(capable_min, int(area / 12)))
                    print(f"  Calculated capable range: {capable_min}-{capable_max}")

                    # Incapable defaults to 0-0
                    incapable_min = 0
                    incapable_max = 0

                    # Block signals temporarily to avoid cascading updates
                    print(f"  Blocking signals")
                    widgets['capable_control'].blockSignals(True)
                    widgets['incapable_control'].blockSignals(True)

                    # Update controls
                    print(f"  Setting capable range: {capable_min}-{capable_max}")
                    widgets['capable_control'].setRange(capable_min, capable_max)

                    print(f"  Setting incapable range: {incapable_min}-{incapable_max}")
                    widgets['incapable_control'].setRange(incapable_min, incapable_max)

                    # Unblock signals
                    print(f"  Unblocking signals")
                    widgets['capable_control'].blockSignals(False)
                    widgets['incapable_control'].blockSignals(False)

                    # Update model directly
                    print(f"  Updating model")
                    self.model.set_occupancy_range(
                        vertex_id,
                        capable_min, capable_max,
                        incapable_min, incapable_max
                    )
                    print(f"  Room {vertex_id} done")

                except Exception as e:
                    print(f"ERROR processing room {vertex_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(self, "Error", f"Error processing room {vertex_id}:\n{e}")
                    return

            # Emit signal once after all updates
            print("DEBUG: Emitting occupancy_changed signal")
            self.occupancy_changed.emit()

            print("DEBUG: Showing success message")
            QMessageBox.information(
                self,
                "Defaults Applied",
                f"Default occupancy ranges applied to {len(self.room_widgets)} rooms."
            )
            print("DEBUG: auto_calculate_defaults completed successfully")

        except Exception as e:
            print(f"ERROR in auto_calculate_defaults: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Unexpected error:\n{e}")


class StatsPanel(QWidget):
    """Panel for displaying graph statistics."""

    def __init__(self, model: GraphModel):
        """Initialize stats panel."""
        super().__init__()

        self.model = model

        # Create UI
        self.init_ui()

    def init_ui(self):
        """Initialize UI elements."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("<b>Graph Statistics</b>")
        layout.addWidget(title)

        # Stats labels
        self.vertices_label = QLabel("Vertices: 0")
        layout.addWidget(self.vertices_label)

        self.edges_label = QLabel("Edges: 0")
        layout.addWidget(self.edges_label)

        self.vertex_types_label = QLabel("")
        layout.addWidget(self.vertex_types_label)

        self.occupants_label = QLabel("Expected Occupants: 0.0")
        layout.addWidget(self.occupants_label)

        self.fire_origin_label = QLabel("Fire Origin: None")
        layout.addWidget(self.fire_origin_label)

        # Firefighter section
        firefighter_title = QLabel("<b>Firefighters</b>")
        layout.addWidget(firefighter_title)

        # Number of firefighters
        ff_num_layout = QHBoxLayout()
        ff_num_label = QLabel("Number:")
        self.ff_num_spin = QSpinBox()
        self.ff_num_spin.setMinimum(1)
        self.ff_num_spin.setMaximum(20)
        self.ff_num_spin.setValue(self.model.num_firefighters)
        self.ff_num_spin.valueChanged.connect(self.on_ff_num_changed)
        ff_num_layout.addWidget(ff_num_label)
        ff_num_layout.addWidget(self.ff_num_spin)
        layout.addLayout(ff_num_layout)

        self.ff_spawn_label = QLabel("Spawn: Auto (at exits)")
        layout.addWidget(self.ff_spawn_label)

        # Validation section
        validation_title = QLabel("<b>Validation</b>")
        layout.addWidget(validation_title)

        self.validation_label = QLabel("")
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        # Validate button
        validate_btn = QPushButton("Validate Graph")
        validate_btn.clicked.connect(self.run_validation)
        layout.addWidget(validate_btn)

        layout.addStretch()

    def refresh_stats(self):
        """Refresh statistics from model."""
        stats = self.model.get_stats()

        self.vertices_label.setText(f"Vertices: {stats['num_vertices']}")
        self.edges_label.setText(f"Edges: {stats['num_edges']}")

        # Vertex types breakdown
        types_text = "Types: " + ", ".join([f"{k}={v}" for k, v in stats['vertex_types'].items()])
        self.vertex_types_label.setText(types_text)

        self.occupants_label.setText(f"Expected Occupants: {stats['expected_occupants']:.1f}")

        fire_origin = self.model.fire_origin if self.model.fire_origin else "None"
        self.fire_origin_label.setText(f"Fire Origin: {fire_origin}")

        # Update firefighter info
        self.ff_num_spin.setValue(self.model.num_firefighters)
        if self.model.firefighter_spawn_vertices:
            spawn_text = "Spawn: " + ", ".join(self.model.firefighter_spawn_vertices[:3])
            if len(self.model.firefighter_spawn_vertices) > 3:
                spawn_text += "..."
            self.ff_spawn_label.setText(spawn_text)
        else:
            self.ff_spawn_label.setText("Spawn: Auto (at exits)")

    def on_ff_num_changed(self, value):
        """Handle firefighter number change."""
        self.model.num_firefighters = value

    def run_validation(self):
        """Run validation and display results."""
        is_valid, errors = self.model.validate()

        if is_valid:
            self.validation_label.setText("✓ Graph is valid!")
            self.validation_label.setStyleSheet("color: green;")
        else:
            error_text = "✗ Validation errors:\n" + "\n".join([f"• {e}" for e in errors])
            self.validation_label.setText(error_text)
            self.validation_label.setStyleSheet("color: red;")
