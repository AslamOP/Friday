"""Friday SDK — main entry point for programmatic use."""

from __future__ import annotations

import logging

import friday.experts  # noqa: F401
import friday.procs  # noqa: F401
from friday._config import Settings, load, seed
from friday._engine import Engine, pick
from friday._events import Bus
from friday._registry import Catalog

log = logging.getLogger("friday")

_PROCS_MAP = {
    "chat": ["calc", "search"],
    "code": ["sh", "read", "write", "ls", "search"],
    "research": ["search"],
    "cad": ["sw_open", "sw_mass", "sw_param", "sw_stl", "sw_tree", "read", "write"],
    "orchestrator": ["calc", "search", "sh", "read", "write", "ls"],
}


class Friday:
    def __init__(self, cfg: Settings | None = None):
        if cfg is not None:
            self._cfg = cfg
        else:
            seed()
            self._cfg = load()
        self._bus = Bus()
        self._engine: Engine | None = None
        self._model: str = ""

    @property
    def bus(self) -> Bus:
        return self._bus

    def _ensure(self, model: str | None = None):
        if self._engine is not None:
            return
        model_name, eng = pick(model or self._cfg.model or None)
        self._model = model_name
        self._engine = eng

    def _load_procs(self, expert: str) -> list:
        names = _PROCS_MAP.get(expert, list(Catalog.names("proc")))
        procs = []
        for n in names:
            if Catalog.has("proc", n):
                try:
                    procs.append(Catalog.spawn("proc", n))
                except Exception as e:
                    log.debug("proc '%s' failed: %s", n, e)
        return procs

    def ask(self, query: str, *, expert: str | None = None, model: str | None = None) -> str:
        self._ensure(model)
        if not self._engine:
            return "No engine available."
        name = expert or self._cfg.expert
        if not Catalog.has("expert", name):
            return f"Unknown expert: {name}. Options: {Catalog.names('expert')}"
        procs = self._load_procs(name)
        agent = Catalog.spawn("expert", name, self._engine, self._model, procs=procs, bus=self._bus)
        try:
            result = agent.run(query)
            return result.text
        except Exception as e:
            log.warning("agent failed, retrying without procs: %s", e)
            agent2 = Catalog.spawn("expert", name, self._engine, self._model, procs=[], bus=self._bus)
            return agent2.run(query).text

    def engines(self) -> dict:
        eng = Engine()
        models = eng.models()
        return {"local": models}
