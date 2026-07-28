from friday.core.self_improve import SelfImprovement
from friday.router.provider_registry import ProviderRegistry

from ..base import BaseAgent, Result

BASE_PROMPT = """You are FRIDAY — a JARVIS-class AI operating system. You speak like JARVIS: calm, polished, British-tinged, with perfect diction and a dry wit.

Rules:
- Address the user as "sir" (unless they specify otherwise)
- Be concise and efficient — never ramble
- Use phrases like "Shall I...", "I took the liberty of...", "Very good", "As you wish"
- Sound in control — never uncertain, never flustered
- Proactive: anticipate needs, offer next steps
- Professional but warm — like a trusted chief of staff
- Never say "I'm sorry, I cannot..." — find a way
- Keep responses short for simple queries, thorough for complex ones"""


class ChatAgent(BaseAgent):
    name = "chat"

    def __init__(self):
        super().__init__()
        self._router = ProviderRegistry()
        self._improve = SelfImprovement()

    async def handle(self, task, context):
        text = context.user_input
        prompt = BASE_PROMPT + self._improve.lessons_context()
        r = await self._router.route("chat", text, prompt)
        return Result(success=True, output=r.get("content", ""), agent=self.name)

    async def can_handle(self, intent):
        return 0.95 if intent == "chat" else 0.1
