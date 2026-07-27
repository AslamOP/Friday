import asyncio
import json, logging
from pathlib import Path
from typing import Any
logger = logging.getLogger("friday.knowledge_graph")
class KnowledgeGraph:
    _instance = None
    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        if hasattr(self, "_graph"): return
        self._graph: dict[str, dict] = {}; self._relations: list[dict] = []
    def add_entity(self, eid: str, etype: str, props: dict | None = None):
        self._graph[eid] = {"id": eid, "type": etype, "properties": props or {}}
    def add_relation(self, src: str, tgt: str, rel: str): self._relations.append({"source": src, "target": tgt, "relation": rel})
    def query_entity(self, eid: str): return self._graph.get(eid)
    def search(self, query: str) -> list[dict]:
        q = query.lower(); results = []
        for e in self._graph.values():
            if q in e["id"].lower() or q in e["type"].lower(): results.append(e); continue
            for v in e["properties"].values():
                if isinstance(v, str) and q in v.lower(): results.append(e); break
        return results
    def get_relations(self, eid: str | None = None):
        if eid is None: return self._relations
        return [r for r in self._relations if r["source"] == eid or r["target"] == eid]
    async def save(self, path):
        p = Path(path) if isinstance(path, str) else path; p.parent.mkdir(parents=True, exist_ok=True)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: p.write_text(json.dumps({"entities": self._graph, "relations": self._relations}, indent=2)))
    async def load(self, path):
        p = Path(path) if isinstance(path, str) else path
        if not p.exists(): return
        loop = asyncio.get_running_loop()
        d = await loop.run_in_executor(None, lambda: json.loads(p.read_text()))
        self._graph = d.get("entities", {}); self._relations = d.get("relations", [])
