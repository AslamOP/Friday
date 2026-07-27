import asyncio
import logging
import uuid

logger = logging.getLogger("friday.task_scheduler")


class ScheduledTask:
    def __init__(self, delay: float, coro, task_id: str = ""):
        self.id = task_id or uuid.uuid4().hex[:8]
        self.delay = delay
        self.coro = coro
        self._task: asyncio.Task | None = None

    async def run(self):
        await asyncio.sleep(self.delay)
        return await self.coro


class TaskScheduler:
    def __init__(self):
        self._tasks: list[ScheduledTask] = []
        self._runner: asyncio.Task | None = None
        self._running = False

    async def add(self, delay: float, coro, task_id: str = ""):
        st = ScheduledTask(delay, coro, task_id)
        self._tasks.append(st)
        return st.id

    async def start(self):
        self._running = True
        self._runner = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if self._runner:
            self._runner.cancel()
            self._runner = None

    async def _loop(self):
        while self._running:
            if not self._tasks:
                await asyncio.sleep(0.5)
                continue
            st = self._tasks.pop(0)
            try:
                result = await st.run()
                logger.info("Task %s completed: %s", st.id, result)
            except Exception as e:
                logger.warning("Task %s failed: %s", st.id, e)
