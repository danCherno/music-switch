"""YTM Bridge — hidden QWebEngineView controlling YouTube Music."""
from __future__ import annotations
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView

from .state import TrackInfo

YTM_URL = 'https://music.youtube.com'
_SCRIPT_PATH = Path(__file__).parent / 'ytm_script.js'
_POLL_INTERVAL_MS = 1000


class YTMBridge(QObject):
    song_ended = pyqtSignal(str)                    # source='ytm'
    track_changed = pyqtSignal(TrackInfo)
    position_updated = pyqtSignal(float, float)     # current_s, duration_s
    ytm_ready = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Persistent profile — Qt stores cookies/localStorage on disk.
        self._profile = QWebEngineProfile('MusicSwitch-YTM')
        self._page = QWebEnginePage(self._profile)
        self._view = QWebEngineView()
        self._view.setPage(self._page)
        self._poll_timer = QTimer(self)
        self._inject_script = _SCRIPT_PATH.read_text()
        self._last_track_key: tuple[str, str] | None = None
        self._ready = False   # flips True on first detected song

        self._setup_view()
        self._setup_poll_timer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Load YTM in the hidden view."""
        self._view.load(QUrl(YTM_URL))

    def play(self) -> None:
        self._last_track_key = None  # force track_changed on next poll
        self._view.page().setAudioMuted(False)
        self._view.page().runJavaScript("document.querySelector('video')?.play()")

    def pause(self) -> None:
        self._view.page().runJavaScript("document.querySelector('video')?.pause()")
        self._view.page().setAudioMuted(True)

    def skip(self) -> None:
        """Click the next-track button inside the YTM player bar."""
        self._view.page().runJavaScript(
            "document.querySelector('.next-button.ytmusic-player-bar')?.click()"
        )

    def show_window(self) -> None:
        """Show the YTM webview so the user can browse and start a song."""
        self._view.setWindowTitle('YouTube Music')
        self._view.resize(1200, 800)
        self._view.show()

    def hide_window(self) -> None:
        """Hide the YTM webview."""
        self._view.hide()

    # ------------------------------------------------------------------
    # Internal setup
    # ------------------------------------------------------------------

    def _setup_view(self) -> None:
        self._view.page().setAudioMuted(True)
        self._view.hide()
        self._view.loadFinished.connect(self._on_load_finished)

    def _setup_poll_timer(self) -> None:
        self._poll_timer.setInterval(_POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll_state)

    # ------------------------------------------------------------------
    # Slots / callbacks
    # ------------------------------------------------------------------

    @pyqtSlot(bool)
    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            return
        self._view.page().runJavaScript(self._inject_script)
        if not self._poll_timer.isActive():
            self._poll_timer.start()

    @pyqtSlot()
    def _poll_state(self) -> None:
        self._view.page().runJavaScript(
            "window.__ytmState || null",
            self._handle_state,
        )

    def _handle_state(self, state: dict | None) -> None:
        if not state:
            return

        title = state.get('title', '')
        artist = state.get('artist', '')
        current = float(state.get('currentTime', 0))
        duration = float(state.get('duration', 0))

        self.position_updated.emit(current, duration)

        track_key = (title, artist)
        if title and track_key != self._last_track_key:
            self._last_track_key = track_key
            if not self._ready:
                self._ready = True
                self.ytm_ready.emit(True)
            self.track_changed.emit(TrackInfo(
                title=title,
                artist=artist,
                duration=duration,
                current_time=current,
                source='ytm',
            ))

        if state.get('ended'):
            # Reset the flag before emitting so a re-poll doesn't double-fire.
            self._view.page().runJavaScript(
                "if (window.__ytmState) window.__ytmState.ended = false;"
            )
            self.song_ended.emit('ytm')
