from __future__ import annotations
import asyncio
import logging
import sys

from friday import __version__
from friday.agents.chat import ChatAgent
from friday.agents.research import ResearchAgent
from friday.agents.code import CodeAgent
from friday.agents.study import StudyAgent
from friday.agents.planner import PlannerAgent
from friday.agents.gaming import GamingAgent
from friday.core.orchestrator import Orchestrator
from friday.router.provider_registry import ProviderRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)


def _build_orchestrator() -> Orchestrator:
    providers = ProviderRegistry()
    orch = Orchestrator()

    def _llm(messages, tools=None):
        return providers.complete(messages, tools=tools)

    orch.register_agent(ChatAgent(_llm))
    orch.register_agent(ResearchAgent(_llm))
    orch.register_agent(CodeAgent(_llm))
    orch.register_agent(StudyAgent(_llm))
    orch.register_agent(PlannerAgent(_llm))
    orch.register_agent(GamingAgent(_llm))

    orch.router.route("research", lambda t: 0.9 if any(w in t.lower() for w in ["research", "search", "find", "look up", "what is", "who is", "latest", "news"]) else 0.0, "research")
    orch.router.route("code", lambda t: 0.9 if any(w in t.lower() for w in ["code", "program", "function", "debug", "implement", "write a", "python", "javascript", "typescript", "algorithm"]) else 0.0, "code")
    orch.router.route("study", lambda t: 0.9 if any(w in t.lower() for w in ["study", "learn", "explain", "teach", "understand", "concept", "what does", "how does"]) else 0.0, "study")
    orch.router.route("planner", lambda t: 0.9 if any(w in t.lower() for w in ["plan", "project", "roadmap", "timeline", "milestone", "schedule", "organize"]) else 0.0, "planner")
    orch.router.route("gaming", lambda t: 0.9 if any(w in t.lower() for w in ["game", "gaming", "play", "walkthrough", "strategy", "cheat", "achievement"]) else 0.0, "gaming")
    orch.router.set_default("chat")

    return orch


def _cli():
    from friday.interfaces.cli import FridayREPL
    orch = _build_orchestrator()
    repl = FridayREPL(orch)
    asyncio.run(repl.run())


def _gui():
    try:
        from friday.interfaces.desktop.app import run_gui
        orch = _build_orchestrator()
        run_gui(orch)
    except ImportError as e:
        logging.getLogger("friday").error("GUI deps not installed: pip install 'friday[gui]'")
        sys.exit(1)


def _entry():
    if "--gui" in sys.argv:
        _gui()
    else:
        _cli()


if __name__ == "__main__":
    _entry()
