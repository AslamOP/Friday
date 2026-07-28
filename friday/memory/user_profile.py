import asyncio
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("friday.user_profile")
_DEFAULT: dict[str, Any] = {"name": "Architect", "title": "sir", "coding_style": {"language_preference": "python", "indent_style": "spaces", "line_length": 88}, "writing_style": {"tone": "technical", "citation_format": "APA"}, "preferences": {"challenge_mode": True, "proactive_alerts": True}, "goals": [], "skills": []}
class UserProfile:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_profile"):
            return
        self._profile: dict = dict(_DEFAULT)

    def get_profile(self):
        return dict(self._profile)

    def update_profile(self, updates: dict):
        for k, v in updates.items():
            if k in self._profile and isinstance(self._profile[k], dict) and isinstance(v, dict):
                self._profile[k].update(v)
            else:
                self._profile[k] = v

    async def save(self, path):
        p = Path(path) if isinstance(path, str) else path
        p.parent.mkdir(parents=True, exist_ok=True)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: p.write_text(json.dumps(self._profile, indent=2)))

    async def load(self, path):
        p = Path(path) if isinstance(path, str) else path
        if not p.exists():
            return
        loop = asyncio.get_running_loop()
        self._profile = await loop.run_in_executor(None, lambda: json.loads(p.read_text()))
