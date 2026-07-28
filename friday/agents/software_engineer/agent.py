import re
from pathlib import Path

from friday.router.provider_registry import ProviderRegistry
from friday.tools.file_ops import FileOps
from friday.tools.shell_sandbox import ShellSandbox

from ..base import BaseAgent, Result
from . import prompts

CB = re.compile(r"```(\w+)?\n(.+?)```", re.DOTALL)
_RUN = re.compile(r"(run|execute|bash|shell)\s+`([^`]+)`", re.IGNORECASE)


class SoftwareEngineerAgent(BaseAgent):
    name = "software_engineer"

    def __init__(self):
        super().__init__(model_preference="deepseek/deepseek-coder-33b-instruct")
        self._router = ProviderRegistry()
        self._sandbox = ShellSandbox()
        self._fs = FileOps()
        self._mode = None
        self._savedir = Path.cwd()

    async def _write_blocks(self, text, outdir=None):
        outdir = outdir or self._savedir
        files = []
        for lang, code in CB.findall(text):
            if not code.strip():
                continue
            ext_map = {
                "py": "py", "js": "js", "ts": "ts", "html": "html", "css": "css",
                "json": "json", "sh": "sh", "bash": "sh", "yaml": "yaml",
                "yml": "yml", "xml": "xml", "sql": "sql", "c": "c", "cpp": "cpp",
                "h": "h", "java": "java", "go": "go", "rs": "rs", "rb": "rb",
                "php": "php", "swift": "swift", "kt": "kt", "dart": "dart",
            }
            ext = ext_map.get((lang or "").lower(), "txt")
            fpath = Path(outdir) / f"gen.{ext}"
            n = 1
            while fpath.exists():
                fpath = Path(outdir) / f"gen_{n}.{ext}"
                n += 1
            r = await self._fs.write(str(fpath), code.strip())
            if r.success:
                files.append(fpath.name)
        return files

    async def _detect_mode(self, text):
        low = text.lower()
        if any(kw in low for kw in ("architect", "design", "structure", "flow", "component")):
            return "architecture"
        if any(kw in low for kw in ("debug", "bug", "fix", "issue", "error", "broken")):
            return "debug"
        if any(kw in low for kw in ("test", "pytest", "unittest")):
            return "test"
        if any(kw in low for kw in ("mini", "quick", "short", "small", "help")):
            return "mini"
        if any(kw in low for kw in ("vibe", "full", "build", "create", "make", "write", "generate")):
            return "vibe"
        return self._mode or "vibe"

    async def handle(self, task, context):
        text = context.user_input

        # detect save directory from user input
        save_match = re.search(r'(?:save to|in dir|output|path)\s+["\']?(.+?)["\']?(?:\s|$)', text, re.IGNORECASE)
        if save_match:
            self._savedir = Path(save_match.group(1).strip()).expanduser().resolve()
            self._savedir.mkdir(parents=True, exist_ok=True)

        # detect and set mode
        mode = await self._detect_mode(text)
        if "mode" in text.lower() and re.search(r'mode\s+(\w+)', text, re.IGNORECASE):
            mode_match = re.search(r'mode\s+(\w+)', text, re.IGNORECASE)
            if mode_match:
                m = mode_match.group(1).lower()
                mode_map = {"vibe": "vibe", "arch": "architecture", "architecture": "architecture",
                            "debug": "debug", "test": "test", "mini": "mini", "help": "mini"}
                mode = mode_map.get(m, mode)
            self._mode = mode

        system_prompt = prompts.SYSTEM_PROMPT
        moded_prompt = prompts.PROMPT.format(input=text)
        if mode:
            moded_prompt += f"\n\nMode: {mode.upper()}"

        # add save dir context
        moded_prompt += f"\nSave directory: {self._savedir}"

        parts = []
        content = ""

        # try up to 2 rounds to ensure complete response
        for attempt in range(2):
            r = await self._router.route("code", moded_prompt, system_prompt)
            content = r.get("content", "")
            if not content:
                continue
            # check if response looks truncated (ends mid-sentence)
            if attempt == 0 and content and not content.rstrip().endswith(("```", ".", ")", "}", "]", '"', "'", "`")):
                moded_prompt = f"Continue from where you left off. Do not repeat. Start from:\n...{content[-200:]}"
                continue
            break

        parts.append(f"## Generated ({mode.upper()} mode)\n\n{content}")

        # write code blocks to files
        files = await self._write_blocks(content)
        if files:
            parts.append("## Written\n- " + "\n- ".join(files))

        # execute shell commands
        for m in _RUN.findall(text):
            sr = await self._sandbox.run(m[1])
            block = f"## `{m[1][:60]}`\n"
            if sr.output:
                block += f"```\n{sr.output[:500]}\n```\n"
            if sr.error:
                block += f"stderr:\n```\n{sr.error[:200]}\n```\n"
            block += f"→ exit {sr.returncode} ({sr.duration:.1f}s)"
            parts.append(block)

        # auto-run tests if in test mode or user asked
        if mode == "test" or "test" in text.lower():
            # find test file or run pytest
            if (self._savedir / "test").exists() or (self._savedir / "tests").exists():
                sr = await self._sandbox.run("python -m pytest -v 2>&1 || true")
                parts.append(f"## Tests\n```\n{sr.output[:800]}\n```")

        return Result(success=True, output="\n\n".join(parts), agent=self.name)

    async def can_handle(self, intent):
        return 0.95 if intent == "code" else 0.1
