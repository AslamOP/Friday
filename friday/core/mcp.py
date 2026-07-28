from __future__ import annotations
import json
import logging
from typing import Any

logger = logging.getLogger("friday.core.mcp")

class MCPClient:
    def __init__(self, server_url: str = ""):
        self.server_url = server_url
        self._tools: dict[str, dict] = {}

    def register_tool(self, name: str, schema: dict, handler=None):
        self._tools[name] = {"schema": schema, "handler": handler}

    def list_tools(self) -> list[dict]:
        return [t["schema"] for t in self._tools.values()]

    async def call_tool(self, name: str, arguments: dict) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Unknown MCP tool: {name}")
        if tool["handler"]:
            return tool["handler"](**arguments)
        return {"error": f"No handler for {name}"}
