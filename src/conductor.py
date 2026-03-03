"""Conductor — shuffle state machine and playback decision engine."""
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Literal

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from .state import AppState


@dataclass
class ConductorState:
    active_source: Literal['ytm', 'spotify'] | None = None
    consecutive_count: int = 0
    phase: Literal['setup', 'running', 'error'] = 'setup'
    ytm_ready: bool = False
    spotify_ready: bool = False
    paused: bool = False


class Conductor(QObject):
    state_changed = pyqtSignal(object)  # AppState

    def __init__(self, ytm_bridge, spotify_client=None, parent=None):
        super().__init__(parent)
        self._state = ConductorState()
        self._ytm = ytm_bridge
        self._spotify = spotify_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """User clicked Start — begin playback on the decided platform."""
        if not self._state.ytm_ready and not self._state.spotify_ready:
            return
        self._state.phase = 'running'
        self.switch_to(self.decide_next_platform())

    # ------------------------------------------------------------------
    # Slots wired from YTMBridge / SpotifyClient
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def on_song_ended(self, source: str) -> None:
        """A song finished — decide next platform and switch if needed."""
        if self._state.phase != 'running':
            return
        next_platform = self.decide_next_platform()
        if next_platform == self._state.active_source:
            self._state.consecutive_count += 1
            self._emit_state()
        else:
            self.switch_to(next_platform)

    @pyqtSlot()
    def on_pause_toggle(self) -> None:
        if self._state.phase != 'running':
            return
        self._state.paused = not self._state.paused
        if self._state.paused:
            if self._state.active_source == 'ytm':
                self._ytm.pause()
            elif self._spotify:
                self._spotify.pause()
        else:
            if self._state.active_source == 'ytm':
                self._ytm.play()
            elif self._spotify:
                self._spotify.play()
        self._emit_state()

    @pyqtSlot()
    def on_skip(self) -> None:
        if self._state.phase != 'running':
            return
        next_platform = self.decide_next_platform()
        if next_platform == self._state.active_source:
            # Staying on same platform — advance its queue
            if self._state.active_source == 'ytm':
                self._ytm.skip()
            elif self._state.active_source == 'spotify' and self._spotify:
                self._spotify.skip()
            self._state.consecutive_count += 1
            self._emit_state()
        else:
            # Switching platforms — don't advance the departing platform's queue
            self.switch_to(next_platform)

    @pyqtSlot(bool)
    def on_ytm_ready(self, ready: bool) -> None:
        self._state.ytm_ready = ready
        self._emit_state()

    @pyqtSlot(bool)
    def on_spotify_ready(self, ready: bool) -> None:
        self._state.spotify_ready = ready
        self._emit_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def decide_next_platform(self) -> str:
        """Weighted coin flip with memory. Returns 'ytm' or 'spotify'.

        consecutive plays on current platform:
          1  →  50/50
          2  →  35/65 toward other
          3  →  20/80 toward other
          4+ →  10/90 toward other
        """
        if not self._state.spotify_ready:
            return 'ytm'
        if not self._state.ytm_ready:
            return 'spotify'

        current = self._state.active_source
        n = self._state.consecutive_count
        weights = {1: 0.5, 2: 0.35, 3: 0.20}.get(n, 0.10)
        stay_prob = weights if current else 0.5

        if random.random() < stay_prob:
            return current or 'ytm'
        return 'spotify' if current == 'ytm' else 'ytm'

    def switch_to(self, platform: str) -> None:
        """Mute the inactive source, play the active one."""
        self._state.active_source = platform
        self._state.consecutive_count = 1
        self._state.paused = False

        if platform == 'ytm':
            if self._spotify:
                self._spotify.skip()   # queue up next Spotify track before leaving
            self._ytm.play()
            if self._spotify:
                self._spotify.pause()
        else:
            if self._spotify:
                self._spotify.play()
            self._ytm.pause()

        self._emit_state()

    def _emit_state(self) -> None:
        state = AppState(
            phase=self._state.phase,
            active_source=self._state.active_source,
            ytm_logged_in=self._state.ytm_ready,
            spotify_authed=self._state.spotify_ready,
            consecutive_count=self._state.consecutive_count,
            paused=self._state.paused,
        )
        self.state_changed.emit(state)
