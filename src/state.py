from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class TrackInfo:
    title: str
    artist: str
    duration: float       # seconds
    current_time: float   # seconds
    source: Literal['ytm', 'spotify']


@dataclass
class AppState:
    phase: Literal['setup', 'running', 'error'] = 'setup'
    active_source: Literal['ytm', 'spotify'] | None = None
    current_track: TrackInfo | None = None
    spotify_authed: bool = False
    spotify_device_active: bool = False
    ytm_logged_in: bool = False
    consecutive_count: int = 0
    paused: bool = False
