"""Progress bar widget — shows playback position."""
from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


def _fmt(seconds: float) -> str:
    s = int(seconds)
    return f'{s // 60}:{s % 60:02d}'


class ProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bar = QProgressBar()
        self._time_label = QLabel('0:00 / 0:00')
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)

        self._bar.setRange(0, 1000)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(6)

        layout.addWidget(self._bar)
        layout.addWidget(self._time_label)

    def update_position(self, current: float, duration: float) -> None:
        self._bar.setValue(int(current / duration * 1000) if duration > 0 else 0)
        self._time_label.setText(f'{_fmt(current)} / {_fmt(duration)}')
