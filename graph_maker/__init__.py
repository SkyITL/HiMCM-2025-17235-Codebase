#!/usr/bin/env python3
"""
Graph Maker - Visual editor for building evacuation graphs.

A PyQt5-based application for creating and editing building evacuation simulation graphs.
Supports visual node/edge placement, property editing, occupancy configuration, and built-in testing.
"""

from .models import GraphModel
from .items import NodeItem, EdgeItem
from .canvas import GraphCanvas
from .panels import PropertyPanel, OccupancyPanel, StatsPanel
from .main_window import MainWindow

__version__ = "1.0.0"
__all__ = [
    'GraphModel',
    'NodeItem',
    'EdgeItem',
    'GraphCanvas',
    'PropertyPanel',
    'OccupancyPanel',
    'StatsPanel',
    'MainWindow',
]
