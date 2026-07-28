"""LLM engine — talks to any OpenAI-compatible API."""

from __future__ import annotations

import json
import logging

import httpx

from friday._config import load

log = logging.getLogger("friday.engine")

_EXCLUDE = {"embed", "nomic-embed", "text-embedding", "ada", "babbage", "instructor"}


def _valid(m: str) -> bool:
    low = m.lower()
    return not any(x in low for x in _EXCLUDE)


class Engine:
    def __init__(self, url: str = "", key: str = ""):
        self._url = url.rstrip("/") or "http://localhost:11434/v1"
        self._key = key or ""
        self._cache: list[str] = []

    def models(self) -> list[str]:
        headers = {}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        try:
            r = httpx.get(f"{self._url}/models", headers=headers, timeout=5)
            if r.status_code in (200, 201):
                all_m = [m["id"] for m in r.json().get("data", [])]
                self._cache = [m for m in all_m if _valid(m)]
                return self._cache
        except Exception:
            pass
        return self._cache

    def chat(
        self,
        messages: list[dict],
        *,
        model: str = "",
        temp: float = 0.7,
        max_tokens: int = 2048,
        tools: list[dict] | None = None,
    ) -> dict:
        if not model:
            available = self.models()
            chat = [m for m in available if _valid(m)]
            model = chat[0] if chat else (available[0] if available else "default")
        headers = {"Content-Type": "application/json"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        body: dict = {
            "model": model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_tokens,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        try:
            r = httpx.post(f"{self._url}/chat/completions", json=body, headers=headers, timeout=120)
            if r.status_code in (200, 201):
                data = r.json()
                choice = data["choices"][0]["message"]
                out = {"text": choice.get("content", ""), "reason": data["choices"][0].get("finish_reason", "")}
                if choice.get("tool_calls"):
                    out["calls"] = [
                        {"id": tc["id"], "fn": tc["function"]["name"], "args": json.loads(tc["function"]["arguments"])}
                        for tc in choice["tool_calls"]
                    ]
                if "usage" in data:
                    out["usage"] = data["usage"]
                return out
            if r.status_code == 400 and tools:
                log.debug("tools rejected, retrying plain")
                body.pop("tools", None)
                body.pop("tool_choice", None)
                r2 = httpx.post(f"{self._url}/chat/completions", json=body, headers=headers, timeout=120)
                if r2.status_code in (200, 201):
                    d2 = r2.json()
                    return {"text": d2["choices"][0]["message"].get("content", ""), "reason": d2["choices"][0].get("finish_reason", "")}
            log.warning("API %d: %s", r.status_code, r.text[:200])
        except Exception as e:
            log.debug("chat error: %s", e)
        return {"text": "", "reason": "error"}


def pick(model: str | None = None) -> tuple[str, Engine]:
    cfg = load()
    url = ""
    key = ""
    prov = cfg.endpoints.get(cfg.provider, {})
    url = prov.get("url", "")
    key = prov.get("key", "")
    eng = Engine(url, key)
    if model:
        return model, eng
    available = eng.models()
    chat = [m for m in available if _valid(m)]
    chosen = chat[0] if chat else (available[0] if available else "")
    return chosen, eng
