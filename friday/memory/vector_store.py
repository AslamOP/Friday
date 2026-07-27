import logging
from typing import Any

from friday.memory.embedding_service import EmbeddingService
from friday.memory.semantic_store import SemanticStore

logger = logging.getLogger("friday.vector_store")


class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_store"):
            return
        self._store = SemanticStore()
        self._embeddings = EmbeddingService()

    async def add_entry(self, eid: str, text: str, metadata: dict | None = None):
        await self._store.add_entry(eid, text, metadata or {})

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        if await self._embeddings.is_available():
            return await self._store.search(query, top_k)
        return []

    async def count(self) -> int:
        return await self._store.count()
