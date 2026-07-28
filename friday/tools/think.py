from __future__ import annotations
from friday.core.tool import Tool

class Think(Tool):
    name = "think"
    description = "Use this to reason through complex problems step by step"
    parameters = {
        "type": "object",
        "properties": {
            "thought": {"type": "string", "description": "Your step-by-step reasoning"},
        },
        "required": ["thought"],
    }
    
    def run(self, thought: str) -> str:
        return "Thought recorded."
