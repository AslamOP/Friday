from dataclasses import dataclass, field
from typing import Any


@dataclass
class Intent:
    type: str
    confidence: float = 1.0
    entities: dict[str, Any] = field(default_factory=dict)


_INTENTS = [
    ("code", ["build", "code", "program", "api", "function", "implement", "script", "develop"]),
    ("plan", ["plan", "schedule", "timeline", "roadmap", "milestone", "organize"]),
    ("study", ["study", "learn", "teach", "explain", "tutor", "practice", "question"]),
    ("knowledge", ["find", "know", "remember", "index", "search for", "locate"]),
    ("research", ["research", "investigate", "what is", "analyze"]),
    ("challenge", ["challenge", "review", "critique", "improve", "optimize", "why"]),
    ("automate", ["automate", "workflow", "pipeline", "schedule task", "cron"]),
    ("gaming", ["game", "gaming", "play", "fps", "settings", "performance"]),
]


class IntentParser:
    def __init__(self):
        self._custom_intents: list[tuple[str, list[str]]] = []

    def register_intent(self, intent_type: str, keywords: list[str]):
        self._custom_intents.append((intent_type, keywords))

    def unregister_intent(self, intent_type: str):
        self._custom_intents = [i for i in self._custom_intents if i[0] != intent_type]

    async def parse(self, text: str) -> Intent:
        t = text.lower()
        for intent_type, keywords in _INTENTS + self._custom_intents:
            if any(kw in t for kw in keywords):
                return Intent(type=intent_type, confidence=0.8)
        return Intent(type="chat", confidence=0.5)
