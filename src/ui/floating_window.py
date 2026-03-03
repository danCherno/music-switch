"""Floating window — the main UI widget."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..state import AppState, TrackInfo
from .now_playing import NowPlaying
from .pause_button import PauseButton
from .progress_bar import ProgressBar
from .setup_screen import SetupScreen
from .skip_button import SkipButton

_SETUP_PAGE = 0
_PLAYER_PAGE = 1


class FloatingWindow(QWidget):
    ytm_open_requested = pyqtSignal()
    ytm_close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_screen = SetupScreen()
        self._now_playing = NowPlaying()
        self._progress_bar = ProgressBar()
        self._pause_button = PauseButton()
        self._skip_button = SkipButton()
        self._ytm_btn = QPushButton('Open YouTube Music')
        self._ytm_window_open = False
        self._stack = QStackedWidget()
        self._drag_pos = None
        self._active_source: str | None = None
        self._collapsed = False
        self._expanded_height = 260
        self._title_bar: _TitleBar

        self._build_ui()
        self._apply_window_flags()
        self.setMinimumWidth(360)
        self.resize(400, self._expanded_height)

    # ------------------------------------------------------------------
    # Slots wired from signals
    # ------------------------------------------------------------------

    @pyqtSlot(object)
    def on_state_changed(self, state: AppState) -> None:
        self._active_source = state.active_source
        if state.phase == 'running':
            self._show_player()
            self._pause_button.update_state(state.paused)
        else:
            self._show_setup()
            self._setup_screen.update_ytm_status(state.ytm_logged_in)
            self._setup_screen.update_spotify_status(state.spotify_authed)
            self._setup_screen.set_ready(state.ytm_logged_in or state.spotify_authed)

    @pyqtSlot(object)
    def on_track_changed(self, track: TrackInfo) -> None:
        if track.source == self._active_source:
            self._now_playing.update_track(track)

    @pyqtSlot(float, float)
    def on_ytm_position_updated(self, current: float, duration: float) -> None:
        if self._active_source == 'ytm':
            self._progress_bar.update_position(current, duration)

    @pyqtSlot(float, float)
    def on_spotify_position_updated(self, current: float, duration: float) -> None:
        if self._active_source == 'spotify':
            self._progress_bar.update_position(current, duration)

    @pyqtSlot()
    def on_spotify_no_device(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Collapse
    # ------------------------------------------------------------------

    def toggle_collapse(self) -> None:
        if self._collapsed:
            self._stack.show()
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self.resize(self.width(), self._expanded_height)
            self._collapsed = False
        else:
            self._expanded_height = self.height()
            self._stack.hide()
            self.setFixedHeight(self._title_bar.height())
            self._collapsed = True
        self._title_bar.update_collapse_button(self._collapsed)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._title_bar = _TitleBar(self)
        root.addWidget(self._title_bar)

        # Player page
        player_page = QWidget()
        player_layout = QVBoxLayout(player_page)
        player_layout.setContentsMargins(12, 8, 12, 12)
        player_layout.setSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._pause_button)
        btn_row.addWidget(self._skip_button)

        self._ytm_btn.setFlat(True)
        self._ytm_btn.clicked.connect(self._toggle_ytm_window)

        player_layout.addWidget(self._now_playing)
        player_layout.addWidget(self._progress_bar)
        player_layout.addLayout(btn_row)
        player_layout.addWidget(self._ytm_btn)

        self._stack.addWidget(self._setup_screen)  # index 0
        self._stack.addWidget(player_page)          # index 1
        root.addWidget(self._stack)

    def _apply_window_flags(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )

    def _show_setup(self) -> None:
        self._stack.setCurrentIndex(_SETUP_PAGE)

    def _show_player(self) -> None:
        self._stack.setCurrentIndex(_PLAYER_PAGE)

    def _toggle_ytm_window(self) -> None:
        if self._ytm_window_open:
            self._ytm_window_open = False
            self._ytm_btn.setText('Open YouTube Music')
            self.ytm_close_requested.emit()
        else:
            self._ytm_window_open = True
            self._ytm_btn.setText('Close YouTube Music')
            self.ytm_open_requested.emit()


class _TitleBar(QWidget):
    """Drag handle + collapse + close buttons for the frameless window."""

    def __init__(self, window: FloatingWindow):
        super().__init__(window)
        self._window = window
        self._drag_pos = None
        self._collapse_btn = QPushButton('−')
        self.setFixedHeight(28)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)

        lbl = QLabel('MusicSwitch')

        self._collapse_btn.setFixedSize(22, 22)
        self._collapse_btn.setFlat(True)
        self._collapse_btn.clicked.connect(self._window.toggle_collapse)

        close_btn = QPushButton('×')
        close_btn.setFixedSize(22, 22)
        close_btn.setFlat(True)
        close_btn.clicked.connect(self._window.close)

        layout.addWidget(lbl)
        layout.addStretch()
        layout.addWidget(self._collapse_btn)
        layout.addWidget(close_btn)

    def update_collapse_button(self, collapsed: bool) -> None:
        self._collapse_btn.setText('+' if collapsed else '−')

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint()
                - self._window.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self._window.move(
                event.globalPosition().toPoint() - self._drag_pos
            )

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
