from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Author(Enum):
    SYSTEM = "system"
    USER = "user"
    BOT = "bot"
    TOOL = "tool"


@dataclass
class Entry:
    author: Author
    text: str
    calls: list[dict] | None = None
    call_id: str = ""
    label: str = ""


@dataclass
class Call:
    ref: str
    action: str
    args: str | dict


@dataclass
class Outcome:
    action: str
    text: str
    ok: bool = True
    elapsed: float = 0.0
    meta: dict = field(default_factory=dict)


@dataclass
class Context:
    history: list[Entry] = field(default_factory=list)

    def push(self, e: Entry):
        self.history.append(e)


@dataclass
class Turn:
    text: str
    results: list[Outcome] = field(default_factory=list)
    rounds: int = 0
    meta: dict = field(default_factory=dict)
