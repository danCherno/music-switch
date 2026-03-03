"""MusicSwitch — entry point."""
from __future__ import annotations
import sys

from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication

from src.conductor import Conductor
from src.spotify_client import SpotifyClient
from src.ytm_bridge import YTMBridge
from src.ui.floating_window import FloatingWindow


def wire_signals(
    conductor: Conductor,
    ytm: YTMBridge,
    spotify: SpotifyClient,
    window: FloatingWindow,
) -> None:
    # YTM → Conductor / Window
    ytm.song_ended.connect(conductor.on_song_ended)
    ytm.ytm_ready.connect(conductor.on_ytm_ready)
    ytm.track_changed.connect(window.on_track_changed)
    ytm.position_updated.connect(window.on_ytm_position_updated)

    # Spotify → Conductor / Window
    spotify.song_ended.connect(conductor.on_song_ended)
    spotify.track_changed.connect(window.on_track_changed)
    spotify.position_updated.connect(window.on_spotify_position_updated)
    spotify.spotify_no_device.connect(window.on_spotify_no_device)
    spotify.auth_changed.connect(conductor.on_spotify_ready)
    spotify.auth_error.connect(window._setup_screen.show_spotify_error)

    # Conductor → Window
    conductor.state_changed.connect(window.on_state_changed)

    # Window → Conductor
    window._pause_button.pause_requested.connect(conductor.on_pause_toggle)
    window._skip_button.skip_requested.connect(conductor.on_skip)
    window.ytm_open_requested.connect(ytm.show_window)
    window.ytm_close_requested.connect(ytm.hide_window)

    # SetupScreen → services
    window._setup_screen.spotify_auth_requested.connect(spotify.authenticate)
    window._setup_screen.ytm_open_requested.connect(ytm.show_window)
    window._setup_screen.ytm_close_requested.connect(ytm.hide_window)
    window._setup_screen.start_requested.connect(conductor.start)


def main() -> None:
    load_dotenv()

    app = QApplication(sys.argv)
    app.setApplicationName('MusicSwitch')
    app.setQuitOnLastWindowClosed(False)

    ytm = YTMBridge()
    spotify = SpotifyClient()
    conductor = Conductor(ytm, spotify)
    window = FloatingWindow()

    wire_signals(conductor, ytm, spotify, window)

    window.show()
    ytm.start()
    spotify.start()  # tries saved token on launch; polls once authed

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
