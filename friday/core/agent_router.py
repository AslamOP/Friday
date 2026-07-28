import logging

from friday.agents.base import BaseAgent, Context, Result
from friday.core.intent_parser import Intent

logger = logging.getLogger("friday.agent_router")

class _Default(BaseAgent):
    name = "default"
    async def handle(self, task, context): return Result(success=True, output=f"No specialized agent for '{context.user_input}'", agent=self.name)
    async def can_handle(self, intent): return 0.0

class AgentRouter:
    def __init__(self):
        self._agents: list[BaseAgent] = []
        self._default = _Default()

    def register_agent(self, agent):
        self._agents.append(agent)
        logger.info("Agent: %s", agent.name)

    def unregister_agent(self, name):
        self._agents = [a for a in self._agents if a.name != name]

    async def route(self, intent: Intent, context: Context | None = None) -> BaseAgent:  # noqa: N802
        if not self._agents:
            return self._default

        best, best_score = None, 0.0
        for a in self._agents:
            s = await a.can_handle(intent.type)
            if s > best_score:
                best_score, best = s, a

        if best is None or best_score < 0.3:
            return self._default
        return best
