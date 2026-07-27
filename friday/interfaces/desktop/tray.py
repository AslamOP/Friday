import asyncio
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("friday.tray")

_ICON = None


def _create_icon():
    global _ICON
    if _ICON is not None:
        return _ICON
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill=(0, 150, 255, 255))
        draw.text((18, 18), "F", fill=(255, 255, 255, 255))
        _ICON = img
    except Exception:
        _ICON = None
    return _ICON


class FridayTray:
    def __init__(self):
        self._running = False

    def _launch_gui(self):
        friday_dir = Path(__file__).resolve().parent.parent.parent.parent
        main_py = friday_dir / "friday" / "main.py"
        subprocess.Popen(
            [sys.executable, str(main_py), "--gui"],
            cwd=str(friday_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _launch_repl(self):
        friday_dir = Path(__file__).resolve().parent.parent.parent.parent
        main_py = friday_dir / "friday" / "main.py"
        subprocess.Popen(
            [sys.executable, str(main_py)],
            cwd=str(friday_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _show_status(self):
        from friday.router.provider_registry import ProviderRegistry

        async def _check():
            reg = ProviderRegistry()
            await reg.check_all()
            online = [p.name for p in reg.get_online_providers()]
            return online

        try:
            online = asyncio.run(_check())
            from .notifications import Notifier
            asyncio.run(Notifier().success(f"Online: {', '.join(online) or 'none'}"))
        except Exception as e:
            from .notifications import Notifier
            asyncio.run(Notifier().warning(f"Status error: {e}"))

    def _refresh_providers(self):
        from friday.router.provider_registry import ProviderRegistry

        async def _do():
            reg = ProviderRegistry()
            await reg.check_all()
            online = [p.name for p in reg.get_online_providers()]
            return online

        try:
            online = asyncio.run(_do())
            from .notifications import Notifier
            asyncio.run(Notifier().info(f"Providers refreshed: {', '.join(online) or 'none online'}"))
        except Exception as e:
            from .notifications import Notifier
            asyncio.run(Notifier().warning(f"Refresh error: {e}"))

    def run(self):
        import pystray
        icon_img = _create_icon()
        menu = pystray.Menu(
            pystray.MenuItem("Open GUI", self._launch_gui, default=True),
            pystray.MenuItem("Open REPL", self._launch_repl),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Check Status", self._show_status),
            pystray.MenuItem("Refresh Providers", self._refresh_providers),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )
        self._running = True
        self._icon = pystray.Icon("friday", icon_img, "FRIDAY AI OS", menu)
        self._icon.run()

    def _quit(self):
        self._running = False
        if hasattr(self, "_icon"):
            self._icon.stop()
