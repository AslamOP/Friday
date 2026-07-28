from __future__ import annotations
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("friday.router.provider")

_DATA_DIR = Path.home() / ".friday"
_PROVIDERS_FILE = _DATA_DIR / "providers.json"

DEFAULT_PROVIDERS = {
    "zen": {
        "type": "openai",
        "api_base": "https://api.zenmarket.ai/v1",
        "api_key": "",
        "models": ["openai/gpt-4o-mini"],
        "enabled": True,
    },
    "ollama": {
        "type": "openai",
        "api_base": "http://localhost:11434/v1",
        "api_key": "ollama",
        "models": [],
        "enabled": True,
    },
}

class ProviderRegistry:
    _instance: ProviderRegistry | None = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._cache: dict[str, tuple[float, list[str]]] = {}
        self._cache_ttl = 10.0
        self._providers: dict[str, dict] = {}
        self._load()
    
    def _load(self):
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        if _PROVIDERS_FILE.exists():
            self._providers = json.loads(_PROVIDERS_FILE.read_text())
        else:
            self._providers = dict(DEFAULT_PROVIDERS)
            self._save()
    
    def _save(self):
        _PROVIDERS_FILE.write_text(json.dumps(self._providers, indent=2))
    
    def get_providers(self) -> dict[str, dict]:
        return dict(self._providers)
    
    def get_provider(self, name: str) -> dict | None:
        return self._providers.get(name)
    
    def set_key(self, name: str, key: str):
        if name in self._providers:
            self._providers[name]["api_key"] = key
            self._save()
    
    def _can_work(self, p: dict) -> bool:
        needs_key = {"openai", "anthropic", "gemini"}
        if p.get("type") in needs_key and not p.get("api_key"):
            return False
        return p.get("enabled", True)
    
    async def _probe_models(self, name: str, p: dict) -> list[str]:
        try:
            base = p["api_base"].rstrip("/")
            headers = {"Authorization": f"Bearer {p.get('api_key', '')}"}
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{base}/models", headers=headers)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", [])]
                    logger.info("Probed %s: %d models", name, len(models))
                    return models
                else:
                    logger.warning("Probe %s returned %d", name, resp.status_code)
                    return p.get("models", [])
        except Exception as e:
            logger.debug("Probe %s failed: %s", name, e)
            return p.get("models", [])
    
    async def get_available_models(self) -> dict[str, list[str]]:
        result = {}
        for name, p in self._providers.items():
            if not self._can_work(p):
                continue
            now = time.time()
            if name in self._cache and now - self._cache[name][0] < self._cache_ttl:
                result[name] = self._cache[name][1]
                continue
            models = await self._probe_models(name, p)
            self._cache[name] = (now, models)
            result[name] = models
        return result
    
    async def route(self, prompt: str, system_prompt: str = "", tools: list[dict] | None = None) -> str:
        available = await self.get_available_models()
        
        for pname, models in available.items():
            p = self._providers[pname]
            base = p["api_base"].rstrip("/")
            headers = {
                "Authorization": f"Bearer {p.get('api_key', '')}",
                "Content-Type": "application/json",
            }
            
            for model in models:
                body: dict[str, Any] = {
                    "model": model,
                    "messages": [],
                    "max_tokens": 2048,
                }
                if system_prompt:
                    body["messages"].append({"role": "system", "content": system_prompt})
                body["messages"].append({"role": "user", "content": prompt})
                
                if tools:
                    body["tools"] = tools
                    body["tool_choice"] = "auto"
                
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.post(f"{base}/chat/completions", json=body, headers=headers)
                        if resp.status_code in (200, 201):
                            data = resp.json()
                            msg = data["choices"][0]["message"]
                            if msg.get("tool_calls"):
                                return {
                                    "content": msg.get("content", ""),
                                    "tool_calls": [
                                        {
                                            "id": tc.get("id", ""),
                                            "name": tc["function"]["name"],
                                            "arguments": json.loads(tc["function"]["arguments"]),
                                        }
                                        for tc in msg["tool_calls"]
                                    ],
                                }
                            return msg.get("content", "")
                        else:
                            logger.warning("%s/%s returned %d: %s", pname, model, resp.status_code, resp.text[:200])
                except Exception as e:
                    logger.debug("%s/%s error: %s", pname, model, e)
                    continue
        
        return "I'm sorry, sir. I cannot reach any language model provider right now. Please check your connection and provider configuration."
    
    async def complete(self, messages: list[dict], tools: list[dict] | None = None) -> str | dict:
        available = await self.get_available_models()
        
        for pname, models in available.items():
            p = self._providers[pname]
            base = p["api_base"].rstrip("/")
            headers = {
                "Authorization": f"Bearer {p.get('api_key', '')}",
                "Content-Type": "application/json",
            }
            
            for model in models:
                body: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 4096,
                }
                if tools:
                    body["tools"] = tools
                    body["tool_choice"] = "auto"
                
                try:
                    async with httpx.AsyncClient(timeout=60) as client:
                        resp = await client.post(f"{base}/chat/completions", json=body, headers=headers)
                        if resp.status_code in (200, 201):
                            data = resp.json()
                            msg = data["choices"][0]["message"]
                            if msg.get("tool_calls"):
                                return {
                                    "content": msg.get("content", ""),
                                    "tool_calls": [
                                        {
                                            "id": tc.get("id", ""),
                                            "name": tc["function"]["name"],
                                            "arguments": json.loads(tc["function"]["arguments"]),
                                        }
                                        for tc in msg["tool_calls"]
                                    ],
                                }
                            return msg.get("content", "")
                        else:
                            logger.warning("%s/%s returned %d: %s", pname, model, resp.status_code, resp.text[:200])
                except Exception as e:
                    logger.debug("%s/%s error: %s", pname, model, e)
                    continue
        
        return "I apologise, sir, but I am unable to reach any language model at this time."
