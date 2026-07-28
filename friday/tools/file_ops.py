from __future__ import annotations
from pathlib import Path
from friday.core.tool import Tool

WORK_DIR = Path.home() / ".friday" / "workspace"

class FileRead(Tool):
    name = "file_read"
    description = "Read the contents of a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path (absolute or relative to workspace)"},
        },
        "required": ["path"],
    }
    
    def run(self, path: str) -> str:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"File not found: {path}"
        return p.read_text()[:8000]

class FileWrite(Tool):
    name = "file_write"
    description = "Write content to a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    }
    
    def run(self, path: str, content: str) -> str:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written {len(content)} bytes to {path}"

class FileList(Tool):
    name = "file_list"
    description = "List files in a directory"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path", "default": "."},
        },
    }
    
    def run(self, path: str = ".") -> str:
        p = Path(path).expanduser().resolve()
        if not p.is_dir():
            return f"Not a directory: {path}"
        items = []
        for f in p.iterdir():
            suffix = "/" if f.is_dir() else ""
            items.append(f"{f.name}{suffix}")
        return "\n".join(sorted(items)) if items else "(empty)"
