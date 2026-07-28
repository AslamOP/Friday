from __future__ import annotations
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger("friday.core.learning")

_DATA = Path.home() / ".friday" / "learning"

class LearningEngine:
    def __init__(self):
        _DATA.mkdir(parents=True, exist_ok=True)
        self._traces: list[dict] = []
        self._trace_file = _DATA / "traces.jsonl"
        self._trace_file.touch(exist_ok=True)
        self._lessons: list[str] = []
        self._lessons_file = _DATA / "lessons.json"
        self._load_lessons()

    def _load_lessons(self):
        if self._lessons_file.exists():
            self._lessons = json.loads(self._lessons_file.read_text())

    def _save_lessons(self):
        self._lessons_file.write_text(json.dumps(self._lessons, indent=2))

    def record(self, user_input: str, response: str, agent: str, feedback: int | None = None):
        trace = {"user": user_input, "response": response, "agent": agent, "feedback": feedback}
        self._traces.append(trace)
        with open(self._trace_file, "a") as f:
            f.write(json.dumps(trace) + "\n")

    def feedback(self, score: int):
        if self._traces:
            self._traces[-1]["feedback"] = score

    def learn(self) -> list[str]:
        corrections = [t for t in self._traces if t.get("feedback") and t["feedback"] < 3]
        for c in corrections:
            words = c["user"].lower().split()
            if len(words) > 3:
                lesson = f"User prefers: {c['response'][:80]}..."
                if lesson not in self._lessons:
                    self._lessons.append(lesson)
        self._save_lessons()
        return self._lessons

    def get_lessons(self) -> list[str]:
        return self._lessons
