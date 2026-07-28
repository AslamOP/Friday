import asyncio
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from friday.memory.knowledge_graph import KnowledgeGraph
from friday.memory.vector_store import VectorStore


@dataclass
class IndexReport:
    total_files: int = 0
    indexed: int = 0
    skipped: int = 0
    errors: int = 0
    paths: list[str] = field(default_factory=list)


_IGNORE = {"__pycache__", ".git", ".venv", "node_modules", ".pytest_cache", "data"}
_TEXTS = {".py", ".js", ".ts", ".html", ".css", ".md", ".json", ".txt", ".sh"}


class FileIndexer:
    def __init__(self):
        self._kg = KnowledgeGraph()
        self._vs = VectorStore()
        self._seen = set()

    async def index_file(self, path):
        p = Path(path) if isinstance(path, str) else path
        if not p.exists() or not p.is_file():
            return False
        try:
            loop = asyncio.get_running_loop()
            h = await loop.run_in_executor(None, lambda: hashlib.sha256(p.read_bytes()).hexdigest())
            if h in self._seen:
                return False
            content = await loop.run_in_executor(None, lambda: p.read_text(errors="replace"))
            eid = f"file:{p.resolve()}"
            self._kg.add_entity(eid, "file", {"path": str(p.resolve()), "size": p.stat().st_size})
            self._vs.add_entry(eid, content[:5000])
            self._seen.add(h)
            return True
        except Exception:
            return False

    async def index_directory(self, path, recursive=True):
        report = IndexReport()
        root = Path(path) if isinstance(path, str) else path
        if not root.exists() or not root.is_dir():
            return report
        for entry in sorted(root.glob("**/*" if recursive else "*")):
            if not entry.is_file():
                continue
            rel = entry.relative_to(root)
            if any(p.startswith(".") or p in _IGNORE for p in rel.parts):
                continue
            report.total_files += 1
            if entry.suffix not in _TEXTS:
                report.skipped += 1
                continue
            if await self.index_file(entry):
                report.indexed += 1
                report.paths.append(str(rel))
            else:
                report.skipped += 1
        return report
