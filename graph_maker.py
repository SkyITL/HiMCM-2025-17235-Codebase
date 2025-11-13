#!/usr/bin/env python3
"""
Graph Maker Tool - Entry Point

Visual editor for creating building evacuation graphs.
Launch the PyQt5-based GUI application for graph editing.
"""

import sys
from PyQt5.QtWidgets import QApplication

# Import from modular package
from graph_maker import MainWindow


def main():
    """Launch the graph maker application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Building Evacuation Graph Maker")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
