from friday.router.provider_registry import ProviderRegistry

from ..base import BaseAgent, Result

SYSTEM_PROMPT = """You are FRIDAY — a calm, helpful, futuristic AI assistant. You talk like JARVIS: polished, intelligent, slightly dry wit. Keep responses concise. You can chat about anything the user asks."""


class ChatAgent(BaseAgent):
    name = "chat"

    def __init__(self):
        super().__init__()
        self._router = ProviderRegistry()

    async def handle(self, task, context):
        text = context.user_input
        r = await self._router.route("chat", text, SYSTEM_PROMPT)
        return Result(success=True, output=r.get("content", ""), agent=self.name)

    async def can_handle(self, intent):
        return 0.95 if intent == "chat" else 0.1
