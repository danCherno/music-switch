"""Pause / Resume toggle button."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QPushButton


class PauseButton(QPushButton):
    pause_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__('⏸  Pause', parent)
        self.clicked.connect(self.pause_requested)

    def update_state(self, paused: bool) -> None:
        self.setText('▶  Resume' if paused else '⏸  Pause')
