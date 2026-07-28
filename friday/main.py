import asyncio
import json
import logging
import signal
import sys

from friday import __version__
from friday.core.ipc import DAEMON_SOCK, UnixServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("friday")


async def daemon():
    logger.info("FRIDAY v%s daemon starting...", __version__)
    from friday.core.orchestrator import get_orchestrator

    agent_classes = []
    for mod_path, cls_name in [
        ("friday.agents.mentor", "MentorAgent"),
        ("friday.agents.planner", "PlannerAgent"),
        ("friday.agents.software_engineer", "SoftwareEngineerAgent"),
        ("friday.agents.research_scientist", "ResearchScientistAgent"),
        ("friday.agents.automation_engineer", "AutomationEngineerAgent"),
        ("friday.agents.knowledge_manager", "KnowledgeManagerAgent"),
        ("friday.agents.study", "StudyAgent"),
        ("friday.agents.gaming_assistant", "GamingAssistantAgent"),
    ]:
        try:
            mod = __import__(mod_path, fromlist=[cls_name])
            agent_classes.append(getattr(mod, cls_name)())
        except Exception as e:
            logger.warning("Agent %s unavailable: %s", cls_name, e)

    o = get_orchestrator()
    for ac in agent_classes:
        o.register_agent(ac)
    await o.initialize()
    logger.info("FRIDAY v%s daemon ready", __version__)

    ipc_server = UnixServer(DAEMON_SOCK)

    async def ipc_handler(reader, writer):
        try:
            data = await reader.readline()
            cmd = json.loads(data.decode())
            cmd_type = cmd.get("type", "")
            resp = {"ok": False, "error": "unknown command"}
            if cmd_type == "route":
                from friday.router.provider_registry import ProviderRegistry

                providers = [p.name for p in ProviderRegistry().get_online_providers()]
                resp = {"ok": True, "providers": providers}
            elif cmd_type == "status":
                resp = {"ok": True, "version": __version__, "agents": len(o.agent_router._agents)}
            writer.write((json.dumps(resp) + "\n").encode())
            await writer.drain()
        except Exception as e:
            logger.debug("IPC handler error: %s", e)
        finally:
            writer.close()

    await ipc_server.start(ipc_handler)

    stop = asyncio.Event()

    def _shutdown():
        logger.info("Shutdown signal received")
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown)

    await stop.wait()
    await ipc_server.stop()
    await o.persistence.save_all()
    await o.persistence.stop()
    logger.info("FRIDAY daemon stopped")


async def repl():
    logger.info("FRIDAY v%s starting...", __version__)
    from friday.interfaces.cli.app import FridayREPL

    repl_app = FridayREPL()
    if "--voice" in sys.argv or "-v" in sys.argv:
        repl_app.voice_mode = True
    await repl_app.run()


def gui():
    logger.info("FRIDAY v%s desktop UI starting...", __version__)
    from friday.interfaces.desktop.app import run_gui

    run_gui()


async def main():
    if "--gui" in sys.argv:
        gui()
    elif "--daemon" in sys.argv or "-d" in sys.argv:
        await daemon()
    elif "--tray" in sys.argv:
        await tray()
    elif "--welcome" in sys.argv:
        await welcome()
    else:
        await repl()


async def tray():
    logger.info("FRIDAY v%s desktop tray starting...", __version__)
    from friday.interfaces.desktop.tray import FridayTray

    ft = FridayTray()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, ft.run)


async def welcome():
    from pathlib import Path

    from friday.memory.user_profile import UserProfile

    profile = UserProfile()
    p_path = Path("data/user_profile.json")
    if p_path.exists():
        profile.load(str(p_path))
    p = profile.get_profile()
    name = p.get("name", "Architect")
    title = p.get("title", "sir")
    msg = f"Welcome {title} {name}"
    inner = 39
    pad = inner - len(msg) - 2
    print()
    print("  " + "╔" + "═" * inner + "╗")
    print("  " + "║" + " " + msg + " " * pad + " ║")
    print("  " + "║" + "   FRIDAY AI OS is ready" + " " * (inner - 24) + "║")
    print("  " + "╚" + "═" * inner + "╝")
    print()
    print("  Type 'friday' to enter the interface")
    print()


if __name__ == "__main__":
    asyncio.run(main())
