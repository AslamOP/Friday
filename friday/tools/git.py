from __future__ import annotations
import subprocess
from friday.core.tool import Tool

class GitTool(Tool):
    name = "git"
    description = "Run git commands"
    parameters = {
        "type": "object",
        "properties": {
            "args": {"type": "string", "description": "Git arguments (e.g. 'status', 'log --oneline -5')"},
            "path": {"type": "string", "description": "Repository path", "default": "."},
        },
        "required": ["args"],
    }
    
    def run(self, args: str, path: str = ".") -> str:
        try:
            result = subprocess.run(
                ["git"] + args.split(),
                capture_output=True, text=True, timeout=30, cwd=path
            )
            return (result.stdout or result.stderr)[:2000]
        except Exception as e:
            return f"Git error: {e}"
