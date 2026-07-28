from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class Bus:
    def __init__(self):
        self._hooks: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str, fn: Callable):
        self._hooks[event].append(fn)

    def fire(self, event: str, data: dict[str, Any] | None = None):
        for fn in self._hooks.get(event, []):
            fn(data or {})

    def off(self, event: str, fn: Callable):
        try:
            self._hooks[event].remove(fn)
        except ValueError:
            pass
