from __future__ import annotations
import logging
from friday.core.agent import Agent

logger = logging.getLogger("friday.agents.study")

_STUDY_PROMPT = """You are FRIDAY's study mentor. You help the user learn and understand concepts.
You are patient, thorough, and use the Socratic method.
Provide explanations with analogies and examples.
Test understanding with questions. Address the user as "sir"."""

class StudyAgent(Agent):
    name = "study"
    description = "Study mentor for learning"

    def __init__(self, provider):
        super().__init__(provider)
        self.system_prompt = _STUDY_PROMPT

    async def handle(self, user_input: str, **kwargs) -> str:
        from friday.tools.web_search import WebSearch
        from friday.tools.think import Think

        self.register_tools(WebSearch(), Think())

        messages: list[dict] = [{"role": "system", "content": self.system_prompt}]
        for msg in self.messages[-6:]:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_input})

        response = await self.provider(messages)

        text = response if isinstance(response, str) else response.get("content", str(response))
        self.messages.append(Message(role="user", content=user_input))
        self.messages.append(Message(role="assistant", content=text))
        return text
