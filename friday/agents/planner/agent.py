from ..base import BaseAgent, Context, Result, Task
from . import prompts
from friday.memory.project_memory import ProjectMemory
from friday.router.omniroute import OmniRouteClient
from uuid import uuid4
class PlannerAgent(BaseAgent):
    name = "planner"
    def __init__(self):
        super().__init__(model_preference="anthropic/claude-3.5-sonnet")
        self._router = OmniRouteClient(); self._pm = ProjectMemory()
    async def handle(self, task, context):
        r = await self._router.route("plan", prompts.PROMPT.format(input=context.user_input), prompts.SYSTEM_PROMPT)
        content = r.get("content", ""); pid = str(uuid4())
        proj = self._pm.find_by_name("plans") or {"id": self._pm.create_project("plans")}
        self._pm.update_project(proj["id"], {f"plan_{pid}": {"goal": context.user_input[:80], "content": content}})
        return Result(success=True, output=f"## Plan\n\n{content}\n\nID: `{pid}`", agent=self.name, data={"plan_id": pid})
    async def can_handle(self, intent): return 0.9 if intent == "plan" else 0.1
