from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from friday._paths import cfg_file


@dataclass
class Settings:
    model: str = ""
    temp: float = 0.7
    tokens: int = 2048
    expert: str = "chat"
    rounds: int = 10
    provider: str = "local"
    endpoints: dict[str, dict] = field(default_factory=lambda: {
        "local": {"url": "http://localhost:11434/v1", "key": ""},
    })


def load(path: str | Path | None = None) -> Settings:
    s = Settings()
    p = Path(path) if path else cfg_file()
    if not p.exists():
        return s
    raw = p.read_text()
    import tomllib
    data = tomllib.loads(raw)
    eng = data.get("engine", {})
    if "provider" in eng:
        s.provider = eng["provider"]
    if "endpoints" in eng:
        s.endpoints.update(eng["endpoints"])
    ai = data.get("ai", {})
    if "model" in ai:
        s.model = ai["model"]
    if "temp" in ai:
        s.temp = ai["temp"]
    if "tokens" in ai:
        s.tokens = ai["tokens"]
    ag = data.get("expert", {})
    if "default" in ag:
        s.expert = ag["default"]
    if "rounds" in ag:
        s.rounds = ag["rounds"]
    return s


def seed():
    p = cfg_file()
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("""[ai]
model = ""
temp = 0.7
tokens = 2048

[expert]
default = "chat"
rounds = 10

[engine]
provider = "local"

[engine.endpoints]
[engine.endpoints.local]
url = "http://localhost:11434/v1"
key = ""
""")
    return p
