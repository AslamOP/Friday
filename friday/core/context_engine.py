import logging

from friday.agents.base import Context
from friday.core.intent_parser import Intent
from friday.memory.conversation_store import ConversationStore
from friday.memory.knowledge_graph import KnowledgeGraph
from friday.memory.semantic_store import SemanticStore
from friday.memory.user_profile import UserProfile

logger = logging.getLogger("friday.context_engine")
class ContextEngine:
    def __init__(self):
        self._conversation = ConversationStore()
        self._semantic = SemanticStore()
        self._kg = KnowledgeGraph()
        self._profile = UserProfile()

    async def load_context(self, user_input: str, intent: Intent) -> Context:
        mem = {"intent": {"type": intent.type, "confidence": intent.confidence}, "profile": self._profile.get_profile()}
        history = await self._conversation.get_history(limit=10)
        conv = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]
        kg = self._kg.search(user_input)
        if kg:
            mem["knowledge_graph"] = [{"id": e["id"], "type": e["type"]} for e in kg[:5]]
        sem = await self._semantic.search(user_input, top_k=3)
        if sem:
            mem["semantic"] = [{"id": r["id"], "text": r["text"][:200], "score": r["score"]} for r in sem]
        return Context(user_input=user_input, memory=mem, conversation=conv)

    async def remember(self, role: str, content: str, metadata: dict | None = None):
        await self._conversation.add_message(role, content, metadata)
