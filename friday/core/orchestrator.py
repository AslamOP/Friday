import asyncio
import logging
from functools import lru_cache

from friday.agents.base import Result, Task
from friday.core.agent_router import AgentRouter
from friday.core.context_engine import ContextEngine
from friday.core.event_bus import EventBus
from friday.core.intent_parser import IntentParser
from friday.core.task_delegator import TaskDelegator
from friday.core.task_scheduler import TaskScheduler
from friday.memory.entity_extractor import EntityExtractor
from friday.memory.persistence import PersistenceManager
from friday.plugin.manager import PluginManager

logger = logging.getLogger("friday.orchestrator")

class Orchestrator:
    def __init__(self):
        self.intent_parser = IntentParser()
        self.context_engine = ContextEngine()
        self.agent_router = AgentRouter()
        self.event_bus = EventBus()
        self.task_scheduler = TaskScheduler()
        self.entity_extractor = EntityExtractor()
        self.persistence = PersistenceManager()
        self.plugin_manager = PluginManager()
        self._delegator: TaskDelegator | None = None

    async def initialize(self):
        await self.persistence.start_auto_save()
        self._delegator = TaskDelegator(self.agent_router)
        await self.plugin_manager.discover_and_load_all(self)
        logger.info("Orchestrator ready")

    def register_agent(self, agent):
        self.agent_router.register_agent(agent)

    def register_intent(self, intent_type: str, keywords: list[str]):
        self.intent_parser.register_intent(intent_type, keywords)

    def unregister_intent(self, intent_type: str):
        self.intent_parser.unregister_intent(intent_type)

    def subscribe_event(self, event_type: str, callback):
        self.event_bus.subscribe(event_type, callback)

    def publish_event(self, event_type: str, data: dict = None):
        asyncio.ensure_future(self.event_bus.publish(event_type, data))

    async def process(self, user_input: str) -> Result:
        logger.info("Process: '%s'", user_input)
        intent = await self.intent_parser.parse(user_input)
        context = await self.context_engine.load_context(user_input, intent)
        await self.context_engine.remember("user", user_input, {"intent": intent.type})

        self.publish_event("agent:start", {"agent": intent.type, "input": user_input})

        if self._delegator:
            subtasks = await self._delegator.plan(user_input, pre_parsed=intent)
            if len(subtasks) > 1:
                logger.info("Delegating %d subtasks", len(subtasks))
                results = await self._delegator.dispatch(subtasks, context)
                merged = self._delegator.merge(results)
                result = Result(success=True, output=merged, agent="collaboration", data={"subtask_count": len(subtasks)})
                await self.context_engine.remember("assistant", merged[:1000], {"agent":"collaboration","subtasks":len(subtasks)})
                await self.persistence.save_all()
                self.publish_event("agent:done", {"agent": "collaboration", "success": True})
                return result

        agent = await self.agent_router.route(intent, context)
        self.publish_event("agent:status", {"agent": agent.name, "status": "running"})
        result = await agent.handle(Task(id="", type=intent.type, payload=intent.entities), context)
        self.publish_event("agent:status", {"agent": agent.name, "status": "done" if result.success else "error"})

        if result.subtasks and self._delegator:
            sub_results = await self._delegator.dispatch(result.subtasks, context)
            result.output += f"\n\n---\n## Subtasks\n{self._delegator.merge(sub_results)}"

        await self.context_engine.remember("assistant" if result.success else "error", result.output[:1000], {"agent": result.agent, "success": result.success})
        extracted = await self.entity_extractor.extract_and_store(f"{user_input} {result.output[:500]}")
        if extracted:
            logger.debug("Extracted %d entities", extracted)
        await self.persistence.save_all()
        self.publish_event("agent:done", {"agent": result.agent, "success": result.success})
        return result

    async def remember_response(self, user_input: str, output: str, agent_name: str, intent_type: str) -> Result:
        result = Result(success=True, output=output, agent=agent_name)
        await self.context_engine.remember("assistant", output[:1000], {"agent": agent_name, "success": True})
        extracted = await self.entity_extractor.extract_and_store(f"{user_input} {output[:500]}")
        if extracted:
            logger.debug("Extracted %d entities", extracted)
        await self.persistence.save_all()
        return result

    async def process_many(self, inputs: list[str]) -> list[Result]:
        return await asyncio.gather(*[self.process(i) for i in inputs])

@lru_cache()
def get_orchestrator() -> Orchestrator: return Orchestrator()
