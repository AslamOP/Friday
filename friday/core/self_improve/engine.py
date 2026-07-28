import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("friday.self_improve")

_DATA_DIR = Path("data/self_improve")


class SelfImprovement:
    def __init__(self):
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._interactions: list[dict] = self._load("interactions.json")
        self._lessons: list[dict] = self._load("lessons.json")
        self._feedback: list[dict] = self._load("feedback.json")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self, name: str) -> list:
        p = _DATA_DIR / name
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        return []

    def _save(self, name: str, data: list):
        p = _DATA_DIR / name
        try:
            p.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.debug("Save %s failed: %s", name, e)

    # ------------------------------------------------------------------
    # Record every interaction
    # ------------------------------------------------------------------

    def record(self, user_input: str, output: str, agent: str, success: bool = True):
        self._interactions.append({
            "input": user_input[:200],
            "output": output[:500],
            "agent": agent,
            "success": success,
            "timestamp": __import__("time").time(),
        })
        if len(self._interactions) > 500:
            self._interactions = self._interactions[-500:]
        self._save("interactions.json", self._interactions)

    # ------------------------------------------------------------------
    # Explicit feedback (thumbs up/down via /feedback command)
    # ------------------------------------------------------------------

    def add_feedback(self, user_input: str, rating: int, comment: str = ""):
        self._feedback.append({
            "input": user_input[:200],
            "rating": rating,
            "comment": comment[:500],
            "timestamp": __import__("time").time(),
        })
        self._save("feedback.json", self._feedback)
        if rating <= 2:
            logger.info("Negative feedback recorded for: %s", user_input[:60])

    # ------------------------------------------------------------------
    # Detect implicit negative feedback from corrections
    # ------------------------------------------------------------------

    def detect_correction(self, user_input: str) -> bool:
        low = user_input.lower()
        correction_words = [
            "wrong", "incorrect", "no", "not right", "that's not",
            "that is not", "actually", "correction", "mistake",
            "error", "fix it", "you're wrong", "you are wrong",
            "try again", "rethink", "bad", "useless", "stupid",
        ]
        return any(w in low for w in correction_words)

    def detect_praise(self, user_input: str) -> bool:
        low = user_input.lower()
        praise_words = [
            "good", "great", "perfect", "thanks", "thank you",
            "nice", "awesome", "correct", "excellent", "well done",
            "amazing", "brilliant", "love it", "impressive",
        ]
        return any(w in low for w in praise_words)

    # ------------------------------------------------------------------
    # Learn lessons from interactions
    # ------------------------------------------------------------------

    async def reflect(self, recent_n: int = 20) -> list[str]:
        recent = self._interactions[-recent_n:]
        if not recent:
            return []

        failed = [i for i in recent if not i["success"]]
        if not failed:
            return []

        from friday.router.provider_registry import ProviderRegistry

        prompt = (
            "Analyze these failed FRIDAY AI interactions. For each, identify what went wrong "
            "and write ONE concrete lesson for the AI to follow in future.\n"
            "Return a JSON array of strings, each being a lesson like:\n"
            '"When user asks about X, always provide Y first" or "Never assume Z without asking"\n\n'
            + "\n".join(f"User: {i['input']}\nFRIDAY: {i['output']}" for i in failed[-5:])
        )

        r = await ProviderRegistry().route("self_improve", prompt,
            "You are a strict quality auditor. Identify specific, actionable improvements.")
        content = r.get("content", "[]")
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            lessons = json.loads(content)
            if isinstance(lessons, list):
                for lesson in lessons:
                    if isinstance(lesson, str) and len(lesson) > 10:
                        if not any(l["lesson"] == lesson for l in self._lessons):
                            self._lessons.append({
                                "lesson": lesson,
                                "timestamp": __import__("time").time(),
                                "applied": False,
                            })
                self._save("lessons.json", self._lessons)
                return lessons
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------
    # Get accumulated lessons for use in system prompts
    # ------------------------------------------------------------------

    def lessons_context(self, max_lessons: int = 5) -> str:
        active = [l for l in self._lessons if not l.get("applied", False)][-max_lessons:]
        if not active:
            return ""
        lines = "\n".join(f"- {l['lesson']}" for l in active)
        return f"\n\nLessons learned from past interactions:\n{lines}"

    # ------------------------------------------------------------------
    # Mark lessons as applied (after prompt optimization)
    # ------------------------------------------------------------------

    def mark_applied(self, lesson_text: str):
        for l in self._lessons:
            if l["lesson"] == lesson_text:
                l["applied"] = True
        self._save("lessons.json", self._lessons)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "interactions": len(self._interactions),
            "lessons": len(self._lessons),
            "feedback": len(self._feedback),
            "pending_lessons": sum(1 for l in self._lessons if not l.get("applied", False)),
        }
