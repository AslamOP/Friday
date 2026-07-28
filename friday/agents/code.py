from __future__ import annotations
import logging
from friday.core.agent import Agent

logger = logging.getLogger("friday.agents.code")

_CODE_PROMPT = """You are FRIDAY's software engineering division.
You help the user write, debug, and understand code.
You have access to file operations, shell execution, and git.
Always write clean, idiomatic code. Test your solutions.
Address the user as "sir"."""

class CodeAgent(Agent):
    name = "code"
    description = "Software engineering assistance"

    def __init__(self, provider):
        super().__init__(provider)
        self.system_prompt = _CODE_PROMPT

    async def handle(self, user_input: str, **kwargs) -> str:
        from friday.tools.file_ops import FileRead, FileWrite, FileList
        from friday.tools.shell import ShellExec
        from friday.tools.code_interpreter import CodeInterpreter
        from friday.tools.git import GitTool
        from friday.tools.think import Think

        self.register_tools(
            FileRead(), FileWrite(), FileList(), ShellExec(),
            CodeInterpreter(), GitTool(), Think(),
        )

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
