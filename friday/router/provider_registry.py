import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger("friday.provider_registry")


@dataclass
class ProviderConfig:
    name: str
    type: str  # "local" or "cloud"
    endpoint: str = ""
    api_key: str = ""
    models: list[str] = field(default_factory=list)
    priority: int = 10
    enabled: bool = True
    status: str = "unknown"  # "online", "offline", "unknown"


_DEFAULTS: list[ProviderConfig] = [
    ProviderConfig(name="ollama", type="local", endpoint="http://127.0.0.1:11434",
                   models=["llama3.2", "codellama", "nomic-embed-text"],
                   priority=30, status="unknown"),
    ProviderConfig(name="zen", type="cloud", endpoint="https://opencode.ai/zen/v1",
                   models=["north-mini-code-free", "nemotron-3-ultra-free",
                           "deepseek-v4-flash-free", "big-pickle", "mimo-v2.5-free",
                           "ling-3.0-flash-free", "laguna-s-2.1-free"],
                   priority=10, status="unknown"),
    ProviderConfig(name="openrouter", type="cloud", endpoint="https://openrouter.ai/api/v1",
                   models=["inclusionai/ling-3.0-flash:free",
                           "poolside/laguna-xs-2.1:free",
                           "poolside/laguna-m.1:free",
                           "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
                           "google/gemma-4-26b-a4b-it:free",
                           "nvidia/nemotron-3-super-120b-a12b:free",
                           "nvidia/nemotron-3-nano-30b-a3b:free",
                           "nvidia/nemotron-nano-12b-v2-vl:free",
                           "nvidia/nemotron-nano-9b-v2:free",
                           "openai/gpt-oss-20b:free"],
                   priority=20, status="unknown"),
]


class ProviderRegistry:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, path: str | Path | None = None):
        if hasattr(self, "_providers"):
            return
        self._path = Path(path) if path else Path("data/providers.json")
        self._providers: dict[str, ProviderConfig] = {}
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text())
                for d in raw:
                    p = ProviderConfig(**d)
                    self._providers[p.name] = p
                logger.info("Loaded %d providers from %s", len(self._providers), self._path)
                return
            except Exception as e:
                logger.warning("Failed to load providers: %s", e)
        for p in _DEFAULTS:
            self._providers[p.name] = p
        self._load_keys_from_env()
        self._save()

    def _load_keys_from_env(self):
        env_path = Path(".env")
        if not env_path.exists():
            return
        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip().lower()
                    v = v.strip().strip("\"'")
                    if k == "opencode_zen_api_key" and v:
                        self._providers["zen"].api_key = v
                    elif k == "openrouter_api_key" and v:
                        self._providers["openrouter"].api_key = v
                    elif k == "ollama_url" and v:
                        self._providers["ollama"].endpoint = v
        except Exception as e:
            logger.warning("Failed to load .env keys: %s", e)

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(p) for p in self._providers.values()]
        self._path.write_text(json.dumps(data, indent=2))

    def list_providers(self) -> list[ProviderConfig]:
        return sorted(self._providers.values(), key=lambda p: p.priority)

    def get_provider(self, name: str) -> ProviderConfig | None:
        return self._providers.get(name)

    def add_provider(self, name: str, type: str, endpoint: str = "",
                     api_key: str = "", models: list[str] | None = None,
                     priority: int = 50) -> ProviderConfig:
        p = ProviderConfig(name=name, type=type, endpoint=endpoint,
                           api_key=api_key, models=models or [],
                           priority=priority)
        self._providers[name] = p
        self._save()
        logger.info("Added provider: %s (%s)", name, type)
        return p

    def remove_provider(self, name: str) -> bool:
        if name in ("ollama", "zen", "openrouter"):
            logger.warning("Cannot remove default provider: %s", name)
            return False
        if name in self._providers:
            del self._providers[name]
            self._save()
            logger.info("Removed provider: %s", name)
            return True
        return False

    def set_key(self, name: str, api_key: str):
        p = self._providers.get(name)
        if p:
            p.api_key = api_key
            self._save()

    def set_enabled(self, name: str, enabled: bool):
        p = self._providers.get(name)
        if p:
            p.enabled = enabled
            self._save()

    def get_online_providers(self) -> list[ProviderConfig]:
        return [p for p in self.list_providers()
                if p.enabled and p.status == "online"]

    async def check_status(self, name: str) -> str:
        p = self._providers.get(name)
        if not p:
            return "unknown"
        if p.type == "local":
            try:
                import httpx
                async with httpx.AsyncClient(timeout=3) as c:
                    r = await c.get(f"{p.endpoint}/api/tags")
                    p.status = "online" if r.status_code == 200 else "offline"
            except Exception:
                p.status = "offline"
        else:
            if not p.api_key:
                p.status = "offline"
            else:
                try:
                    import httpx
                    headers = {"Authorization": f"Bearer {p.api_key}"}
                    if name == "zen":
                        url = f"{p.endpoint}/models"
                    elif name == "openrouter":
                        url = f"{p.endpoint}/auth/key"
                    else:
                        url = f"{p.endpoint}/models"
                    async with httpx.AsyncClient(timeout=3) as c:
                        r = await c.get(url, headers=headers)
                        p.status = "online" if r.status_code in (200, 201) else "offline"
                except Exception:
                    p.status = "offline"
        self._save()
        return p.status

    async def check_all(self):
        for p in self.list_providers():
            await self.check_status(p.name)

    async def route(self, task_type: str, prompt: str, system_prompt: str = "") -> dict[str, Any]:
        await self.check_all()
        for p in self.get_online_providers():
            logger.info("Trying %s (%s)", p.name, p.type)
            result = await self._call(p, task_type, prompt, system_prompt)
            if result.get("model") != "none" and result.get("content"):
                return result
        return {"model": "none", "content": "No provider available", "role": "assistant"}

    async def route_stream(self, task_type: str, prompt: str, system_prompt: str = ""):
        await self.check_all()
        for p in self.get_online_providers():
            logger.info("Trying stream %s (%s)", p.name, p.type)
            async for chunk in self._call_stream(p, task_type, prompt, system_prompt):
                yield chunk
                if chunk.get("done"):
                    return
        yield {"model": "none", "content": "", "done": True}

    async def _call(self, provider: ProviderConfig, task_type: str,
                    prompt: str, system_prompt: str) -> dict[str, Any]:
        try:
            if provider.name == "zen":
                from friday.router.zen_client import ZenClient
                client = ZenClient(provider.api_key, base_url=provider.endpoint)
                model = provider.models[0] if provider.models else "deepseek-v4-flash-free"
                return await client.call_model(model, prompt, system_prompt)
            elif provider.name == "openrouter":
                from friday.router.fallback import FallbackHandler
                handler = FallbackHandler()
                return await handler.execute_with_fallback(
                    provider.models, prompt, system_prompt, provider.api_key, base_url=provider.endpoint
                )
            elif provider.name == "ollama":
                from friday.router.ollama_client import OllamaClient
                client = OllamaClient(base_url=provider.endpoint)
                return await client.generate(task_type, prompt, system_prompt)
            else:
                return await self._call_openai_compat(provider, prompt, system_prompt)
        except Exception as e:
            logger.warning("Provider %s failed: %s", provider.name, e)
            return {"model": "none", "content": "", "role": "assistant"}

    async def _call_stream(self, provider: ProviderConfig, task_type: str,
                           prompt: str, system_prompt: str):
        try:
            if provider.name == "zen":
                from friday.router.zen_client import ZenClient
                client = ZenClient(provider.api_key, base_url=provider.endpoint)
                model = provider.models[0] if provider.models else "deepseek-v4-flash-free"
                async for chunk in client.call_model_stream(model, prompt, system_prompt):
                    yield chunk
                    if chunk.get("done"):
                        return
            elif provider.name == "openrouter":
                from friday.router.fallback import FallbackHandler
                handler = FallbackHandler()
                async for chunk in handler.execute_stream(
                    provider.models, prompt, system_prompt, provider.api_key, base_url=provider.endpoint
                ):
                    yield chunk
                    if chunk.get("done"):
                        return
            elif provider.name == "ollama":
                from friday.router.ollama_client import OllamaClient
                client = OllamaClient(base_url=provider.endpoint)
                async for chunk in client.generate_stream(task_type, prompt, system_prompt):
                    yield chunk
                    if chunk.get("done"):
                        return
            else:
                async for chunk in self._call_openai_compat_stream(provider, prompt, system_prompt):
                    yield chunk
                    if chunk.get("done"):
                        return
        except Exception as e:
            logger.warning("Stream %s failed: %s", provider.name, e)
            yield {"model": "none", "content": "", "done": True}

    async def _call_openai_compat(self, provider: ProviderConfig,
                                  prompt: str, system_prompt: str) -> dict[str, Any]:
        import httpx
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        model = provider.models[0] if provider.models else "gpt-3.5-turbo"
        headers = {"Content-Type": "application/json"}
        if provider.api_key:
            headers["Authorization"] = f"Bearer {provider.api_key}"
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{provider.endpoint}/chat/completions",
                json={"model": model, "messages": messages},
                headers=headers,
            )
            if r.status_code == 200:
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                return {"model": model, "content": content, "role": "assistant"}
            return {"model": "none", "content": "", "role": "assistant"}

    async def _call_openai_compat_stream(self, provider: ProviderConfig,
                                          prompt: str, system_prompt: str):
        import httpx
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        model = provider.models[0] if provider.models else "gpt-3.5-turbo"
        headers = {"Content-Type": "application/json"}
        if provider.api_key:
            headers["Authorization"] = f"Bearer {provider.api_key}"
        async with httpx.AsyncClient(timeout=30) as c:
            async with c.stream(
                "POST",
                f"{provider.endpoint}/chat/completions",
                json={"model": model, "messages": messages, "stream": True},
                headers=headers,
            ) as r:
                if r.status_code != 200:
                    yield {"model": "none", "content": "", "done": True}
                    return
                async for line in r.aiter_lines():
                    if not line or line.startswith(":") or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield {"model": model, "content": content, "done": False}
                        except json.JSONDecodeError:
                            continue
                yield {"model": model, "content": "", "done": True}
