import asyncio, logging
from friday.config import get_config
from friday.memory.knowledge_graph import KnowledgeGraph
from friday.memory.user_profile import UserProfile
from friday.memory.project_memory import ProjectMemory
logger = logging.getLogger("friday.persistence")
_INTERVAL = 60
class PersistenceManager:
    def __init__(self):
        d = get_config().data_dir; d.mkdir(parents=True, exist_ok=True)
        self._kg_path = d / "kg.json"; self._profile_path = d / "profile.json"; self._projects_path = d / "projects.json"
        self._task: asyncio.Task | None = None
    async def load_all(self):
        KnowledgeGraph().load(self._kg_path); UserProfile().load(self._profile_path); ProjectMemory().load(self._projects_path)
        logger.info("Memory loaded")
    async def save_all(self):
        KnowledgeGraph().save(self._kg_path); UserProfile().save(self._profile_path); ProjectMemory().save(self._projects_path)
    async def start_auto_save(self):
        await self.load_all()
        async def loop():
            while True: await asyncio.sleep(_INTERVAL); await self.save_all()
        self._task = asyncio.create_task(loop()); logger.info("Auto-save every %ds", _INTERVAL)
    async def stop(self):
        if self._task: self._task.cancel(); self._task = None
        await self.save_all(); logger.info("Persistence stopped")
