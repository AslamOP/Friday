import asyncio, logging, json
from friday.agents.base import BaseAgent, Context, Result, Task
from friday.core.agent_router import AgentRouter
from friday.core.intent_parser import Intent, IntentParser
from friday.router.omniroute import OmniRouteClient
logger = logging.getLogger("friday.task_delegator")

_PROMPT = "Break this into subtasks for specialist agents. Available agents: software_engineer (code), research_scientist (research), planner (planning), academic_tutor (study), mentor (challenge), knowledge_manager (knowledge), automation_engineer (automate), gaming_assistant (gaming). Return JSON array of objects each with keys 'agent' and 'input'. Single item if only one needed. Empty array if none.\nRequest: {input}"

class TaskDelegator:
    def __init__(self, router: AgentRouter):
        self._router = router; self._intent = IntentParser(); self._llm = OmniRouteClient()
    async def plan(self, user_input: str) -> list[dict[str, str]]:
        r = await self._llm.route("plan", _PROMPT.format(input=user_input))
        c = r.get("content", "[]").strip()
        if c.startswith("```"): c = c.split("\n",1)[-1].rsplit("```",1)[0]
        try:
            st = json.loads(c)
            if isinstance(st, list) and all("agent" in s and "input" in s for s in st):
                logger.info("Delegated %d subtasks", len(st)); return st
        except: pass
        intent = await self._intent.parse(user_input)
        return [{"agent": intent.type, "input": user_input}] if intent.type not in ("chat","gaming","challenge") else []
    async def dispatch(self, subtasks: list[dict], context: Context) -> list[tuple[dict, Result]]:
        async def run(st):
            agent = await self._router.route(Intent(type=st["agent"], confidence=1.0, entities={}))
            ctx = Context(user_input=st["input"], user_id=context.user_id, conversation=context.conversation, memory=context.memory)
            return st, await agent.handle(Task(type=st["agent"], input=st["input"]), ctx)
        return await asyncio.gather(*[run(s) for s in subtasks])
    def merge(self, results: list[tuple[dict, Result]]) -> str:
        return "\n\n---\n\n".join(f"### {'✅' if r.success else '❌'} {s['agent']}\n{r.output[:2000]}" for s, r in results)
