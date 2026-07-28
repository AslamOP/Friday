"""Native persistent long-term memory for FRIDAY.

This package provides the automatic memory service that extracts durable facts
from conversations in the background and persists them across sessions. It is
started and stopped as part of the ``jarvis serve`` / ``jarvis chat`` lifecycle
and configured via the ``[memory]`` section of ``config.toml``.
"""

from __future__ import annotations

from friday.memory.extractor import FactExtractor
from friday.memory.service import (
    MemoryService,
    build_memory_service,
    publish_completed_exchange,
)
from friday.memory.store import (
    Fact,
    FactStore,
    LocalFactStore,
    create_fact_store,
)

__all__ = [
    "Fact",
    "FactStore",
    "FactExtractor",
    "LocalFactStore",
    "MemoryService",
    "build_memory_service",
    "create_fact_store",
    "publish_completed_exchange",
]
