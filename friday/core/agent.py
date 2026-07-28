from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from friday.core.tool import Tool

logger = logging.getLogger("friday.core.agent")

@dataclass
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    name: str | None = None
    tool_call_id: str | None = None

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]

class Agent(ABC):
    name: str = "base"
    description: str = "Base agent"
    system_prompt: str = "You are FRIDAY, a JARVIS-class AI assistant."

    def __init__(self, provider):
        self.provider = provider
        self.messages: list[Message] = []
        self.tools: dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def register_tools(self, *tools: Tool):
        for t in tools:
            self.register_tool(t)

    @abstractmethod
    async def handle(self, user_input: str, **kwargs) -> str:
        ...

    def _build_tool_schemas(self) -> list[dict]:
        return [t.openai_schema() for t in self.tools.values()]

    def _execute_tool(self, name: str, args: dict) -> str:
        tool = self.tools.get(name)
        if not tool:
            return f"Error: tool '{name}' not found"
        try:
            result = tool.run(**args)
            return str(result)
        except Exception as e:
            logger.exception("Tool %s failed", name)
            return f"Error executing {name}: {e}"
