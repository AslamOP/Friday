import logging, uuid
from friday.memory.embedding_service import EmbeddingService
logger = logging.getLogger("friday.semantic_store")
class SemanticStore:
    def __init__(self, persist_dir: str = "data/chroma"):
        self._persist_dir = persist_dir; self._emb = EmbeddingService(); self._entries: dict[str, dict] = {}
    async def add_entry(self, eid: str, text: str, metadata: dict | None = None):
        emb = await self._emb.embed(text)
        self._entries[eid] = {"id": eid, "text": text, "embedding": emb, "metadata": metadata or {}}
    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        qe = await self._emb.embed(query)
        if not qe or not self._entries: return []
        import math
        scored = []
        for eid, e in self._entries.items():
            if not e["embedding"]: continue
            dot = sum(a * b for a, b in zip(qe, e["embedding"]))
            nq = math.sqrt(sum(x*x for x in qe)); ne = math.sqrt(sum(x*x for x in e["embedding"]))
            sim = dot / (nq * ne) if nq and ne else 0
            scored.append((sim, eid, e))
        scored.sort(key=lambda x: -x[0])
        return [{"id": eid, "text": e["text"][:500], "score": s, "metadata": e["metadata"]} for s, eid, e in scored[:top_k]]
    async def count(self): return len(self._entries)
