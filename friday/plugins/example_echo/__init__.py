from friday.agents.base import BaseAgent, Context, Result, Task
from friday.plugin.base import Plugin


class EchoAgent(BaseAgent):
    name = "echo"
    def __init__(self):
        super().__init__(model_preference="local")

    async def can_handle(self, intent: str) -> float:
        return 0.95 if intent == "echo" else 0.0

    async def handle(self, task: Task, context: Context) -> Result:
        return Result(success=True, output=f"Echo: {context.user_input}", agent=self.name)


class ExampleEchoPlugin(Plugin):
    name = "example_echo"
    version = "1.0.0"
    description = "Echoes back user input (demonstrates plugin API)"

    async def on_load(self, orchestrator):
        orchestrator.register_agent(EchoAgent())
        orchestrator.register_intent("echo", ["echo", "repeat", "say again"])

    async def on_unload(self, orchestrator):
        orchestrator.agent_router.unregister_agent("echo")
        orchestrator.unregister_intent("echo")
