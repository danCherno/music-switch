"""Skip button widget."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QPushButton


class SkipButton(QPushButton):
    skip_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__('Skip', parent)
        self.clicked.connect(self.skip_requested)
