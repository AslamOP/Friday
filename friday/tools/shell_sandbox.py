import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("friday.shell_sandbox")
_BLOCKED = {"rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:", "> /dev/sda"}
_MAX_OUT = 100_000
_TIMEOUT = 30
_WORK = Path.cwd()


@dataclass
class ShellResult:
    success: bool
    output: str
    error: str = ""
    returncode: int = -1
    duration: float = 0.0


class ShellSandbox:
    def __init__(self, workspace: str | Path | None = None):
        self._workspace = Path(workspace) if workspace else _WORK
        self._workspace.mkdir(parents=True, exist_ok=True)

    def _safe(self, cmd: str) -> tuple[bool, str]:
        for p in _BLOCKED:
            if p in cmd.lower():
                return False, f"Blocked: {p}"
        return True, ""

    async def run(
        self, command: str, timeout: int = _TIMEOUT, cwd: str | Path | None = None, env: dict | None = None
    ) -> ShellResult:
        safe, reason = self._safe(command)
        if not safe:
            return ShellResult(success=False, output="", error=reason, returncode=-1)
        wd = Path(cwd) if cwd else self._workspace
        import time

        start = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(wd),
                env={**os.environ, **(env or {})},
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ShellResult(
                    success=False,
                    output="",
                    error=f"Timeout {timeout}s",
                    returncode=-1,
                    duration=time.monotonic() - start,
                )
            d = time.monotonic() - start
            return ShellResult(
                success=proc.returncode == 0,
                output=stdout.decode(errors="replace")[:_MAX_OUT],
                error=stderr.decode(errors="replace")[:_MAX_OUT],
                returncode=proc.returncode or 0,
                duration=d,
            )
        except Exception as e:
            return ShellResult(success=False, output="", error=str(e), returncode=-1, duration=time.monotonic() - start)
