#!/usr/bin/env python3
"""
Custom widgets for graph maker.

Provides RangeSlider and other custom UI components.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSpinBox
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import QRect, QPoint


class RangeSlider(QWidget):
    """Dual-handle slider for selecting a min-max range."""

    rangeChanged = pyqtSignal(int, int)  # Emits (min_value, max_value)

    def __init__(self, minimum=0, maximum=100, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)

        self._minimum = minimum
        self._maximum = maximum
        self._min_value = minimum
        self._max_value = maximum

        self._handle_radius = 8
        self._track_height = 4
        self._dragging = None  # 'min', 'max', or None

        self.setMouseTracking(True)

    def minimum(self):
        return self._minimum

    def maximum(self):
        return self._maximum

    def setMinimum(self, value):
        self._minimum = value
        self._min_value = max(self._min_value, value)
        self._max_value = max(self._max_value, value)
        self.update()

    def setMaximum(self, value):
        self._maximum = value
        self._min_value = min(self._min_value, value)
        self._max_value = min(self._max_value, value)
        self.update()

    def minValue(self):
        return self._min_value

    def maxValue(self):
        return self._max_value

    def setMinValue(self, value):
        value = max(self._minimum, min(value, self._max_value))
        if value != self._min_value:
            self._min_value = value
            self.update()
            self.rangeChanged.emit(self._min_value, self._max_value)

    def setMaxValue(self, value):
        value = min(self._maximum, max(value, self._min_value))
        if value != self._max_value:
            self._max_value = value
            self.update()
            self.rangeChanged.emit(self._min_value, self._max_value)

    def setRange(self, min_value, max_value):
        """Set both min and max values."""
        self._min_value = max(self._minimum, min(min_value, self._maximum))
        self._max_value = min(self._maximum, max(max_value, self._min_value))
        self.update()
        self.rangeChanged.emit(self._min_value, self._max_value)

    def _value_to_pixel(self, value):
        """Convert a value to pixel position."""
        margin = self._handle_radius + 2
        usable_width = self.width() - 2 * margin
        if self._maximum == self._minimum:
            return margin
        ratio = (value - self._minimum) / (self._maximum - self._minimum)
        return margin + int(ratio * usable_width)

    def _pixel_to_value(self, pixel):
        """Convert pixel position to value."""
        margin = self._handle_radius + 2
        usable_width = self.width() - 2 * margin
        if usable_width <= 0:
            return self._minimum
        ratio = (pixel - margin) / usable_width
        ratio = max(0.0, min(1.0, ratio))
        value = self._minimum + ratio * (self._maximum - self._minimum)
        return int(round(value))

    def paintEvent(self, event):
        # Safety checks
        if self.width() < 20 or self.height() < 10:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw track
        track_y = self.height() // 2
        track_width = max(1, self.width() - 2 * (self._handle_radius + 2))
        track_rect = QRect(
            self._handle_radius + 2,
            track_y - self._track_height // 2,
            track_width,
            self._track_height
        )
        painter.fillRect(track_rect, QColor(200, 200, 200))

        # Draw highlighted range
        min_x = self._value_to_pixel(self._min_value)
        max_x = self._value_to_pixel(self._max_value)
        highlight_width = max(0, max_x - min_x)

        if highlight_width > 0:
            highlight_rect = QRect(
                min_x,
                track_y - self._track_height // 2,
                highlight_width,
                self._track_height
            )
            painter.fillRect(highlight_rect, QColor(100, 150, 250))

        # Draw min handle
        painter.setBrush(QColor(50, 100, 200))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(
            QPoint(min_x, track_y),
            self._handle_radius,
            self._handle_radius
        )

        # Draw max handle
        painter.setBrush(QColor(50, 100, 200))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(
            QPoint(max_x, track_y),
            self._handle_radius,
            self._handle_radius
        )

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        track_y = self.height() // 2
        mouse_pos = event.pos()

        min_x = self._value_to_pixel(self._min_value)
        max_x = self._value_to_pixel(self._max_value)

        # Check if clicked on min handle
        if abs(mouse_pos.x() - min_x) <= self._handle_radius and \
           abs(mouse_pos.y() - track_y) <= self._handle_radius:
            self._dragging = 'min'
        # Check if clicked on max handle
        elif abs(mouse_pos.x() - max_x) <= self._handle_radius and \
             abs(mouse_pos.y() - track_y) <= self._handle_radius:
            self._dragging = 'max'

    def mouseMoveEvent(self, event):
        if self._dragging == 'min':
            new_value = self._pixel_to_value(event.pos().x())
            self.setMinValue(new_value)
        elif self._dragging == 'max':
            new_value = self._pixel_to_value(event.pos().x())
            self.setMaxValue(new_value)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = None


class RangeControl(QWidget):
    """Combined widget with range slider and spin boxes for precise entry."""

    rangeChanged = pyqtSignal(int, int)  # Emits (min_value, max_value)

    def __init__(self, minimum=0, maximum=100, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Min label and spinbox
        layout.addWidget(QLabel("Min:"))
        self.min_spin = QSpinBox()
        self.min_spin.setMinimum(minimum)
        self.min_spin.setMaximum(maximum)
        self.min_spin.setValue(minimum)
        layout.addWidget(self.min_spin)

        # Range slider
        self.slider = RangeSlider(minimum, maximum)
        layout.addWidget(self.slider, stretch=3)

        # Max label and spinbox
        layout.addWidget(QLabel("Max:"))
        self.max_spin = QSpinBox()
        self.max_spin.setMinimum(minimum)
        self.max_spin.setMaximum(maximum)
        self.max_spin.setValue(maximum)
        layout.addWidget(self.max_spin)

        # Connect signals
        self.slider.rangeChanged.connect(self._on_slider_changed)
        self.min_spin.valueChanged.connect(self._on_min_spin_changed)
        self.max_spin.valueChanged.connect(self._on_max_spin_changed)

    def _on_slider_changed(self, min_val, max_val):
        """Handle slider changes."""
        self.min_spin.blockSignals(True)
        self.max_spin.blockSignals(True)
        self.min_spin.setValue(min_val)
        self.max_spin.setValue(max_val)
        self.min_spin.blockSignals(False)
        self.max_spin.blockSignals(False)
        self.rangeChanged.emit(min_val, max_val)

    def _on_min_spin_changed(self, value):
        """Handle min spinbox changes."""
        self.slider.setMinValue(value)
        # Ensure max is at least equal to min
        if self.max_spin.value() < value:
            self.max_spin.setValue(value)

    def _on_max_spin_changed(self, value):
        """Handle max spinbox changes."""
        self.slider.setMaxValue(value)
        # Ensure min is at most equal to max
        if self.min_spin.value() > value:
            self.min_spin.setValue(value)

    def setRange(self, min_value, max_value):
        """Set the current min-max range."""
        self.slider.setRange(min_value, max_value)
        self.min_spin.setValue(min_value)
        self.max_spin.setValue(max_value)

    def minValue(self):
        return self.min_spin.value()

    def maxValue(self):
        return self.max_spin.value()

    def setMinimum(self, value):
        """Set the minimum possible value."""
        self.slider.setMinimum(value)
        self.min_spin.setMinimum(value)
        self.max_spin.setMinimum(value)

    def setMaximum(self, value):
        """Set the maximum possible value."""
        self.slider.setMaximum(value)
        self.min_spin.setMaximum(value)
        self.max_spin.setMaximum(value)
