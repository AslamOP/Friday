import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("friday.git_tool")

_BLOCKED_PREFIXES = ("git push --force", "git push -f", "git reset --hard", "git rebase")
_DEFAULT_REPO = Path.cwd()


@dataclass
class GitResult:
    success: bool
    output: str = ""
    error: str = ""
    returncode: int = -1


class GitTool:
    def __init__(self, repo_path: str | Path | None = None):
        self._repo = Path(repo_path).resolve() if repo_path else _DEFAULT_REPO

    def _safe(self, command: str) -> tuple[bool, str]:
        for prefix in _BLOCKED_PREFIXES:
            if command.strip().startswith(prefix):
                return False, f"Blocked destructive git command: {prefix}"
        return True, ""

    async def run(self, *args: str) -> GitResult:
        cmd = ["git"] + list(args)
        safe, reason = self._safe("git " + " ".join(args))
        if not safe:
            return GitResult(success=False, error=reason, returncode=-1)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._repo),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            out = stdout.decode(errors="replace").strip()
            err = stderr.decode(errors="replace").strip()
            return GitResult(
                success=proc.returncode == 0,
                output=out,
                error=err,
                returncode=proc.returncode or 0,
            )
        except asyncio.TimeoutError:
            return GitResult(success=False, error="Timeout (30s)", returncode=-1)
        except Exception as e:
            return GitResult(success=False, error=str(e), returncode=-1)

    async def status(self) -> GitResult:
        return await self.run("status", "--short")

    async def log(self, count: int = 10) -> GitResult:
        return await self.run("log", f"--oneline", "-n", str(count))

    async def diff(self, staged: bool = False) -> GitResult:
        args = ["diff"]
        if staged:
            args.append("--cached")
        return await self.run(*args)

    async def branch(self) -> GitResult:
        return await self.run("branch", "-a")

    async def commit(self, message: str) -> GitResult:
        return await self.run("commit", "-m", message)
