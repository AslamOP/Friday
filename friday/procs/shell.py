"""Shell command execution."""

from __future__ import annotations

import subprocess

from friday._registry import Catalog
from friday._tools import Outcome, Proc, Spec


@Catalog.tag("proc", "sh")
class ShellProc(Proc):
    label = "sh"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="sh",
            desc="Execute a shell command",
            params={
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "Command to run"},
                    "timeout": {"type": "integer", "description": "Seconds", "default": 30},
                },
                "required": ["cmd"],
            },
            sensitive=True,
        )

    def run(self, **kw) -> Outcome:
        cmd = kw.get("cmd", "")
        timeout = kw.get("timeout", 30)
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            out = r.stdout[:4000]
            err = r.stderr[:2000]
            if err:
                out += f"\nSTDERR:\n{err}" if out else err
            return Outcome(action="sh", text=out or "(empty)")
        except subprocess.TimeoutExpired:
            return Outcome(action="sh", text=f"timed out ({timeout}s)", ok=False)
        except Exception as e:
            return Outcome(action="sh", text=f"error: {e}", ok=False)
