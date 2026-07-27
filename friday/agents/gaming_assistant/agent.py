from ..base import BaseAgent, Context, Result, Task
from . import prompts
from friday.router.provider_registry import ProviderRegistry
import json
from pathlib import Path

CONFIG_PATH = Path("~/.config/friday/gaming_profile.json").expanduser()


def _load_games():
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text())
    except Exception:
        pass
    return {}


def _save_games(data):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


class GamingAssistantAgent(BaseAgent):
    name = "gaming_assistant"

    def __init__(self):
        super().__init__(model_preference="openai/gpt-4o-mini")
        self._router = ProviderRegistry()

    async def handle(self, task, context):
        text = context.user_input
        low = text.lower()
        games = _load_games()

        # handle "i play <games>" to register games
        if low.startswith("i play") or low.startswith("i am playing") or "play" in low and len(low) < 100:
            raw = text
            import re
            game_names = re.findall(r'(?:play(?:ing)?\s+)([\w\s]+?)(?:,|\.|and|$)', low)
            if not game_names:
                game_names = [low.replace("i play", "").replace("i am playing", "").strip().strip(".,")]
            for g in game_names:
                gn = g.strip()
                if gn and gn not in games:
                    games[gn] = {"known": True, "sessions": 0}
            _save_games(games)

        game_context = ""
        if games:
            game_context = "Known games: " + ", ".join(games.keys())

        prompt_content = text
        if game_context:
            prompt_content = f"{game_context}\n\nUser message: {text}"

        r = await self._router.route("chat", prompts.PROMPT.format(input=prompt_content), prompts.SYSTEM_PROMPT)
        output = r.get("content", "")

        # track session
        for g in games:
            games[g]["sessions"] = games[g].get("sessions", 0) + 1
        _save_games(games)

        return Result(success=True, output=output, agent=self.name)

    async def can_handle(self, intent):
        return 0.9 if intent == "gaming" else 0.1
