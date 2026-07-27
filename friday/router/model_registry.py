import logging
logger = logging.getLogger("friday.model_registry")

_ZEN_PRIMARY = {
    "code": "north-mini-code-free",
    "automate": "north-mini-code-free",
    "research": "nemotron-3-ultra-free",
    "study": "nemotron-3-ultra-free",
    "challenge": "nemotron-3-ultra-free",
    "plan": "deepseek-v4-flash-free",
    "knowledge": "deepseek-v4-flash-free",
    "gaming": "deepseek-v4-flash-free",
    "chat": "deepseek-v4-flash-free",
}

_ZEN_FALLBACK = [
    "big-pickle",
    "mimo-v2.5-free",
    "ling-3.0-flash-free",
    "laguna-s-2.1-free",
]

_OR_FALLBACK = [
    "inclusionai/ling-3.0-flash:free",
    "poolside/laguna-xs-2.1:free",
    "poolside/laguna-m.1:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "openai/gpt-oss-20b:free",
]


class ModelRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_zen_model(self, task_type: str) -> str:
        return _ZEN_PRIMARY.get(task_type, "deepseek-v4-flash-free")

    def get_zen_fallback(self) -> list[str]:
        return list(_ZEN_FALLBACK)

    def get_or_fallback(self) -> list[str]:
        return list(_OR_FALLBACK)

    def list_task_types(self):
        return list(_ZEN_PRIMARY.keys())
