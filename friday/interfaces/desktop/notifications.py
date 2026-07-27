import asyncio
import logging
import subprocess
import shutil

logger = logging.getLogger("friday.notifications")


class Notifier:
    def __init__(self):
        self._available = shutil.which("notify-send") is not None

    async def notify(self, title: str, message: str, urgency: str = "normal"):
        if not self._available:
            logger.debug("notify-send not available")
            return
        try:
            proc = await asyncio.create_subprocess_exec(
                "notify-send", "--urgency", urgency,
                "--app-name", "FRIDAY",
                title, message,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
        except Exception as e:
            logger.debug("notify failed: %s", e)

    async def success(self, message: str):
        await self.notify("FRIDAY", message, "normal")

    async def warning(self, message: str):
        await self.notify("FRIDAY", message, "critical")
