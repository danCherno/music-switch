"""Spotify Client — spotipy wrapper with polling on a QThread."""
from __future__ import annotations
import http.server
import logging
import os
import threading
import traceback
import urllib.parse
import webbrowser
from pathlib import Path

import platformdirs
import spotipy
from spotipy.oauth2 import SpotifyPKCE
from PyQt6.QtCore import QThread, pyqtSignal

from .state import TrackInfo

_SCOPE = 'user-read-playback-state user-modify-playback-state'
_REDIRECT_URI = 'http://127.0.0.1:8888/callback'
_END_BUFFER_MS = 3000


class SpotifyClient(QThread):
    song_ended = pyqtSignal(str)                    # source='spotify'
    track_changed = pyqtSignal(TrackInfo)
    position_updated = pyqtSignal(float, float)     # current_s, duration_s
    spotify_no_device = pyqtSignal()
    auth_changed = pyqtSignal(bool)                 # True = authenticated
    auth_error = pyqtSignal(str)                    # human-readable error

    POLL_INTERVAL_MS = 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._sp: spotipy.Spotify | None = None
        self._auth: SpotifyPKCE | None = None
        self._authed = False
        self._device_active = False   # True only when a device is confirmed live
        self._device_id: str | None = None  # last known device ID for reliable play
        self._end_armed = False
        self._end_timer: threading.Timer | None = None
        self._last_track_id: str | None = None
        # Silence spotipy's HTTP-level error logging — we handle errors ourselves.
        logging.getLogger('spotipy').setLevel(logging.CRITICAL)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def authenticate(self) -> None:
        """Start OAuth PKCE flow in a background thread (non-blocking)."""
        if not os.getenv('SPOTIFY_CLIENT_ID'):
            self.auth_error.emit('SPOTIFY_CLIENT_ID not set in .env')
            return
        threading.Thread(target=self._do_auth, daemon=True).start()

    def play(self) -> None:
        self._last_track_id = None  # force track_changed on next poll
        if self._sp and self._authed:
            try:
                self._sp.start_playback(device_id=self._device_id)
            except Exception:
                pass

    def pause(self) -> None:
        if self._sp and self._device_active:
            try:
                self._sp.pause_playback()
            except Exception:
                pass

    def skip(self) -> None:
        if self._sp and self._device_active:
            try:
                self._sp.next_track()
            except Exception:
                pass

    def stop_polling(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # QThread entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        self._running = True
        # Try to restore a saved token before asking the user to auth.
        if not self._authed:
            self._load_saved_token()
        while self._running:
            if self._authed and self._sp:
                self._tick()
            self.msleep(self.POLL_INTERVAL_MS)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        try:
            playback = self._sp.current_playback()
            self._process_state(playback)
            if not self._device_id:
                self._fetch_device_id()
        except Exception:
            pass

    def _fetch_device_id(self) -> None:
        """Find any available Spotify device even when nothing is playing."""
        try:
            result = self._sp.devices()
            devices = (result or {}).get('devices', [])
            if devices:
                self._device_id = devices[0]['id']
        except Exception:
            pass

    def _process_state(self, playback: dict | None) -> None:
        if not playback or not playback.get('item'):
            self._device_active = False
            self.spotify_no_device.emit()
            self._cancel_end_timer()
            return

        device = playback.get('device') or {}
        self._device_active = True
        self._device_id = device.get('id') or self._device_id
        item = playback['item']
        track_id = item['id']
        progress_ms = playback.get('progress_ms') or 0
        duration_ms = item.get('duration_ms') or 0

        # Reset end detection when the track changes.
        if track_id != self._last_track_id:
            self._last_track_id = track_id
            self._cancel_end_timer()
            self._end_armed = False
            self.track_changed.emit(TrackInfo(
                title=item['name'],
                artist=', '.join(a['name'] for a in item['artists']),
                duration=duration_ms / 1000,
                current_time=progress_ms / 1000,
                source='spotify',
            ))

        self.position_updated.emit(progress_ms / 1000, duration_ms / 1000)

        # Predictive end detection — fire song_ended slightly before the
        # track finishes so the conductor has time to act.
        remaining_ms = duration_ms - progress_ms
        if 0 < remaining_ms < _END_BUFFER_MS and not self._end_armed:
            self._end_armed = True
            self._arm_end(remaining_ms)

    def _arm_end(self, remaining_ms: int) -> None:
        # QTimer.singleShot doesn't work in a bare QThread.run() (no event
        # loop), so use a Python threading.Timer instead.
        self._end_timer = threading.Timer(
            remaining_ms / 1000.0,
            lambda: self.song_ended.emit('spotify'),
        )
        self._end_timer.daemon = True
        self._end_timer.start()

    def _cancel_end_timer(self) -> None:
        if self._end_timer:
            self._end_timer.cancel()
            self._end_timer = None

    def _do_auth(self) -> None:
        """Full OAuth PKCE flow — opens browser, catches redirect locally."""
        try:
            auth = self._build_auth()
            auth_url = auth.get_authorize_url()

            # Start the local redirect server before opening the browser
            # to guarantee the socket is bound before Spotify redirects.
            code_holder: list[str] = []
            server_ready = threading.Event()

            def serve() -> None:
                _run_callback_server(code_holder, server_ready)

            server_thread = threading.Thread(target=serve, daemon=True)
            server_thread.start()
            server_ready.wait(timeout=2)

            webbrowser.open(auth_url)
            server_thread.join(timeout=120)

            if not code_holder:
                self.auth_changed.emit(False)
                return

            auth.get_access_token(code_holder[0])
            self._auth = auth
            self._sp = spotipy.Spotify(auth_manager=self._auth)
            self._authed = True
            self.auth_changed.emit(True)
        except Exception as exc:
            traceback.print_exc()
            self.auth_error.emit(str(exc))
            self.auth_changed.emit(False)

    def _build_auth(self) -> SpotifyPKCE:
        cache_path = (
            Path(platformdirs.user_config_dir('MusicSwitch')) / 'spotify_token.cache'
        )
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        return SpotifyPKCE(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            redirect_uri=_REDIRECT_URI,
            scope=_SCOPE,
            cache_path=str(cache_path),
            open_browser=False,  # we open the browser ourselves
        )

    def _load_saved_token(self) -> bool:
        """Restore session from disk without triggering browser auth."""
        try:
            auth = self._build_auth()
            if auth.get_cached_token():
                self._auth = auth
                self._sp = spotipy.Spotify(auth_manager=self._auth)
                self._authed = True
                self.auth_changed.emit(True)
                return True
        except Exception:
            pass
        return False


# ---------------------------------------------------------------------------
# OAuth redirect helper (module-level, no class state needed)
# ---------------------------------------------------------------------------

def _run_callback_server(
    code_holder: list[str],
    ready_event: threading.Event,
) -> None:
    """Start a one-shot HTTP server on 127.0.0.1:8888, signal ready_event
    once the socket is bound, then block until Spotify redirects back."""

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            params = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query
            )
            code = params.get('code', [None])[0]
            if code:
                code_holder.append(code)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(
                b'<html><body>'
                b'<h2>Authenticated!</h2>'
                b'<p>You can close this tab and return to MusicSwitch.</p>'
                b'</body></html>'
            )

        def log_message(self, *_) -> None:
            pass  # silence request logs

    server = http.server.HTTPServer(('127.0.0.1', 8888), _Handler)
    server.timeout = 120
    ready_event.set()       # socket is bound — safe to open the browser now
    server.handle_request() # blocks until exactly one request arrives
    server.server_close()
