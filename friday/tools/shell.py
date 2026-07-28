from __future__ import annotations
import asyncio
import shlex
from friday.core.tool import Tool

class ShellExec(Tool):
    name = "shell_exec"
    description = "Execute a shell command and return output"
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to run"},
            "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
        },
        "required": ["command"],
    }
    
    def run(self, command: str, timeout: int = 30) -> str:
        import subprocess
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            out = result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
            err = result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
            if err:
                return f"{out}\nSTDERR:\n{err}" if out else err
            return out or "(no output)"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s"
        except Exception as e:
            return f"Shell error: {e}"
