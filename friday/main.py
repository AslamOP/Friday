import asyncio
import logging
import signal
import sys

from friday.config import get_config
from friday import __version__

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("friday")


async def daemon():
    cfg = get_config()
    logger.info("FRIDAY v%s daemon starting...", __version__)
    from friday.core.orchestrator import get_orchestrator
    from friday.agents.mentor import MentorAgent
    from friday.agents.planner import PlannerAgent
    from friday.agents.software_engineer import SoftwareEngineerAgent
    from friday.agents.research_scientist import ResearchScientistAgent
    from friday.agents.automation_engineer import AutomationEngineerAgent
    from friday.agents.knowledge_manager import KnowledgeManagerAgent
    from friday.agents.study import StudyAgent
    from friday.agents.gaming_assistant import GamingAssistantAgent

    o = get_orchestrator()
    for ac in [MentorAgent, PlannerAgent, SoftwareEngineerAgent,
               ResearchScientistAgent, AutomationEngineerAgent,
               KnowledgeManagerAgent, StudyAgent, GamingAssistantAgent]:
        o.register_agent(ac())
    await o.initialize()
    logger.info("FRIDAY v%s daemon ready", __version__)

    stop = asyncio.Event()

    def _shutdown():
        logger.info("Shutdown signal received")
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown)

    await stop.wait()
    await o.persistence.save_all()
    await o.persistence.stop()
    logger.info("FRIDAY daemon stopped")


async def repl():
    cfg = get_config()
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
    from friday.memory.user_profile import UserProfile
    from pathlib import Path

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
