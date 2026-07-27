import json
import logging
from typing import Any, AsyncGenerator
import httpx

logger = logging.getLogger("friday.zen_client")
_ZEN_URL = "https://opencode.ai/zen/v1/chat/completions"

_TASK_MODELS = {
    "code": "north-mini-code-free",
    "automate": "north-mini-code-free",
    "research": "nemotron-3-ultra-free",
    "study": "nemotron-3-ultra-free",
    "challenge": "nemotron-3-ultra-free",
    "plan": "deepseek-v4-flash-free",
    "knowledge": "deepseek-v4-flash-free",
    "gaming": "deepseek-v4-flash-free",
    "chat": "deepseek-v4-flash-free",
}


class ZenClient:
    def __init__(self, api_key: str, base_url: str = _ZEN_URL):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def get_model(self, task_type: str) -> str:
        return _TASK_MODELS.get(task_type, "deepseek-v4-flash-free")

    def _build_payload(self, model: str, prompt: str, system_prompt: str, stream: bool = False) -> dict:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
        }
        if system_prompt:
            payload["messages"].insert(0, {"role": "system", "content": system_prompt})
        return payload

    async def generate(self, task_type: str, prompt: str, system_prompt: str = "") -> dict[str, Any]:
        return await self.call_model(self.get_model(task_type), prompt, system_prompt)

    async def call_model(self, model: str, prompt: str, system_prompt: str = "") -> dict[str, Any]:
        payload = self._build_payload(model, prompt, system_prompt, stream=False)
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            r = await httpx.AsyncClient(timeout=8.0).post(
                self.base_url, headers=headers,
                json=payload,
            )
            r.raise_for_status()
            d = r.json()
            return {
                "content": d["choices"][0]["message"]["content"],
                "model": f"zen:{model}",
                "usage": d.get("usage", {}),
            }
        except Exception as e:
            logger.debug("Zen model '%s' failed: %s", model, e)
            return {"content": "", "model": "none", "usage": {}}

    async def generate_stream(self, task_type: str, prompt: str, system_prompt: str = "") -> AsyncGenerator[dict[str, Any], None]:
        model = self.get_model(task_type)
        async for chunk in self.call_model_stream(model, prompt, system_prompt):
            yield chunk

    async def call_model_stream(self, model: str, prompt: str, system_prompt: str = "") -> AsyncGenerator[dict[str, Any], None]:
        payload = self._build_payload(model, prompt, system_prompt, stream=True)
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST", self.base_url, headers=headers,
                    json=payload,
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
                                yield {"token": token, "model": f"zen:{model}", "done": False}
                        except (json.JSONDecodeError, IndexError, KeyError):
                            continue
            yield {"token": "", "model": f"zen:{model}", "done": True}
        except Exception as e:
            logger.debug("Zen stream '%s' failed: %s", model, e)
            yield {"token": "", "model": "none", "done": True}
