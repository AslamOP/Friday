import logging
from typing import Any, AsyncGenerator

from friday.router.provider_registry import ProviderRegistry

logger = logging.getLogger("friday.omniroute")


class OmniRouteClient:
    def __init__(self):
        self.registry = ProviderRegistry()

    async def route(self, task_type: str, prompt: str, system_prompt: str = "") -> dict[str, Any]:
        return await self.registry.route(task_type, prompt, system_prompt)

    async def route_stream(self, task_type: str, prompt: str, system_prompt: str = "") -> AsyncGenerator[dict[str, Any], None]:
        async for chunk in self.registry.route_stream(task_type, prompt, system_prompt):
            yield chunk
