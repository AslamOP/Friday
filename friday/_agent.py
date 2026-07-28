"""Agent loop — multi-turn reasoning with tool calls."""

from __future__ import annotations

import concurrent.futures
import re

from friday._engine import Engine
from friday._events import Bus
from friday._tools import Dispatcher, Proc
from friday._types import Call, Context, Outcome, Turn


def _strip_think(t: str) -> str:
    t = re.sub(r"<think>.*?</response>\s*", "", t, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r"^.*?</response>\s*", "", t, flags=re.DOTALL | re.IGNORECASE)
    return t.strip()


def _sys_block(prompt: str) -> dict:
    return {"role": "system", "content": prompt}


class Agent:
    """Multi-turn agent that calls tools until it has an answer."""

    def __init__(
        self,
        engine: Engine,
        model: str,
        procs: list[Proc] | None = None,
        *,
        prompt: str = "",
        rounds: int = 10,
        temp: float = 0.7,
        tokens: int = 2048,
        parallel: bool = True,
        bus: Bus | None = None,
    ):
        self._eng = engine
        self._model = model
        self._procs = procs or []
        self._dispatch = Dispatcher(self._procs)
        self._prompt = prompt or "You are a helpful assistant. Use tools when appropriate."
        self._rounds = rounds
        self._temp = temp
        self._tokens = tokens
        self._parallel = parallel
        self._bus = bus

    def _fire(self, event: str, data: dict | None = None):
        if self._bus:
            self._bus.fire(event, data or {})

    def run(self, query: str, ctx: Context | None = None) -> Turn:
        self._fire("agent.start", {"query": query})
        msgs = [_sys_block(self._prompt)]
        if ctx:
            for e in ctx.history:
                msgs.append({"role": e.author.value, "content": e.text})
        msgs.append({"role": "user", "content": query})
        openai_tools = self._dispatch.openai_tools() if self._procs else []
        all_outcomes: list[Outcome] = []
        rounds = 0

        for _ in range(self._rounds):
            rounds += 1
            kw: dict = {}
            if openai_tools:
                kw["tools"] = openai_tools
            result = self._eng.chat(msgs, model=self._model, temp=self._temp, max_tokens=self._tokens, **kw)

            text = result.get("text", "")
            calls_raw = result.get("calls", [])

            if not calls_raw:
                text = _strip_think(text)
                self._fire("agent.end", {"rounds": rounds})
                return Turn(text=text, results=all_outcomes, rounds=rounds)

            calls = [Call(ref=c.get("id", f"c_{i}"), action=c.get("fn", ""), args=c.get("args", "{}")) for i, c in enumerate(calls_raw)]
            msgs.append({"role": "assistant", "content": text, "tool_calls": calls_raw})

            if self._parallel and len(calls) > 1:

                def _exec(c: Call) -> tuple[Call, Outcome]:
                    return c, self._dispatch.dispatch(c)

                with concurrent.futures.ThreadPoolExecutor(max_workers=len(calls)) as pool:
                    fs = {pool.submit(_exec, c): c for c in calls}
                    by_id = {}
                    for f in concurrent.futures.as_completed(fs):
                        oc = fs[f]
                        by_id[id(oc)] = f.result()
                    for c in calls:
                        _, oc = by_id[id(c)]
                        all_outcomes.append(oc)
                        msgs.append({"role": "tool", "content": oc.text, "tool_call_id": c.ref, "name": c.action})
            else:
                for c in calls:
                    oc = self._dispatch.dispatch(c)
                    all_outcomes.append(oc)
                    msgs.append({"role": "tool", "content": oc.text, "tool_call_id": c.ref, "name": c.action})

        txt = "Reached max rounds without final answer."
        self._fire("agent.end", {"rounds": rounds, "exceeded": True})
        return Turn(text=txt, results=all_outcomes, rounds=rounds, meta={"exceeded": True})
