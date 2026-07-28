from __future__ import annotations

from typing import Any


class Catalog:
    _storage: dict[str, dict[str, Any]] = {}

    @classmethod
    def tag(cls, group: str, key: str):
        def wrap(klass):
            cls._storage.setdefault(group, {})[key] = klass
            return klass
        return wrap

    @classmethod
    def fetch(cls, group: str, key: str) -> Any:
        g = cls._storage.get(group, {})
        if key not in g:
            raise KeyError(f"'{key}' not found in '{group}'")
        return g[key]

    @classmethod
    def spawn(cls, group: str, key: str, *args, **kwargs) -> Any:
        return cls.fetch(group, key)(*args, **kwargs)

    @classmethod
    def names(cls, group: str) -> list[str]:
        return list(cls._storage.get(group, {}).keys())

    @classmethod
    def has(cls, group: str, key: str) -> bool:
        return key in cls._storage.get(group, {})
