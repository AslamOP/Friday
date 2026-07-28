from __future__ import annotations
import tomllib
from pathlib import Path
from typing import Any

_PRESETS_DIR = Path(__file__).parent.parent / "presets"

def load_preset(name: str = "default") -> dict[str, Any]:
    path = _PRESETS_DIR / f"{name}.toml"
    if not path.exists():
        path = _PRESETS_DIR / "default.toml"
    return tomllib.loads(path.read_text())
