import json
import logging
from typing import Any, AsyncGenerator
import httpx

logger = logging.getLogger("friday.ollama_client")
_URL = "http://127.0.0.1:11434"
_DEFAULT = "llama3.2"
_TASK_MODELS = {
    "code": "codellama", "research": "llama3.2", "plan": "llama3.2",
    "study": "llama3.2", "challenge": "llama3.2", "knowledge": "llama3.2",
    "automate": "codellama", "chat": "llama3.2",
}


class OllamaClient:
    def __init__(self, base_url: str = _URL):
        self.base_url = base_url.rstrip("/")

    def get_model(self, task_type: str) -> str:
        return _TASK_MODELS.get(task_type, _DEFAULT)

    async def generate(self, task_type: str, prompt: str, system_prompt: str = "") -> dict[str, Any]:
        model = self.get_model(task_type)
        payload = {"model": model, "prompt": prompt, "stream": False}
        if system_prompt:
            payload["system"] = system_prompt
        try:
            r = await httpx.AsyncClient(timeout=120.0).post(f"{self.base_url}/api/generate", json=payload)
            r.raise_for_status()
            d = r.json()
            return {"content": d.get("response", ""), "model": f"ollama:{model}", "usage": {}}
        except Exception as e:
            logger.warning("Ollama '%s' failed: %s", model, e)
            return {"content": "", "model": f"ollama:{model}", "usage": {}}

    async def generate_stream(self, task_type: str, prompt: str, system_prompt: str = "") -> AsyncGenerator[dict[str, Any], None]:
        model = self.get_model(task_type)
        payload = {"model": model, "prompt": prompt, "stream": True}
        if system_prompt:
            payload["system"] = system_prompt
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                yield {"token": token, "model": f"ollama:{model}", "done": False}
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
            yield {"token": "", "model": f"ollama:{model}", "done": True}
        except Exception as e:
            logger.warning("Ollama stream '%s' failed: %s", model, e)
            yield {"token": "", "model": "none", "done": True}

    async def is_available(self) -> bool:
        try:
            return (await httpx.AsyncClient(timeout=2.0).get(f"{self.base_url}/api/tags")).status_code == 200
        except Exception:
            return False
