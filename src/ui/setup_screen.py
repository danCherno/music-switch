"""Setup screen — shown before playback is ready."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SetupScreen(QWidget):
    spotify_auth_requested = pyqtSignal()
    ytm_open_requested = pyqtSignal()
    ytm_close_requested = pyqtSignal()
    start_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ytm_status = QLabel('Waiting for a song...')
        self._ytm_open_btn = QPushButton('Open YouTube Music')
        self._ytm_close_btn = QPushButton('Done')
        self._spotify_status = QLabel('Not connected')
        self._spotify_auth_btn = QPushButton('Connect Spotify')
        self._start_btn = QPushButton('▶  Start')
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(6)

        # YTM section
        root.addWidget(_section_label('YouTube Music'))
        root.addWidget(self._ytm_status)
        ytm_row = QHBoxLayout()
        ytm_row.addWidget(self._ytm_open_btn)
        ytm_row.addWidget(self._ytm_close_btn)
        root.addLayout(ytm_row)

        root.addWidget(_divider())

        # Spotify section
        root.addWidget(_section_label('Spotify'))
        root.addWidget(self._spotify_status)
        root.addWidget(self._spotify_auth_btn)

        root.addWidget(_divider())

        root.addWidget(self._start_btn)

        self._ytm_open_btn.clicked.connect(self.ytm_open_requested)
        self._ytm_close_btn.clicked.connect(self.ytm_close_requested)
        self._spotify_auth_btn.clicked.connect(self.spotify_auth_requested)
        self._start_btn.clicked.connect(self.start_requested)

        self._start_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Public updates (called by FloatingWindow on state_changed)
    # ------------------------------------------------------------------

    def update_ytm_status(self, song_detected: bool) -> None:
        self._ytm_status.setText(
            '✓ Song detected' if song_detected else 'Waiting for a song...'
        )

    def update_spotify_status(self, authed: bool) -> None:
        self._spotify_status.setText('✓ Connected' if authed else 'Not connected')
        self._spotify_auth_btn.setText(
            'Re-authenticate' if authed else 'Connect Spotify'
        )

    def show_spotify_error(self, message: str) -> None:
        self._spotify_status.setText(f'Error: {message}')

    def set_ready(self, ready: bool) -> None:
        self._start_btn.setEnabled(ready)


def _section_label(text: str) -> QLabel:
    return QLabel(f'<b>{text}</b>')


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
