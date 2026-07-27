from abc import ABC
from typing import Any


class Plugin(ABC):
    name: str = "unnamed"
    version: str = "0.1.0"
    description: str = ""

    async def on_load(self, orchestrator: Any) -> None:
        pass

    async def on_unload(self, orchestrator: Any) -> None:
        pass
