from ..base import BaseAgent, Context, Result, Task
from . import prompts
from .indexer import FileIndexer
from friday.memory.knowledge_graph import KnowledgeGraph
from friday.memory.vector_store import VectorStore
from friday.router.omniroute import OmniRouteClient
from friday.tools.file_ops import FileOps
import re
IDX = re.compile(r"(index|scan|crawl)\s+(directory|folder|path|file)\s+(\S+)", re.IGNORECASE)
SCH = re.compile(r"(find|search|glob)\s+(\S+)", re.IGNORECASE)
class KnowledgeManagerAgent(BaseAgent):
    name = "knowledge_manager"
    def __init__(self):
        super().__init__(model_preference="openai/gpt-4o-mini")
        self._router = OmniRouteClient(); self._kg = KnowledgeGraph(); self._vs = VectorStore()
        self._idx = FileIndexer(); self._fs = FileOps()
    async def handle(self, task, context):
        text = context.user_input
        m = IDX.search(text)
        if m:
            report = await self._idx.index_directory(m.group(3))
            return Result(success=True, output=f"Indexed {report.indexed}/{report.total_files} ({report.skipped} skipped)", agent=self.name)
        m = SCH.search(text)
        if m:
            fr = await self._fs.search(m.group(2))
            return Result(success=True, output=fr.output, agent=self.name)
        kg = self._kg.search(text); vs = self._vs.search(text); ctx = ""
        if kg: ctx += "KG:\n" + "\n".join(f"- {e['id']}" for e in kg[:3]) + "\n"
        if vs: ctx += "Docs:\n" + "\n".join(f"- {e['text'][:100]}" for e in vs[:3])
        r = await self._router.route("knowledge", prompts.PROMPT.format(input=f"{text}\n\n{ctx}" if ctx else text), prompts.SYSTEM_PROMPT)
        return Result(success=True, output=r.get("content", ""), agent=self.name)
    async def can_handle(self, intent): return 0.9 if intent == "knowledge" else 0.15
