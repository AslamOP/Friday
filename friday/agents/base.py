from dataclasses import dataclass, field
from typing import Any

@dataclass
class Task:
    type: str; input: str = ""; id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)

@dataclass
class Context:
    user_input: str; user_id: str = "default"
    conversation: list[dict] = field(default_factory=list)
    memory: dict[str, Any] = field(default_factory=dict)

@dataclass
class Result:
    success: bool; output: str; agent: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    subtasks: list[dict[str, str]] = field(default_factory=list)

class BaseAgent:
    name: str = "base"
    def __init__(self, model_preference: str = ""): self.model_preference = model_preference
    async def handle(self, task: Task, context: Context) -> Result: raise NotImplementedError
    async def can_handle(self, intent: str) -> float: return 0.0
