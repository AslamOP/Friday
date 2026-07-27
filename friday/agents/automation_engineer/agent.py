from ..base import BaseAgent, Context, Result, Task
from . import prompts
from friday.router.omniroute import OmniRouteClient
class AutomationEngineerAgent(BaseAgent):
    name = "automation_engineer"
    def __init__(self):
        super().__init__(model_preference="deepseek/deepseek-coder-33b-instruct")
        self._router = OmniRouteClient()
    async def handle(self, task, context):
        r = await self._router.route("automate", prompts.PROMPT.format(input=context.user_input), prompts.SYSTEM_PROMPT)
        return Result(success=True, output=r.get("content", ""), agent=self.name)
    async def can_handle(self, intent): return 0.9 if intent == "automate" else 0.1
