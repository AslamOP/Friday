"""Tool system — base class, spec, and dispatch executor."""

from __future__ import annotations

import concurrent.futures
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

from friday._types import Call, Outcome

log = logging.getLogger("friday.tools")


@dataclass
class Spec:
    name: str
    desc: str
    params: dict = field(default_factory=dict)
    sensitive: bool = False
    timeout: float = 30.0


class Proc(ABC):
    label: str = ""

    @property
    @abstractmethod
    def spec(self) -> Spec:
        ...

    @abstractmethod
    def run(self, **kwargs) -> Outcome:
        ...

    def openai_def(self) -> dict:
        s = self.spec
        return {
            "type": "function",
            "function": {"name": s.name, "description": s.desc, "parameters": s.params},
        }


class Dispatcher:
    def __init__(self, procs: list[Proc], confirm: Callable[[str], bool] | None = None):
        self._index = {p.spec.name: p for p in procs}
        self._confirm = confirm

    def dispatch(self, call: Call) -> Outcome:
        proc = self._index.get(call.action)
        if not proc:
            return Outcome(action=call.action, text=f"unknown: {call.action}", ok=False)
        try:
            params = json.loads(call.args) if isinstance(call.args, str) else (call.args or {})
        except json.JSONDecodeError as e:
            return Outcome(action=call.action, text=f"bad args: {e}", ok=False)
        spec = proc.spec
        if spec.sensitive and self._confirm:
            if not self._confirm(f"Run {call.action} with {params}?"):
                return Outcome(action=call.action, text="denied", ok=False)
        t0 = time.time()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                f = pool.submit(proc.run, **params)
                result = f.result(timeout=spec.timeout)
        except concurrent.futures.TimeoutError:
            result = Outcome(action=call.action, text=f"timed out ({spec.timeout}s)", ok=False)
        except Exception as e:
            result = Outcome(action=call.action, text=f"error: {e}", ok=False)
        result.elapsed = time.time() - t0
        result.meta["args"] = params
        return result

    def openai_tools(self) -> list[dict]:
        return [p.openai_def() for p in self._index.values()]
