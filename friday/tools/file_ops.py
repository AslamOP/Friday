import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("friday.file_ops")
_WORK = Path.cwd()
_MAX_SIZE = 5 * 1024 * 1024


@dataclass
class FileResult:
    success: bool
    output: str = ""
    data: any = None


class FileOps:
    def __init__(self, workspace: str | Path | None = None):
        self._workspace = Path(workspace) if workspace else _WORK

    def _resolve(self, path):
        p = Path(path)
        return p.resolve() if p.is_absolute() else (self._workspace / p).resolve()

    async def read(self, path) -> FileResult:
        p = self._resolve(path)
        try:
            if not p.exists():
                return FileResult(success=False, output=f"Not found: {p}")
            if p.stat().st_size > _MAX_SIZE:
                return FileResult(success=False, output=f"Too large: {p}")
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, lambda: p.read_text(errors="replace"))
            return FileResult(success=True, output=text, data={"path": str(p)})
        except Exception as e:
            return FileResult(success=False, output=str(e))

    async def write(self, path, content: str) -> FileResult:
        p = self._resolve(path)
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, lambda: (p.parent.mkdir(parents=True, exist_ok=True), p.write_text(content))
            )
            return FileResult(success=True, output=f"Written {len(content)}b to {p}")
        except Exception as e:
            return FileResult(success=False, output=str(e))

    async def search(self, pattern: str, root=None) -> FileResult:
        base = self._resolve(root) if root else self._workspace
        try:
            m = [str(p.relative_to(base)) for p in sorted(base.rglob(pattern))]
            return FileResult(
                success=True, output="\n".join(m) if m else "No matches", data={"count": len(m), "matches": m}
            )
        except Exception as e:
            return FileResult(success=False, output=str(e))

    async def tree(self, root=None, depth: int = 2) -> FileResult:
        base = self._resolve(root) if root else self._workspace
        try:
            lines = [
                (("  " * (len(p.relative_to(base).parts) - 1)) + p.name + ("/" if p.is_dir() else ""))
                for p in sorted(base.rglob("*"))
                if len(p.relative_to(base).parts) <= min(depth, 5)
            ]
            return FileResult(success=True, output="\n".join(lines), data={"count": len(lines)})
        except Exception as e:
            return FileResult(success=False, output=str(e))

    async def info(self, path) -> FileResult:
        p = self._resolve(path)
        try:
            if not p.exists():
                return FileResult(success=False, output=f"Not found: {p}")
            s = p.stat()
            return FileResult(
                success=True,
                output=str({"path": str(p), "type": "dir" if p.is_dir() else "file", "size": s.st_size}),
                data={},
            )
        except Exception as e:
            return FileResult(success=False, output=str(e))
