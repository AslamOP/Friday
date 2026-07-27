from ..base import BaseAgent, Context, Result, Task
from . import prompts
from .pyq_parser import PYQParser
from friday.router.provider_registry import ProviderRegistry
from pathlib import Path
import re
PYQ_RE = re.compile(r"(parse|read|extract)\s+(pyq|pdf|paper)\s+(\S+\.pdf)", re.IGNORECASE)
class AcademicTutorAgent(BaseAgent):
    name = "academic_tutor"
    def __init__(self):
        super().__init__(model_preference="anthropic/claude-3.5-sonnet")
        self._router = ProviderRegistry(); self._pyq = PYQParser()
    async def handle(self, task, context):
        m = PYQ_RE.search(context.user_input)
        if m:
            p = Path(m.group(3))
            if not p.exists(): return Result(success=False, output=f"Not found: {p}", agent=self.name)
            entries = await self._pyq.parse_pdf(p)
            if not entries: return Result(success=False, output="No questions found", agent=self.name)
            lines = [f"**{len(entries)}** questions from {p.name}:\n"]
            for i, e in enumerate(entries[:5], 1): lines.append(f"{i}. [{e.subject}] {e.year} {e.topic} ({e.marks}m)")
            return Result(success=True, output="\n".join(lines), agent=self.name)
        r = await self._router.route("study", prompts.PROMPT.format(input=context.user_input), prompts.SYSTEM_PROMPT)
        return Result(success=True, output=r.get("content", ""), agent=self.name)
    async def can_handle(self, intent): return 0.9 if intent == "study" else 0.1
