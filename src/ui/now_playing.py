"""Now Playing widget — displays current track info."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..state import TrackInfo

_SOURCE_NAMES = {'ytm': 'YouTube Music', 'spotify': 'Spotify'}


class NowPlaying(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._source_label = QLabel('')
        self._title_label = QLabel('—')
        self._artist_label = QLabel('—')
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(2)

        self._source_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        title_font = self._title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 1)
        self._title_label.setFont(title_font)
        self._title_label.setWordWrap(True)
        self._artist_label.setWordWrap(True)

        layout.addWidget(self._source_label)
        layout.addWidget(self._title_label)
        layout.addWidget(self._artist_label)

    def update_track(self, track: TrackInfo | None) -> None:
        if track is None:
            self._source_label.setText('')
            self._title_label.setText('—')
            self._artist_label.setText('—')
            return
        self._source_label.setText(_SOURCE_NAMES.get(track.source, track.source))
        self._title_label.setText(track.title or '—')
        self._artist_label.setText(track.artist or '—')
