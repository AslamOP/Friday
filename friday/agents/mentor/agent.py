from friday.router.provider_registry import ProviderRegistry

from ..base import BaseAgent, Result
from . import prompts


class MentorAgent(BaseAgent):
    name = "mentor"
    def __init__(self):
        super().__init__(model_preference="anthropic/claude-3.5-sonnet")
        self._router = ProviderRegistry()
    async def handle(self, task, context):
        r = await self._router.route("chat", prompts.PROMPT.format(input=context.user_input), prompts.SYSTEM_PROMPT)
        return Result(success=True, output=r.get("content", ""), agent=self.name)
    async def can_handle(self, intent): return 0.85 if intent == "challenge" else 0.1
