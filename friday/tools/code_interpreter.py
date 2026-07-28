from __future__ import annotations
import sys
import io
import contextlib
from friday.core.tool import Tool

class CodeInterpreter(Tool):
    name = "code_interpreter"
    description = "Execute Python code in a sandboxed environment"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to execute"},
        },
        "required": ["code"],
    }
    
    def run(self, code: str) -> str:
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec(code, {"__builtins__": __builtins__})
            out = stdout.getvalue()
            err = stderr.getvalue()
            result = out or "(no output)"
            if err:
                result += f"\nSTDERR:\n{err}"
            return result[:3000]
        except Exception as e:
            return f"Execution error: {e}"
