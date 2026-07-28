from __future__ import annotations
import logging
from friday.core.agent import Agent

logger = logging.getLogger("friday.agents.gaming")

_GAMING_PROMPT = """You are FRIDAY's gaming assistant.
You help with game strategies, walkthroughs, and lore.
You have knowledge of game mechanics and can search for current info.
Address the user as "sir"."""

class GamingAgent(Agent):
    name = "gaming"
    description = "Gaming assistant for strategies and walkthroughs"

    def __init__(self, provider):
        super().__init__(provider)
        self.system_prompt = _GAMING_PROMPT

    async def handle(self, user_input: str, **kwargs) -> str:
        from friday.tools.web_search import WebSearch

        self.register_tools(WebSearch())

        messages: list[dict] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]

        response = await self.provider(messages, tools=self._build_tool_schemas())

        if isinstance(response, dict) and "tool_calls" in response:
            for tc in response["tool_calls"]:
                result = self._execute_tool(tc["name"], tc["arguments"])
                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tc.get("id", ""),
                })
            response = await self.provider(messages)

        return response if isinstance(response, str) else response.get("content", str(response))
