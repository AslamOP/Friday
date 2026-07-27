import re, logging
from friday.memory.knowledge_graph import KnowledgeGraph
logger = logging.getLogger("friday.entity_extractor")
_PATTERNS: list[tuple[str, str, str]] = [
    (r'\b(FRIDAY|Friday)\b', "system", "FRIDAY"),
    (r'\b(Python|FastAPI|React|Docker|Ollama|ChromaDB|SQLite)\b', "technology", ""),
    (r'\b(Arch Linux|Linux|Windows|macOS)\b', "platform", ""),
    (r'\b(REST API|API|endpoint)\b', "concept", "API"),
    (r'\b(GitHub|Git|OpenRouter)\b', "service", ""),
    (r'\b(mentor|planner|coder|tutor|agent)\b', "role", ""),
    (r'\b(project|feature|bug|task|issue)\b', "work_item", ""),
]
class EntityExtractor:
    def __init__(self):
        self._kg = KnowledgeGraph(); self._known: set[str] = set()
    def extract_regex(self, text: str) -> list[dict]:
        found = []
        for pat, etype, default in _PATTERNS:
            for m in re.finditer(pat, text, re.IGNORECASE):
                name = default or m.group(1); eid = f"{etype}:{name.lower().replace(' ','_')}"
                found.append({"id": eid, "name": name, "type": etype})
        return found
    async def extract_and_store(self, text: str, source: str = "conversation") -> int:
        count = 0
        for ent in self.extract_regex(text):
            if ent["id"] in self._known: continue
            if self._kg.query_entity(ent["id"]) is None:
                self._kg.add_entity(ent["id"], ent["type"], {"name": ent["name"], "source": source})
                count += 1
            self._known.add(ent["id"])
        return count
    async def extract_from_conversation(self, conv: list[dict]) -> int:
        total = 0
        for msg in conv[-20:]: total += await self.extract_and_store(msg.get("content", ""), msg.get("role", "unknown"))
        return total
    def get_stats(self) -> dict: return {"known_entities": len(self._known)}
