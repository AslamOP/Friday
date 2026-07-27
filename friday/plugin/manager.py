import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

from friday.config import get_config
from friday.plugin.base import Plugin

logger = logging.getLogger("friday.plugin_manager")


def _default_plugin_dir() -> Path:
    cfg = get_config()
    p = Path("friday/plugins")
    if p.is_dir():
        return p.resolve()
    alt = Path(__file__).parent.parent / "plugins"
    if alt.is_dir():
        return alt.resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p.resolve()


class PluginManager:
    def __init__(self, plugin_dir: str | Path | None = None):
        self.plugin_dir = Path(plugin_dir) if plugin_dir else _default_plugin_dir()
        self._plugins: dict[str, Plugin] = {}
        self._orchestrator: Any = None

    async def discover_and_load_all(self, orchestrator: Any) -> int:
        self._orchestrator = orchestrator
        count = 0
        if not self.plugin_dir.is_dir():
            logger.info("Plugin dir %s not found, skipping", self.plugin_dir)
            return 0
        for entry in sorted(self.plugin_dir.iterdir()):
            name = None
            if entry.is_file() and entry.suffix == ".py" and not entry.name.startswith("_"):
                name = entry.stem
            elif entry.is_dir() and (entry / "__init__.py").exists() and not entry.name.startswith("_"):
                name = entry.name
            if name is None:
                continue
            try:
                ok = await self._load_module(name, entry)
                if ok:
                    count += 1
            except Exception as e:
                logger.error("Failed to load plugin %s: %s", name, e)
        logger.info("Loaded %d plugin(s) from %s", count, self.plugin_dir)
        return count

    async def load_plugin(self, name: str, orchestrator: Any) -> bool:
        self._orchestrator = orchestrator
        for entry in sorted(self.plugin_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".py" and entry.stem == name and not entry.name.startswith("_"):
                return await self._load_module(name, entry)
            if entry.is_dir() and entry.name == name and not name.startswith("_") and (entry / "__init__.py").exists():
                return await self._load_module(name, entry)
        logger.warning("Plugin %s not found in %s", name, self.plugin_dir)
        return False

    async def unload_plugin(self, name: str) -> bool:
        plugin = self._plugins.pop(name, None)
        if plugin is None:
            logger.warning("Plugin %s not loaded", name)
            return False
        try:
            await plugin.on_unload(self._orchestrator)
        except Exception as e:
            logger.error("Error unloading plugin %s: %s", name, e)
        logger.info("Unloaded plugin %s", name)
        return True

    def list_plugins(self) -> list[dict]:
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "class": type(p).__name__,
            }
            for p in self._plugins.values()
        ]

    def get_plugin(self, name: str) -> Plugin | None:
        return self._plugins.get(name)

    async def _load_module(self, name: str, entry: Path) -> bool:
        if name in self._plugins:
            logger.debug("Plugin %s already loaded", name)
            return False
        if entry.is_file():
            spec = importlib.util.spec_from_file_location(f"friday.plugins.{name}", entry)
        else:
            spec = importlib.util.spec_from_file_location(f"friday.plugins.{name}", entry / "__init__.py")
        if spec is None or spec.loader is None:
            logger.warning("Could not load spec for %s", name)
            return False
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        found = False
        for attr_name in dir(module):
            cls = getattr(module, attr_name)
            if isinstance(cls, type) and issubclass(cls, Plugin) and cls is not Plugin:
                instance = cls()
                try:
                    await instance.on_load(self._orchestrator)
                except Exception as e:
                    logger.error("Plugin %s on_load failed: %s", name, e)
                    continue
                self._plugins[instance.name] = instance
                found = True
                logger.info("Loaded plugin %s v%s: %s", instance.name, instance.version, instance.description)
        if not found:
            logger.info("No Plugin subclass found in %s", name)
            del sys.modules[spec.name]
            return False
        return True
