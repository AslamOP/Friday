import collections
import json
import logging
import re
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
    # Learn lessons from interactions using NLP
    # ------------------------------------------------------------------

    @staticmethod
    def _ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
        return list(zip(*[tokens[i:] for i in range(n)]))

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def reflect(self, recent_n: int = 20) -> list[str]:
        recent = self._interactions[-recent_n:]
        if not recent:
            return []

        # split into successful vs failed
        good = [i for i in recent if i.get("success", True)]
        bad = [i for i in recent if not i.get("success", True)]

        if not bad:
            return []

        # tokenize inputs
        good_tokens = []
        for i in good:
            good_tokens.extend(self._tokenize(i["input"]))
        bad_tokens = []
        for i in bad:
            bad_tokens.extend(self._tokenize(i["input"]))

        # count unigrams and bigrams
        good_unigrams = collections.Counter(good_tokens)
        bad_unigrams = collections.Counter(bad_tokens)
        good_bigrams = collections.Counter(self._ngrams(good_tokens, 2))
        bad_bigrams = collections.Counter(self._ngrams(bad_tokens, 2))

        # find tokens over-represented in failures (discounted by good frequency)
        def score(tok, count):
            g = good_unigrams.get(tok, 0) + 1
            return count / g

        top_failure_terms = sorted(bad_unigrams.items(), key=lambda x: score(x[0], x[1]), reverse=True)[:8]

        # generate lessons from patterns
        lessons = []

        # lesson 1: agent-specific patterns
        agent_failures = collections.Counter(i["agent"] for i in bad if i.get("agent"))
        if agent_failures:
            worst_agent = agent_failures.most_common(1)[0]
            lessons.append(f"Agent '{worst_agent[0]}' has {worst_agent[1]} failures — review its prompts and capabilities")

        # lesson 2: topic-based patterns from failure bigrams
        if bad_bigrams:
            top_bigram = bad_bigrams.most_common(1)[0]
            term1, term2 = top_bigram[0]
            if top_bigram[1] >= 2:
                lessons.append(f"Users mentioning '{term1} {term2}' often get poor responses — prepare better handling")

        # lesson 3: contrastive — what makes failures different
        distinctive = []
        for tok, count in bad_unigrams.most_common(20):
            g = good_unigrams.get(tok, 0)
            if count > g * 2 and count >= 2:
                distinctive.append(tok)
        if distinctive:
            examples = ", ".join(distinctive[:5])
            lessons.append(f"Terms like '{examples}' correlate with failed interactions — adjust responses when these appear")

        # lesson 4: if users explicitly correct, extract topic
        corrections = [i for i in bad if self.detect_correction(i["input"])]
        if corrections:
            topics = set()
            for c in corrections:
                inp = c["input"].lower()
                for w in ("wrong", "incorrect", "no", "not", "actually"):
                    if w in inp:
                        after = inp.split(w, 1)[-1].strip().split()[:5]
                        topics.add(" ".join(after))
            if topics:
                topic_str = "|".join(list(topics)[:3])
                lessons.append(f"When user says '{topic_str}' is wrong, verify before responding confidently")

        # de-duplicate and save
        new_lessons = []
        for lesson in lessons:
            if len(lesson) > 10 and not any(l["lesson"] == lesson for l in self._lessons):
                self._lessons.append({
                    "lesson": lesson,
                    "timestamp": __import__("time").time(),
                    "applied": False,
                })
                new_lessons.append(lesson)

        if new_lessons:
            self._save("lessons.json", self._lessons)
            logger.info("Extracted %d lessons via NLP", len(new_lessons))

        return new_lessons

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
