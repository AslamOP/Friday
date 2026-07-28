from __future__ import annotations

try:
    from importlib.metadata import version as _v
    __version__ = _v("friday")
except Exception:
    __version__ = "3.0.0"

from friday._sdk import Friday

__all__ = ["Friday", "__version__"]
