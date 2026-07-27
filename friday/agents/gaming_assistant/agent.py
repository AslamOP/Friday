from ..base import BaseAgent, Context, Result, Task
from . import prompts
from friday.router.provider_registry import ProviderRegistry
class GamingAssistantAgent(BaseAgent):
    name = "gaming_assistant"
    def __init__(self):
        super().__init__(model_preference="openai/gpt-4o-mini")
        self._router = ProviderRegistry()
    async def handle(self, task, context):
        r = await self._router.route("chat", prompts.PROMPT.format(input=context.user_input), prompts.SYSTEM_PROMPT)
        return Result(success=True, output=r.get("content", ""), agent=self.name)
    async def can_handle(self, intent): return 0.9 if intent == "gaming" else 0.1
