#!/usr/bin/env python3
"""
Main window for graph maker application.

Provides menu bar, layout, and orchestrates canvas and panels.
"""

import json
from typing import Optional
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QSplitter, QMenuBar, QAction, QFileDialog,
                              QMessageBox, QInputDialog, QTabWidget, QDialog,
                              QTextEdit, QPushButton, QDialogButtonBox, QSlider,
                              QLabel, QToolBar, QGraphicsLineItem, QGraphicsTextItem,
                              QComboBox, QSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QColor, QFont

from .models import GraphModel
from .canvas import GraphCanvas
from .panels import PropertyPanel, OccupancyPanel, StatsPanel


class MainWindow(QMainWindow):
    """Main application window for graph maker."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()

        self.model = GraphModel()
        self.current_file_path: Optional[str] = None

        # Set window properties
        self.setWindowTitle("Building Evacuation Graph Maker")
        self.setGeometry(100, 100, 1400, 800)

        # Create UI
        self.init_ui()

    def init_ui(self):
        """Initialize UI elements."""
        # Create menu bar
        self.create_menu_bar()

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left side: Canvas with scale controls
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        self.canvas = GraphCanvas(self.model)
        self.canvas.selection_changed.connect(self.on_canvas_selection_changed)
        self.canvas.graph_modified.connect(self.on_graph_modified)
        self.canvas.node_position_changed.connect(self.on_node_position_changed)
        left_layout.addWidget(self.canvas)

        # Add control panel at bottom
        control_layout = QHBoxLayout()

        # Zoom control
        control_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)  # 10% zoom
        self.zoom_slider.setMaximum(400)  # 400% zoom
        self.zoom_slider.setValue(100)  # 100% default
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.setTickInterval(50)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        self.zoom_slider.setMaximumWidth(200)
        control_layout.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        control_layout.addWidget(self.zoom_label)

        control_layout.addWidget(QLabel(" | "))  # Separator

        # Measurement scale control
        control_layout.addWidget(QLabel("Measurement Scale:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(5)  # 5 pixels/meter
        self.scale_slider.setMaximum(100)  # 100 pixels/meter
        self.scale_slider.setValue(20)  # 20 default (same as canvas.pixels_per_meter)
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_slider.setTickInterval(10)
        self.scale_slider.valueChanged.connect(self.on_measurement_scale_changed)
        self.scale_slider.sliderPressed.connect(self.on_measurement_scale_pressed)
        self.scale_slider.sliderReleased.connect(self.on_measurement_scale_released)
        self.scale_slider.setMaximumWidth(200)
        control_layout.addWidget(self.scale_slider)

        self.scale_label = QLabel("20 px/m")
        self.scale_label.setMinimumWidth(70)
        control_layout.addWidget(self.scale_label)

        # Visual indicator
        self.scale_indicator_label = QLabel("(100px = 5m)")
        control_layout.addWidget(self.scale_indicator_label)

        control_layout.addWidget(QLabel(" | "))  # Separator

        # Floor selector
        control_layout.addWidget(QLabel("Floor:"))
        self.floor_selector = QComboBox()
        self.floor_selector.addItem("Floor 1")
        self.floor_selector.currentIndexChanged.connect(self.on_floor_changed)
        control_layout.addWidget(self.floor_selector)

        # Add/Remove floor buttons
        add_floor_btn = QPushButton("+")
        add_floor_btn.setMaximumWidth(30)
        add_floor_btn.setToolTip("Add new floor")
        add_floor_btn.clicked.connect(self.add_floor)
        control_layout.addWidget(add_floor_btn)

        remove_floor_btn = QPushButton("-")
        remove_floor_btn.setMaximumWidth(30)
        remove_floor_btn.setToolTip("Remove current floor")
        remove_floor_btn.clicked.connect(self.remove_floor)
        control_layout.addWidget(remove_floor_btn)

        # Duplicate floor button
        duplicate_floor_btn = QPushButton("Duplicate")
        duplicate_floor_btn.setToolTip("Duplicate layout from another floor")
        duplicate_floor_btn.clicked.connect(self.duplicate_from_floor)
        control_layout.addWidget(duplicate_floor_btn)

        control_layout.addStretch()
        left_layout.addLayout(control_layout)

        splitter.addWidget(left_widget)

        # Right side: Tab widget with panels
        tab_widget = QTabWidget()
        splitter.addWidget(tab_widget)

        # Property panel
        self.property_panel = PropertyPanel(self.model)
        self.property_panel.property_changed.connect(self.on_graph_modified)
        tab_widget.addTab(self.property_panel, "Properties")

        # Occupancy panel
        self.occupancy_panel = OccupancyPanel(self.model)
        self.occupancy_panel.occupancy_changed.connect(self.on_graph_modified)
        tab_widget.addTab(self.occupancy_panel, "Occupancy")

        # Stats panel
        self.stats_panel = StatsPanel(self.model)
        tab_widget.addTab(self.stats_panel, "Statistics")

        # Set splitter proportions (70% canvas, 30% panels)
        splitter.setSizes([1000, 400])

    def create_menu_bar(self):
        """Create menu bar with actions."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        export_action = QAction("&Export Config...", self)
        export_action.triggered.connect(self.export_config)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        delete_action = QAction("&Delete Selected", self)
        delete_action.setShortcut("Del")
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        background_action = QAction("Load &Background Image...", self)
        background_action.triggered.connect(self.load_background_image)
        view_menu.addAction(background_action)

        opacity_action = QAction("Set Background &Opacity...", self)
        opacity_action.triggered.connect(self.set_background_opacity)
        view_menu.addAction(opacity_action)

        view_menu.addSeparator()

        refresh_action = QAction("&Refresh All", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all_panels)
        view_menu.addAction(refresh_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        validate_action = QAction("&Validate Graph", self)
        validate_action.triggered.connect(self.validate_graph)
        tools_menu.addAction(validate_action)

        test_action = QAction("&Quick Test Simulation...", self)
        test_action.setShortcut("Ctrl+T")
        test_action.triggered.connect(self.quick_test_simulation)
        tools_menu.addAction(test_action)

        tools_menu.addSeparator()

        # Measurement tools
        measure_menu = tools_menu.addMenu("&Measurement Tools")

        scale_action = QAction("Set &Scale...", measure_menu)
        scale_action.triggered.connect(lambda: self.canvas.set_measurement_scale())
        measure_menu.addAction(scale_action)

        measure_menu.addSeparator()

        box_action = QAction("&Box Tool (Area)", measure_menu)
        box_action.setShortcut("Ctrl+B")
        box_action.triggered.connect(lambda: self.canvas.start_box_measurement())
        measure_menu.addAction(box_action)

        line_action = QAction("&Line Tool (Width)", measure_menu)
        line_action.setShortcut("Ctrl+L")
        line_action.triggered.connect(lambda: self.canvas.start_line_measurement())
        measure_menu.addAction(line_action)

        cancel_measure_action = QAction("&Cancel Measurement", measure_menu)
        cancel_measure_action.setShortcut("Esc")
        cancel_measure_action.triggered.connect(lambda: self.canvas.cancel_measurement())
        measure_menu.addAction(cancel_measure_action)

        tools_menu.addSeparator()

        # Auto-generation tools
        auto_hallway_action = QAction("Auto-Generate &Hallway Segments", self)
        auto_hallway_action.setShortcut("Ctrl+H")
        auto_hallway_action.triggered.connect(lambda: self.canvas.auto_generate_hallway_segments())
        tools_menu.addAction(auto_hallway_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # ========== File Operations ==========

    def new_file(self):
        """Create a new graph."""
        # Confirm if unsaved changes
        if len(self.model.vertices) > 0:
            reply = QMessageBox.question(
                self, "New File",
                "Create new graph? Current work will be lost if not saved.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Reset model
        self.model = GraphModel()
        self.canvas.model = self.model
        self.property_panel.model = self.model
        self.occupancy_panel.model = self.model
        self.stats_panel.model = self.model

        # Refresh canvas
        self.canvas.refresh_from_model()
        self.refresh_all_panels()

        self.current_file_path = None
        self.setWindowTitle("Building Evacuation Graph Maker - New File")

    def open_file(self):
        """Open an existing graph file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Graph File", "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not filepath:
            return

        if self.model.load_from_file(filepath):
            self.canvas.refresh_from_model()
            self.refresh_all_panels()
            self.current_file_path = filepath
            self.setWindowTitle(f"Building Evacuation Graph Maker - {filepath}")
            QMessageBox.information(self, "Success", f"Loaded: {filepath}")
        else:
            QMessageBox.warning(self, "Error", f"Failed to load: {filepath}")

    def save_file(self):
        """Save to current file or prompt for new file."""
        if self.current_file_path:
            if self.model.save_to_file(self.current_file_path):
                QMessageBox.information(self, "Success", f"Saved: {self.current_file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save file")
        else:
            self.save_file_as()

    def save_file_as(self):
        """Save to a new file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Graph File", "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not filepath:
            return

        if self.model.save_to_file(filepath):
            self.current_file_path = filepath
            self.setWindowTitle(f"Building Evacuation Graph Maker - {filepath}")
            QMessageBox.information(self, "Success", f"Saved: {filepath}")
        else:
            QMessageBox.warning(self, "Error", "Failed to save file")

    def export_config(self):
        """Export as simulation config file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Config", "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not filepath:
            return

        # Validate before export
        is_valid, errors = self.model.validate()
        if not is_valid:
            reply = QMessageBox.question(
                self, "Validation Errors",
                f"Graph has validation errors:\n" + "\n".join(errors) + "\n\nExport anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Export
        if self.model.save_to_file(filepath):
            QMessageBox.information(self, "Success", f"Exported config: {filepath}")
        else:
            QMessageBox.warning(self, "Error", "Failed to export config")

    # ========== Edit Operations ==========

    def delete_selected(self):
        """Delete selected item."""
        selected_item = self.canvas.get_selected_item()

        if not selected_item:
            QMessageBox.information(self, "Delete", "No item selected")
            return

        from .items import NodeItem, EdgeItem

        if isinstance(selected_item, NodeItem):
            self.canvas.delete_node(selected_item.vertex_id)
        elif isinstance(selected_item, EdgeItem):
            self.canvas.delete_edge(selected_item.edge_id)

    # ========== View Operations ==========

    def load_background_image(self):
        """Load a background image."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load Background Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )

        if not filepath:
            return

        # Get opacity
        opacity, ok = QInputDialog.getDouble(
            self, "Background Opacity",
            "Enter opacity (0.0 - 1.0):",
            value=0.5, min=0.0, max=1.0, decimals=2
        )

        if not ok:
            opacity = 0.5

        self.canvas.load_background_image(filepath, opacity)

    def set_background_opacity(self):
        """Change background image opacity."""
        if not self.canvas.background_pixmap_item:
            QMessageBox.information(self, "No Background", "No background image loaded")
            return

        opacity, ok = QInputDialog.getDouble(
            self, "Background Opacity",
            "Enter opacity (0.0 - 1.0):",
            value=self.model.background_opacity, min=0.0, max=1.0, decimals=2
        )

        if ok:
            self.canvas.set_background_opacity(opacity)

    def refresh_all_panels(self):
        """Refresh all panels."""
        self.occupancy_panel.refresh_all()
        self.stats_panel.refresh_stats()

    # ========== Tools ==========

    def validate_graph(self):
        """Run validation and show results."""
        self.stats_panel.run_validation()

    def quick_test_simulation(self):
        """Run a quick test simulation with current graph."""
        # Validate first
        is_valid, errors = self.model.validate()
        if not is_valid:
            QMessageBox.warning(
                self, "Validation Failed",
                "Cannot run simulation. Fix validation errors first:\n" + "\n".join(errors)
            )
            return

        # Show test dialog
        dialog = TestSimulationDialog(self.model, self)
        dialog.exec_()

    # ========== Event Handlers ==========

    def on_canvas_selection_changed(self, item):
        """Handle canvas selection changes."""
        self.property_panel.set_item(item)

    def on_graph_modified(self):
        """Handle graph modifications."""
        self.refresh_all_panels()

    def on_node_position_changed(self, vertex_id):
        """Handle node position changes (update property panel in real-time)."""
        # Only update if this is the currently selected node
        current_item = self.property_panel.current_item
        if hasattr(current_item, 'vertex_id') and current_item.vertex_id == vertex_id:
            self.property_panel.update_position_display()

    def on_zoom_changed(self, value):
        """Handle zoom slider changes."""
        # Update zoom label
        self.zoom_label.setText(f"{value}%")

        # Apply zoom to canvas
        zoom_factor = value / 100.0

        # Reset transform and apply new zoom
        self.canvas.resetTransform()
        self.canvas.scale(zoom_factor, zoom_factor)

    def on_measurement_scale_pressed(self):
        """Handle when measurement scale slider is pressed - show reference."""
        self.canvas.show_scale_reference()

    def on_floor_changed(self, index):
        """Handle floor selector changes."""
        new_floor = index + 1  # Convert 0-indexed to 1-indexed
        self.model.current_floor = new_floor

        # Refresh canvas to show only nodes/edges on this floor
        self.canvas.refresh_for_floor(new_floor)
        self.on_graph_modified()

    def add_floor(self):
        """Add a new floor to the building."""
        self.model.num_floors += 1
        new_floor = self.model.num_floors

        # Add to selector
        self.floor_selector.addItem(f"Floor {new_floor}")

        # Switch to new floor
        self.floor_selector.setCurrentIndex(new_floor - 1)

        QMessageBox.information(
            self, "Floor Added",
            f"Floor {new_floor} added. You can now add nodes to this floor."
        )

    def remove_floor(self):
        """Remove the current floor (if not the only floor)."""
        if self.model.num_floors <= 1:
            QMessageBox.warning(
                self, "Cannot Remove",
                "Cannot remove the only floor. Building must have at least one floor."
            )
            return

        current_floor = self.model.current_floor

        # Check if floor has any nodes
        floor_vertices = self.model.get_vertices_on_floor(current_floor)
        if floor_vertices:
            reply = QMessageBox.question(
                self, "Confirm Deletion",
                f"Floor {current_floor} has {len(floor_vertices)} nodes. Delete them all?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

            # Delete all vertices on this floor
            for vertex_id in list(floor_vertices.keys()):
                self.model.delete_vertex(vertex_id)

        # Remove from model
        self.model.num_floors -= 1

        # Update selector
        self.floor_selector.removeItem(current_floor - 1)

        # Switch to floor 1
        self.floor_selector.setCurrentIndex(0)

        self.on_graph_modified()

    def duplicate_from_floor(self):
        """Duplicate layout from another floor to current floor."""
        current_floor = self.model.current_floor

        # Get list of available source floors (excluding current)
        source_floors = [f for f in range(1, self.model.num_floors + 1) if f != current_floor]

        if not source_floors:
            QMessageBox.information(
                self, "No Source Floor",
                "No other floors available to duplicate from."
            )
            return

        # Ask user which floor to duplicate from
        floor_names = [f"Floor {f}" for f in source_floors]
        source_floor_name, ok = QInputDialog.getItem(
            self, "Duplicate Floor",
            "Select floor to duplicate from:",
            floor_names, 0, False
        )

        if not ok:
            return

        source_floor = source_floors[floor_names.index(source_floor_name)]

        # Confirm if current floor has nodes
        current_vertices = self.model.get_vertices_on_floor(current_floor)
        if current_vertices:
            reply = QMessageBox.question(
                self, "Overwrite Existing",
                f"Floor {current_floor} has {len(current_vertices)} nodes. Overwrite?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

            # Delete existing nodes on current floor
            for vertex_id in list(current_vertices.keys()):
                self.model.delete_vertex(vertex_id)

        # Copy vertices from source floor
        source_vertices = self.model.get_vertices_on_floor(source_floor)
        vertex_id_map = {}  # Old ID -> New ID mapping

        for old_id, vertex_data in source_vertices.items():
            # Create new ID for this floor
            # Strip floor suffix if present, add new floor suffix
            base_name = old_id.rsplit('_F', 1)[0] if '_F' in old_id else old_id
            new_id = f"{base_name}_F{current_floor}"

            # Copy vertex data
            new_vertex = vertex_data.copy()
            new_vertex['id'] = new_id
            new_vertex['floor'] = current_floor

            self.model.vertices[new_id] = new_vertex
            vertex_id_map[old_id] = new_id

        # Copy edges between copied vertices
        source_edges = self.model.get_edges_on_floor(source_floor)
        edge_counter = len(self.model.edges)

        for old_edge_id, edge_data in source_edges.items():
            old_v_a = edge_data['vertex_a']
            old_v_b = edge_data['vertex_b']

            if old_v_a in vertex_id_map and old_v_b in vertex_id_map:
                new_edge_id = f"edge_{edge_counter}"
                edge_counter += 1

                new_edge = edge_data.copy()
                new_edge['id'] = new_edge_id
                new_edge['vertex_a'] = vertex_id_map[old_v_a]
                new_edge['vertex_b'] = vertex_id_map[old_v_b]

                self.model.edges[new_edge_id] = new_edge

        # Refresh display
        self.canvas.refresh_for_floor(current_floor)
        self.on_graph_modified()

        QMessageBox.information(
            self, "Duplication Complete",
            f"Duplicated {len(vertex_id_map)} nodes and {len(source_edges)} edges from Floor {source_floor} to Floor {current_floor}."
        )

    def on_measurement_scale_released(self):
        """Handle when measurement scale slider is released - hide reference."""
        self.canvas.hide_scale_reference()

    def on_measurement_scale_changed(self, value):
        """Handle measurement scale slider changes."""
        # Update scale label
        self.scale_label.setText(f"{value} px/m")

        # Update canvas measurement scale
        self.canvas.pixels_per_meter = value

        # Update visual indicator
        # Show what distance equals in meters
        # e.g., "100px = 5m" when scale is 20 px/m
        example_pixels = 100
        example_meters = example_pixels / value
        self.scale_indicator_label.setText(f"({example_pixels}px = {example_meters:.1f}m)")

        # Update scale reference if visible
        if self.canvas.scale_reference_visible:
            self.canvas.update_scale_reference()

    # ========== Help ==========

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About",
            "<h2>Building Evacuation Graph Maker</h2>"
            "<p>Visual editor for creating evacuation simulation graphs.</p>"
            "<p>HiMCM 2025 Problem A</p>"
        )


class TestSimulationDialog(QDialog):
    """Dialog for running quick test simulation."""

    def __init__(self, model: GraphModel, parent=None):
        """Initialize test dialog."""
        super().__init__(parent)

        self.model = model
        self.setWindowTitle("Quick Test Simulation")
        self.resize(600, 500)

        # Create UI
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Instructions
        label = QLabel("Running simulation with current graph...")
        layout.addWidget(label)

        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFontFamily("Courier")
        layout.addWidget(self.output_text)

        # Buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        self.run_btn = QPushButton("Run Simulation")
        self.run_btn.clicked.connect(self.run_simulation)
        button_layout.addWidget(self.run_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

    def run_simulation(self):
        """Run the simulation."""
        self.output_text.clear()
        self.run_btn.setEnabled(False)

        try:
            # Export to temp file
            import tempfile
            import os

            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            config = self.model.to_config()
            json.dump(config, temp_file, indent=2)
            temp_file.close()

            # Import simulator
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

            from simulator import Simulation

            # Create simulation
            sim = Simulation(
                config=config,
                num_firefighters=self.model.num_firefighters,
                fire_origin=self.model.fire_origin or list(self.model.vertices.keys())[0],
                seed=42
            )

            # Run for 30 ticks
            self.output_text.append("=== Running 30 tick simulation ===\n")

            for tick in range(31):
                if tick == 0:
                    self.output_text.append(f"Tick {tick}: Initial state")
                else:
                    sim.update({})

                    if tick % 10 == 0:
                        # Show status
                        fire_rooms = sum(1 for v in sim.vertices.values() if v.fire_intensity > 0.5)
                        evacuated = len(sim.evacuated_occupants)
                        remaining = sum(len(v.occupants) for v in sim.vertices.values())

                        self.output_text.append(
                            f"Tick {tick}: {fire_rooms} rooms on fire, "
                            f"{evacuated} evacuated, {remaining} remaining"
                        )

            # Final statistics
            self.output_text.append("\n=== Final Statistics ===")
            self.output_text.append(f"Total evacuated: {len(sim.evacuated_occupants)}")
            self.output_text.append(f"Total casualties: {len(sim.casualties)}")

            fire_rooms = sum(1 for v in sim.vertices.values() if v.fire_intensity > 0.5)
            self.output_text.append(f"Rooms on fire: {fire_rooms}")

            # Clean up temp file
            os.unlink(temp_file.name)

            self.output_text.append("\n✓ Simulation completed successfully!")

        except Exception as e:
            self.output_text.append(f"\n✗ Simulation failed: {e}")
            import traceback
            self.output_text.append(traceback.format_exc())

        finally:
            self.run_btn.setEnabled(True)


# Import QLabel for TestSimulationDialog
from PyQt5.QtWidgets import QLabel
