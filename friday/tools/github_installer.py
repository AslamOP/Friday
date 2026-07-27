import asyncio
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("friday.github_installer")

_BASE = Path.home() / "github"


@dataclass
class InstallResult:
    success: bool
    output: str = ""
    repo: str = ""
    path: str = ""
    project_type: str = ""
    error: str = ""


class GitHubInstaller:
    def __init__(self, base_dir: str | Path | None = None):
        self._base = Path(base_dir).resolve() if base_dir else _BASE
        self._base.mkdir(parents=True, exist_ok=True)

    def _parse_url(self, url: str) -> tuple[str, str, str]:
        url = url.strip().rstrip("/").removesuffix(".git")
        if "github.com/" in url:
            parts = url.split("github.com/")[-1].split("/")
        else:
            parts = url.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")
        owner, repo_name = parts[0], parts[1]
        clone_url = f"https://github.com/{owner}/{repo_name}.git"
        dest = self._base / repo_name
        return clone_url, repo_name, str(dest)

    async def install(self, url: str, branch: str = "") -> InstallResult:
        try:
            clone_url, repo_name, dest_str = self._parse_url(url)
            dest = Path(dest_str)
        except ValueError as e:
            return InstallResult(success=False, error=str(e), repo=url)

        if Path(dest).exists():
            return InstallResult(
                success=False,
                error=f"Already exists: {dest}",
                repo=url,
                path=dest,
            )

        steps = []

        steps.append(f"Cloning {clone_url}...")
        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd += ["--branch", branch]
        cmd += [clone_url, dest]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode != 0:
            return InstallResult(
                success=False,
                error=stderr.decode(errors="replace").strip() or f"git clone failed (code {proc.returncode})",
                repo=url,
            )
        steps.append(f"  Cloned to {dest}")

        ptype, build_steps = await self._detect_and_build(dest)
        steps.extend(build_steps)

        output = "\n".join(steps)
        logger.info("Installed %s (%s) at %s", repo_name, ptype, dest)
        return InstallResult(
            success=True,
            output=output,
            repo=clone_url,
            path=dest,
            project_type=ptype,
        )

    async def list_installed(self) -> list[dict]:
        results = []
        for d in sorted(self._base.iterdir()):
            if d.is_dir() and (d / ".git").exists():
                results.append({
                    "name": d.name,
                    "path": str(d),
                    "type": self._detect_type(d),
                })
        return results

    def _detect_type(self, path: Path) -> str:
        if (path / "package.json").exists():
            return "node"
        if (path / "setup.py").exists() or (path / "pyproject.toml").exists() or (path / "requirements.txt").exists():
            return "python"
        if (path / "go.mod").exists():
            return "go"
        if (path / "Cargo.toml").exists():
            return "rust"
        if (path / "Makefile").exists() or (path / "CMakeLists.txt").exists():
            return "c/c++"
        if (path / "Gemfile").exists():
            return "ruby"
        return "unknown"

    async def _detect_and_build(self, path: Path) -> tuple[str, list[str]]:
        ptype = self._detect_type(path)
        steps = [f"  Detected: {ptype}"]
        if ptype == "python":
            req = path / "requirements.txt"
            if req.exists():
                steps.append("  Installing pip deps...")
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, "-m", "pip", "install", "-r", str(req),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
                if proc.returncode == 0:
                    steps.append("  ✓ pip deps installed")
                else:
                    steps.append(f"  ! pip install issue: {stderr.decode(errors='replace')[:200]}")
        elif ptype == "node":
            steps.append("  Running npm install...")
            proc = await asyncio.create_subprocess_exec(
                "npm", "install", cwd=str(path),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            if proc.returncode == 0:
                steps.append("  ✓ npm install done")
            else:
                steps.append(f"  ! npm issue: {stderr.decode(errors='replace')[:200]}")
        elif ptype == "go":
            steps.append("  Running go mod download...")
            proc = await asyncio.create_subprocess_exec(
                "go", "mod", "download", cwd=str(path),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=120)
            steps.append("  ✓ go mod downloaded")
        elif ptype == "rust":
            steps.append("  Building with cargo...")
            proc = await asyncio.create_subprocess_exec(
                "cargo", "build", "--release", cwd=str(path),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            if proc.returncode == 0:
                steps.append("  ✓ cargo build --release done")
            else:
                steps.append(f"  ! cargo issue: {stderr.decode(errors='replace')[:200]}")
        return ptype, steps
