import asyncio
import logging
from typing import Any, AsyncGenerator

from friday.config import get_config
from friday.router.fallback import FallbackHandler
from friday.router.model_registry import ModelRegistry
from friday.router.network import is_online, check_openrouter, check_zen
from friday.router.ollama_client import OllamaClient
from friday.router.zen_client import ZenClient

logger = logging.getLogger("friday.omniroute")


class OmniRouteClient:
    def __init__(self):
        self.config = get_config()
        self.model_registry = ModelRegistry()
        self.zen = ZenClient(self.config.opencode_zen_api_key)
        self.fallback_handler = FallbackHandler()
        self.ollama = OllamaClient()

    async def route(self, task_type: str, prompt: str, system_prompt: str = "") -> dict[str, Any]:
        net = await is_online()

        if net and self.config.opencode_zen_api_key:
            if await check_zen(self.config.opencode_zen_api_key):
                zen_model = self.model_registry.get_zen_model(task_type)
                logger.info("Online → Zen primary %s", zen_model)
                r = await self.zen.call_model(zen_model, prompt, system_prompt)
                if r.get("model") != "none":
                    return r
                for fb_model in self.model_registry.get_zen_fallback():
                    logger.info("Zen fallback %s", fb_model)
                    r = await self.zen.call_model(fb_model, prompt, system_prompt)
                    if r.get("model") != "none":
                        return r
                    await asyncio.sleep(0.1)
            else:
                logger.info("Zen auth failed")

        if net and self.config.openrouter_api_key:
            if await check_openrouter(self.config.openrouter_api_key):
                logger.info("Online → OpenRouter fallback")
                r = await self.fallback_handler.execute_with_fallback(
                    self.model_registry.get_or_fallback(), prompt, system_prompt, self.config.openrouter_api_key
                )
                if r.get("model") != "none":
                    return r
            else:
                logger.info("OpenRouter auth failed")

        logger.info("→ Ollama")
        return await self.ollama.generate(task_type, prompt, system_prompt)

    async def route_stream(self, task_type: str, prompt: str, system_prompt: str = "") -> AsyncGenerator[dict[str, Any], None]:
        net = await is_online()

        if net and self.config.opencode_zen_api_key:
            if await check_zen(self.config.opencode_zen_api_key):
                zen_model = self.model_registry.get_zen_model(task_type)
                logger.info("Online → Zen stream %s", zen_model)
                async for chunk in self.zen.call_model_stream(zen_model, prompt, system_prompt):
                    yield chunk
                    if chunk.get("done"):
                        return
                for fb_model in self.model_registry.get_zen_fallback():
                    logger.info("Zen fallback stream %s", fb_model)
                    async for chunk in self.zen.call_model_stream(fb_model, prompt, system_prompt):
                        yield chunk
                        if chunk.get("done"):
                            return
                    await asyncio.sleep(0.1)
            else:
                logger.info("Zen auth failed")

        if net and self.config.openrouter_api_key:
            if await check_openrouter(self.config.openrouter_api_key):
                logger.info("Online → OpenRouter stream")
                async for chunk in self.fallback_handler.execute_stream(
                    self.model_registry.get_or_fallback(), prompt, system_prompt, self.config.openrouter_api_key
                ):
                    yield chunk
                    if chunk.get("done"):
                        return
            else:
                logger.info("OpenRouter auth failed")

        logger.info("→ Ollama stream")
        async for chunk in self.ollama.generate_stream(task_type, prompt, system_prompt):
            yield chunk
