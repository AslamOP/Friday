import asyncio
import json
import logging
from typing import Any, AsyncGenerator

from friday.router.cost_tracker import CostTracker

logger = logging.getLogger("friday.fallback_handler")
_OR_URL = "https://openrouter.ai/api/v1/chat/completions"


class FallbackHandler:
    def __init__(self):
        self.cost_tracker = CostTracker()

    async def _call(self, model: str, prompt: str, system_prompt: str, api_key: str, base_url: str = "") -> dict[str, Any] | None:
        try:
            import httpx
            url = (base_url.rstrip("/") + "/chat/completions") if base_url else _OR_URL

            r = await httpx.AsyncClient(timeout=15.0).post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            r.raise_for_status()
            d = r.json()
            u = d.get("usage", {})
            self.cost_tracker.log_usage(
                model=model, tokens_in=u.get("prompt_tokens", 0), tokens_out=u.get("completion_tokens", 0)
            )
            return {"content": d["choices"][0]["message"]["content"], "model": model, "usage": u}
        except Exception as e:
            logger.warning("Model '%s' failed: %s", model, e)
            self.cost_tracker.log_usage(model=model, tokens_in=0, tokens_out=0, success=False)
            return None

    async def execute_with_fallback(self, models: list[str], prompt: str, system_prompt: str = "", api_key: str = "", base_url: str = "") -> dict[str, Any]:
        if not api_key:
            return {"content": "No API key configured.", "model": "none", "usage": {}}
        for m in models:
            r = await self._call(m, prompt, system_prompt, api_key, base_url)
            if r is not None:
                return r
            await asyncio.sleep(0.5)
        return {"content": "All models failed.", "model": "none", "usage": {}}

    async def execute_stream(self, models: list[str], prompt: str, system_prompt: str = "", api_key: str = "", base_url: str = "") -> AsyncGenerator[dict[str, Any], None]:
        if not api_key:
            yield {"token": "", "model": "none", "done": True}
            return
        for m in models:
            try:
                import httpx
                url = (base_url.rstrip("/") + "/chat/completions") if base_url else _OR_URL

                async with httpx.AsyncClient(timeout=30.0) as client:
                    async with client.stream(
                        "POST",
                        url,
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={
                            "model": m,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt},
                            ],
                            "stream": True,
                        },
                    ) as resp:
                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:].strip()
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                choices = chunk.get("choices") or []
                                if not choices:
                                    continue
                                token = choices[0].get("delta", {}).get("content", "")
                                if token:
                                    yield {"token": token, "model": m, "done": False}
                            except (json.JSONDecodeError, IndexError, KeyError):
                                continue
                yield {"token": "", "model": m, "done": True}
                return
            except Exception as e:
                logger.warning("OpenRouter stream '%s' failed: %s", m, e)
                await asyncio.sleep(0.5)
        yield {"token": "", "model": "none", "done": True}
