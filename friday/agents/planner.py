from __future__ import annotations
import logging
from friday.core.agent import Agent

logger = logging.getLogger("friday.agents.planner")

_PLANNER_PROMPT = """You are FRIDAY's planning division.
You break down complex projects into actionable steps.
Create timelines, identify dependencies, and track progress.
Be structured and practical. Address the user as "sir"."""

class PlannerAgent(Agent):
    name = "planner"
    description = "Project planning and timelines"

    def __init__(self, provider):
        super().__init__(provider)
        self.system_prompt = _PLANNER_PROMPT

    async def handle(self, user_input: str, **kwargs) -> str:
        messages: list[dict] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        response = await self.provider(messages)
        return response if isinstance(response, str) else response.get("content", str(response))
