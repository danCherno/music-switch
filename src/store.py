"""Persistent config storage (tokens, preferences) via platformdirs."""
from __future__ import annotations
import json
import os
from pathlib import Path

import platformdirs


APP_NAME = 'MusicSwitch'


def _config_path() -> Path:
    return Path(platformdirs.user_config_dir(APP_NAME)) / 'config.json'


def load() -> dict:
    path = _config_path()
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def save(data: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as f:
        json.dump(data, f, indent=2)


def get(key: str, default=None):
    return load().get(key, default)


def set(key: str, value) -> None:
    data = load()
    data[key] = value
    save(data)
