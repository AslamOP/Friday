import asyncio
import json, logging, uuid
from pathlib import Path
from friday.memory.embedding_service import EmbeddingService
logger = logging.getLogger("friday.semantic_store")
class SemanticStore:
    def __init__(self, persist_dir: str = "data/chroma"):
        self._persist_dir = Path(persist_dir); self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._emb = EmbeddingService(); self._entries: dict[str, dict] = {}
        self._load()
    def _path(self): return self._persist_dir / "entries.json"
    def _load(self):
        p = self._path()
        if p.exists():
            try:
                with open(p) as f: raw = json.load(f)
                self._entries = {e["id"]: e for e in raw}
                logger.info("Loaded %d entries from %s", len(self._entries), p)
            except Exception as e:
                logger.warning("Failed to load semantic store: %s", e)
    async def _save(self):
        p = self._path()
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: p.write_text(json.dumps([e for e in self._entries.values()], indent=2)))
        except Exception as e:
            logger.warning("Failed to save semantic store: %s", e)
    async def add_entry(self, eid: str, text: str, metadata: dict | None = None):
        emb = await self._emb.embed(text)
        self._entries[eid] = {"id": eid, "text": text, "embedding": emb, "metadata": metadata or {}}
        await self._save()
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
