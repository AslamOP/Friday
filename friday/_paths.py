from __future__ import annotations

import os
from pathlib import Path


def _home() -> Path:
    return Path(os.environ.get("FRIDAY_DIR", Path.home() / ".friday"))


def cfg_dir() -> Path:
    d = _home()
    d.mkdir(parents=True, exist_ok=True)
    return d


def cfg_file() -> Path:
    return cfg_dir() / "config.toml"


def data_dir() -> Path:
    d = _home() / "store"
    d.mkdir(parents=True, exist_ok=True)
    return d
