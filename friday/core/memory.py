from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("friday.core.memory")

_DATA_DIR = Path.home() / ".friday" / "data"

class MemoryStore:
    def __init__(self):
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._conversations: list[dict] = []
        self._conv_file = _DATA_DIR / "conversations.jsonl"
        self._conv_file.touch(exist_ok=True)

    def save_interaction(self, user: str, assistant: str, metadata: dict | None = None):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": user,
            "assistant": assistant,
            "metadata": metadata or {},
        }
        self._conversations.append(entry)
        with open(self._conv_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_history(self, limit: int = 10) -> list[dict]:
        return self._conversations[-limit:]

    def get_all(self) -> list[dict]:
        if not self._conversations:
            with open(self._conv_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self._conversations.append(json.loads(line))
        return self._conversations

    def clear(self):
        self._conversations = []
        self._conv_file.write_text("")
