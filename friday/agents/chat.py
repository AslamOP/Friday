from __future__ import annotations
import logging
from friday.core.agent import Agent

logger = logging.getLogger("friday.agents.chat")

_CHAT_PROMPT = """You are FRIDAY, a JARVIS-class AI personal assistant.
You are helpful, concise, and efficient. You speak with a slightly British tone.
Address the user as "sir". Keep responses brief and actionable.

Available tools:
{tool_descriptions}

If you need current information, use the web_search tool.
If you need to do math, use the calculator tool.
Always think step by step for complex questions."""

class ChatAgent(Agent):
    name = "chat"
    description = "General conversation with FRIDAY"

    def __init__(self, provider):
        super().__init__(provider)
        self.system_prompt = _CHAT_PROMPT

    async def handle(self, user_input: str, **kwargs) -> str:
        from friday.tools.web_search import WebSearch, WebFetch
        from friday.tools.calculator import Calculator
        from friday.tools.think import Think
        from friday.tools.file_ops import FileRead, FileList
        from friday.tools.shell import ShellExec

        self.register_tools(
            WebSearch(), WebFetch(), Calculator(), Think(),
            FileRead(), FileList(), ShellExec(),
        )

        tool_descs = "\n".join(f"- {t.name}: {t.description}" for t in self.tools.values())
        system = self.system_prompt.replace("{tool_descriptions}", tool_descs)

        messages: list[dict] = [{"role": "system", "content": system}]
        for msg in self.messages[-10:]:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_input})

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

        text = response if isinstance(response, str) else response.get("content", str(response))
        self.messages.append(Message(role="user", content=user_input))
        self.messages.append(Message(role="assistant", content=text))
        return text
