import asyncio
import logging

from friday.agents.base import Context, Result, Task
from friday.core.agent_router import AgentRouter
from friday.core.intent_parser import Intent, IntentParser

logger = logging.getLogger("friday.task_delegator")


_INTENT_TO_AGENT = {
    "code": "software_engineer",
    "research": "research_scientist",
    "plan": "planner",
    "study": "study",
    "challenge": "mentor",
    "knowledge": "knowledge_manager",
    "automate": "automation_engineer",
    "gaming": "gaming_assistant",
    "chat": "chat",
}

_NO_DELEGATE = {"chat", "gaming", "challenge"}


class TaskDelegator:
    def __init__(self, router: AgentRouter):
        self._router = router
        self._intent = IntentParser()

    async def plan(self, user_input: str, pre_parsed: Intent | None = None) -> list[dict[str, str]]:
        intent = pre_parsed or await self._intent.parse(user_input)
        if intent.type in _NO_DELEGATE:
            return []
        agent = _INTENT_TO_AGENT.get(intent.type)
        if agent:
            return [{"agent": agent, "input": user_input}]
        return []

    async def dispatch(self, subtasks: list[dict], context: Context) -> list[tuple[dict, Result]]:
        async def run(st):
            agent = await self._router.route(Intent(type=st["agent"], confidence=1.0, entities={}))
            ctx = Context(user_input=st["input"], user_id=context.user_id,
                          conversation=context.conversation, memory=context.memory)
            return st, await agent.handle(Task(type=st["agent"], input=st["input"]), ctx)
        return await asyncio.gather(*[run(s) for s in subtasks])

    def merge(self, results: list[tuple[dict, Result]]) -> str:
        return "\n\n---\n\n".join(
            f"### {'✅' if r.success else '❌'} {s['agent']}\n{r.output[:2000]}"
            for s, r in results
        )
