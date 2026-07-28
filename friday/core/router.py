from __future__ import annotations
import logging
from typing import Callable

logger = logging.getLogger("friday.core.router")

class AgentRouter:
    def __init__(self):
        self._routes: dict[str, tuple[Callable[[str], float], str]] = {}
        self._default: str | None = None

    def route(self, name: str, matcher: Callable[[str], float], agent_name: str):
        self._routes[name] = (matcher, agent_name)

    def set_default(self, agent_name: str):
        self._default = agent_name

    def resolve(self, user_input: str) -> str:
        best_score = 0.0
        best_agent = self._default
        for name, (matcher, agent_name) in self._routes.items():
            score = matcher(user_input)
            if score > best_score:
                best_score = score
                best_agent = agent_name
        return best_agent or "chat"
