from ..base import BaseAgent, Context, Result, Task
from . import prompts
from friday.router.provider_registry import ProviderRegistry
from friday.tools.shell_sandbox import ShellSandbox
from friday.tools.file_ops import FileOps
import re
CB = re.compile(r"```(\w+)?\n(.+?)```", re.DOTALL)
_RUN = re.compile(r"(run|execute|bash|shell)\s+`([^`]+)`", re.IGNORECASE)
class SoftwareEngineerAgent(BaseAgent):
    name = "software_engineer"
    def __init__(self):
        super().__init__(model_preference="deepseek/deepseek-coder-33b-instruct")
        self._router = ProviderRegistry(); self._sandbox = ShellSandbox(); self._fs = FileOps()
    async def _write_blocks(self, text, outdir="."):
        files = []
        for lang, code in CB.findall(text):
            if not code.strip(): continue
            ext = {"py":"py","js":"js","ts":"ts","html":"html","json":"json","sh":"sh"}.get(lang or "", "txt")
            r = await self._fs.write(f"{outdir}/gen.{ext}", code.strip())
            if r.success: files.append(f"gen.{ext}")
        return files
    async def handle(self, task, context):
        text = context.user_input; parts = []
        r = await self._router.route("code", prompts.PROMPT.format(input=text), prompts.SYSTEM_PROMPT)
        content = r.get("content", ""); parts.append(f"## Generated\n\n{content}")
        files = await self._write_blocks(content)
        if files: parts.append("## Written\n- " + "\n- ".join(files))
        for m in _RUN.findall(text):
            sr = await self._sandbox.run(m[1])
            block = f"## `{m[1][:60]}`\n"
            if sr.output: block += f"```\n{sr.output[:500]}\n```\n"
            if sr.error: block += f"stderr:\n```\n{sr.error[:200]}\n```\n"
            block += f"→ exit {sr.returncode} ({sr.duration:.1f}s)"; parts.append(block)
        if "test" in text.lower():
            sr = await self._sandbox.run("python -m pytest -v 2>&1 || true")
            parts.append(f"## Tests\n```\n{sr.output[:500]}\n```")
        return Result(success=True, output="\n\n".join(parts), agent=self.name)
    async def can_handle(self, intent): return 0.95 if intent == "code" else 0.1
