from __future__ import annotations
from friday.core.tool import Tool
from friday.core.memory import MemoryStore

class MemoryRecall(Tool):
    name = "memory_recall"
    description = "Recall recent conversation history"
    parameters = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "Number of recent exchanges", "default": 5},
        },
    }
    
    def __init__(self):
        super().__init__()
        self._store = MemoryStore()
    
    def run(self, limit: int = 5) -> str:
        history = self._store.get_history(limit)
        if not history:
            return "No conversation history."
        lines = []
        for h in history:
            lines.append(f"User: {h['user'][:100]}")
            lines.append(f"FRIDAY: {h['assistant'][:100]}")
        return "\n".join(lines)
