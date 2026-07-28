from __future__ import annotations
import logging
from friday.core.agent import Agent

logger = logging.getLogger("friday.agents.research")

_RESEARCH_PROMPT = """You are FRIDAY's research division. You are a world-class research scientist.
You have access to web search and web fetch tools.
Always search for current information before answering.
Provide citations and synthesize findings from multiple sources.
Be thorough but concise. Address the user as "sir"."""

class ResearchAgent(Agent):
    name = "research"
    description = "Deep research with web search"

    def __init__(self, provider):
        super().__init__(provider)
        self.system_prompt = _RESEARCH_PROMPT

    async def handle(self, user_input: str, **kwargs) -> str:
        from friday.tools.web_search import WebSearch, WebFetch

        self.register_tools(WebSearch(), WebFetch())

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
