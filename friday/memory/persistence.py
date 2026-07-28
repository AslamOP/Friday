import asyncio
import logging

from friday.config import get_config
from friday.memory.knowledge_graph import KnowledgeGraph
from friday.memory.project_memory import ProjectMemory
from friday.memory.user_profile import UserProfile

logger = logging.getLogger("friday.persistence")
_INTERVAL = 60


class PersistenceManager:
    def __init__(self):
        d = get_config().data_dir
        d.mkdir(parents=True, exist_ok=True)
        self._kg_path = d / "kg.json"
        self._profile_path = d / "profile.json"
        self._projects_path = d / "projects.json"
        self._task: asyncio.Task | None = None

    async def load_all(self):
        errors = []
        for name, path, obj in [
            ("kg", self._kg_path, KnowledgeGraph()),
            ("profile", self._profile_path, UserProfile()),
            ("projects", self._projects_path, ProjectMemory()),
        ]:
            try:
                await obj.load(path)
            except Exception as e:
                errors.append(f"{name}: {e}")
                logger.warning("Failed to load %s from %s: %s", name, path, e)
        if errors:
            logger.warning("Memory loaded with %d error(s): %s", len(errors), "; ".join(errors))
        else:
            logger.info("Memory loaded")

    async def save_all(self):
        for name, path, obj in [
            ("kg", self._kg_path, KnowledgeGraph()),
            ("profile", self._profile_path, UserProfile()),
            ("projects", self._projects_path, ProjectMemory()),
        ]:
            try:
                await obj.save(path)
            except Exception as e:
                logger.warning("Failed to save %s to %s: %s", name, path, e)

    async def start_auto_save(self):
        await self.load_all()

        async def loop():
            while True:
                try:
                    await asyncio.sleep(_INTERVAL)
                    await self.save_all()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Auto-save error: %s", e)

        self._task = asyncio.create_task(loop())
        logger.info("Auto-save every %ds", _INTERVAL)

    async def stop(self):
        if self._task:
            self._task.cancel()
            self._task = None
        await self.save_all()
        logger.info("Persistence stopped")
