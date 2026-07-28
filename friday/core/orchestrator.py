from __future__ import annotations
import logging
from datetime import datetime

from friday.core.agent import Agent
from friday.core.memory import MemoryStore
from friday.core.router import AgentRouter
from friday.core.learning import LearningEngine

logger = logging.getLogger("friday.core.orchestrator")

class Orchestrator:
    def __init__(self):
        self.memory = MemoryStore()
        self.router = AgentRouter()
        self.learning = LearningEngine()
        self._agents: dict[str, Agent] = {}

    def register_agent(self, agent: Agent):
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> Agent | None:
        return self._agents.get(name)

    async def process(self, user_input: str, agent_name: str | None = None) -> str:
        if not agent_name:
            agent_name = self.router.resolve(user_input)

        agent = self._agents.get(agent_name)
        if not agent:
            agent = self._agents.get("chat")
        if not agent:
            return "No agent available."

        response = await agent.handle(user_input)
        self.memory.save_interaction(user_input, response, {"agent": agent_name})
        self.learning.record(user_input, response, agent_name)
        return response
