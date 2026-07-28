import re
from pathlib import Path

from friday.router.provider_registry import ProviderRegistry
from friday.tools.file_ops import FileOps  # noqa: F401

from ..base import BaseAgent, Result
from . import prompts


class AutomationEngineerAgent(BaseAgent):
    name = "automation_engineer"

    def __init__(self):
        super().__init__(model_preference="deepseek/deepseek-coder-33b-instruct")
        self._router = ProviderRegistry()
        self._fs = FileOps()
        self._output_dir = Path.cwd() / "cad_output"

    async def handle(self, task, context):
        text = context.user_input

        # detect output save directory
        save_match = re.search(r'(?:save to|output|dir)\s+["\']?(.+?)["\']?(?:\s|$)', text, re.IGNORECASE)
        if save_match:
            self._output_dir = Path(save_match.group(1).strip()).expanduser().resolve()
            self._output_dir.mkdir(parents=True, exist_ok=True)

        # detect project name
        proj_match = re.search(r'(?:project|for)\s+["\']?(.+?)["\']?(?:\s|$)', text, re.IGNORECASE)
        if proj_match:
            proj_name = proj_match.group(1).strip().replace(" ", "_")
            self._output_dir = Path.cwd() / "cad_output" / proj_name
            self._output_dir.mkdir(parents=True, exist_ok=True)

        r = await self._router.route("automate", prompts.PROMPT.format(input=text), prompts.SYSTEM_PROMPT)
        content = r.get("content", "")

        # extract and save code blocks
        cb = re.compile(r"```(\w+)?\n(.+?)```", re.DOTALL)
        saved = []
        for lang, code in cb.findall(content):
            if not code.strip():
                continue
            ext_map = {"py": "py", "js": "js", "m": "m", "cae": "py", "f90": "f90"}
            ext = ext_map.get((lang or "").lower(), "txt")
            fpath = self._output_dir / f"cad_script.{ext}"
            n = 1
            while fpath.exists():
                fpath = self._output_dir / f"cad_script_{n}.{ext}"
                n += 1
            result = await self._fs.write(str(fpath), code.strip())
            if result.success:
                saved.append(str(fpath))

        if saved:
            content += "\n\n📁 **Saved scripts:**\n" + "\n".join(f"- `{s}`" for s in saved)

        return Result(success=True, output=content, agent=self.name)

    async def can_handle(self, intent):
        return 0.9 if intent == "automate" else 0.1
