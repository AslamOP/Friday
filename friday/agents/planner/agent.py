from ..base import BaseAgent, Context, Result, Task
from . import prompts
from friday.memory.project_memory import ProjectMemory
from friday.router.provider_registry import ProviderRegistry
from uuid import uuid4


class PlannerAgent(BaseAgent):
    name = "planner"

    def __init__(self):
        super().__init__(model_preference="anthropic/claude-3.5-sonnet")
        self._router = ProviderRegistry()
        self._pm = ProjectMemory()

    async def handle(self, task, context):
        text = context.user_input.lower()

        # detect if this is actually a planning request
        plan_keywords = ("plan", "schedule", "timeline", "roadmap", "milestone",
                         "outline", "organize", "break down", "project plan",
                         "study plan", "research plan", "prepare for")
        is_plan = any(kw in text for kw in plan_keywords)

        if not is_plan:
            return Result(success=True, output="I only handle planning requests — project plans, study plans, research outlines, schedules, and timelines. Tell me what you'd like to plan.", agent=self.name)

        r = await self._router.route("plan", prompts.PROMPT.format(input=context.user_input), prompts.SYSTEM_PROMPT)
        content = r.get("content", "")

        # persist to ProjectMemory
        pid = str(uuid4())
        proj = self._pm.find_by_name("plans")
        if not proj:
            proj_id = self._pm.create_project("plans", "Auto-generated plans")
        else:
            proj_id = proj["id"]

        self._pm.update_project(proj_id, {
            f"plan_{pid}": {
                "goal": context.user_input[:100],
                "content": content[:2000],
            }
        })

        return Result(
            success=True,
            output=f"## Plan\n\n{content}\n\n📁 Plan ID: `{pid}`",
            agent=self.name,
            data={"plan_id": pid},
        )

    async def can_handle(self, intent):
        return 0.9 if intent == "plan" else 0.1
