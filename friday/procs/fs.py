"""File system tools: read, write, list."""

from __future__ import annotations

from pathlib import Path

from friday._registry import Catalog
from friday._tools import Outcome, Proc, Spec


@Catalog.tag("proc", "read")
class ReadProc(Proc):
    label = "read"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="read",
            desc="Read a file",
            params={
                "type": "object",
                "properties": {"path": {"type": "string", "description": "File path"}},
                "required": ["path"],
            },
        )

    def run(self, **kw) -> Outcome:
        p = Path(kw.get("path", "")).expanduser().resolve()
        if not p.exists():
            return Outcome(action="read", text=f"not found: {kw.get('path')}", ok=False)
        return Outcome(action="read", text=p.read_text()[:8000])


@Catalog.tag("proc", "write")
class WriteProc(Proc):
    label = "write"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="write",
            desc="Write content to a file",
            params={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content"},
                },
                "required": ["path", "content"],
            },
        )

    def run(self, **kw) -> Outcome:
        p = Path(kw.get("path", "")).expanduser().resolve()
        c = kw.get("content", "")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(c)
        return Outcome(action="write", text=f"wrote {len(c)} bytes")


@Catalog.tag("proc", "ls")
class ListProc(Proc):
    label = "ls"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="ls",
            desc="List directory contents",
            params={
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Directory", "default": "."}},
            },
        )

    def run(self, **kw) -> Outcome:
        p = Path(kw.get("path", ".")).expanduser().resolve()
        if not p.is_dir():
            return Outcome(action="ls", text=f"not a dir: {kw.get('path')}", ok=False)
        items = [f"{f.name}/" if f.is_dir() else f.name for f in sorted(p.iterdir())]
        return Outcome(action="ls", text="\n".join(items) if items else "(empty)")
