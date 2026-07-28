import asyncio
import logging
import shutil
from datetime import datetime

from rich import box
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from friday import __version__
from friday.agents.automation_engineer import AutomationEngineerAgent
from friday.agents.gaming_assistant import GamingAssistantAgent
from friday.agents.knowledge_manager import KnowledgeManagerAgent
from friday.agents.mentor import MentorAgent
from friday.agents.planner import PlannerAgent
from friday.agents.research_scientist import ResearchScientistAgent
from friday.agents.software_engineer import SoftwareEngineerAgent
from friday.agents.study import StudyAgent
from friday.core.orchestrator import get_orchestrator
from friday.interfaces.audio import SpeechToText, TextToSpeech
from friday.router.provider_registry import ProviderRegistry

logger = logging.getLogger("friday.cli")

_BANNER = """
  _____ _____ ___   _   _ _____
 |  ___|  ___/ _ \\ | \\ | |  __ \\
 | |__ | |_ | | | ||  \\| | |  | |
 |  __||  _|| |_| || . ` | |  | |
 | |___| |   \\___/ | |\\  | |__| |
 |____/|_|        |_| \\_|_____/
"""

_HELP = f"""[bold]FRIDAY v{__version__}[/bold]
  /help         This help          /agents    List agents
  /status       System state       /save      Force save
  /plugins      List plugins       /history   Session history
  /providers    Manage LLM providers  /voice   Toggle voice mode
  /speak        Read last response  /clear    Clear screen
  exit          Shutdown"""


class FridayREPL:
    def __init__(self):
        self.console = Console()
        self.orchestrator = get_orchestrator()
        self.router = ProviderRegistry()
        for a in [
            MentorAgent(), PlannerAgent(), SoftwareEngineerAgent(),
            ResearchScientistAgent(), AutomationEngineerAgent(),
            KnowledgeManagerAgent(), StudyAgent(), GamingAssistantAgent(),
        ]:
            self.orchestrator.register_agent(a)
        self.history: list[dict] = []
        self.voice_mode = False
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self._last_output = ""

    async def _agents(self):
        t = Table(show_header=True, box=box.SIMPLE)
        t.add_column("Agent", style="cyan")
        t.add_column("Model", style="yellow")
        for a in self.orchestrator.agent_router._agents:
            t.add_row(a.name, a.model_preference or "auto")
        self.console.print(t)

    async def _status(self):
        kg = self.orchestrator.context_engine._kg
        e = len(kg._graph) if hasattr(kg, "_graph") else 0
        r = len(kg._relations) if hasattr(kg, "_relations") else 0
        g = Table.grid(padding=1)
        g.add_column(style="cyan")
        g.add_column(style="white")
        g.add_row("Version", f"v{__version__}")
        g.add_row("Agents", str(len(self.orchestrator.agent_router._agents)))
        g.add_row("KG entities", str(e))
        g.add_row("KG relations", str(r))
        g.add_row("Auto-save", "every 60s")
        g.add_row("History", str(len(self.history)))
        self.console.print(Panel(g, title="Status", border_style="blue"))

    async def _history_cmd(self):
        if not self.history:
            self.console.print("[dim]No history[/dim]")
            return
        for i, h in enumerate(self.history[-20:], 1):
            self.console.print(f"[dim]{i}.[/dim] [cyan]You:[/cyan] {h['input'][:80]}")
            agent = h.get("agent", "?")
            model = h.get("model", "")
            badge = f"[bold green]{agent}[/bold green]"
            if model:
                badge += f" [dim]({model})[/dim]"
            self.console.print(f"    {badge}")
            self.console.print()

    async def _providers(self):
        t = Table(show_header=True, box=box.SIMPLE)
        t.add_column("Provider", style="cyan")
        t.add_column("Type", style="yellow")
        t.add_column("Status", style="magenta")
        t.add_column("Models")
        for p in self.router.list_providers():
            status = p.status
            key_set = "✓" if p.api_key else "✗"
            label = f"{status} key:{key_set}" if p.type == "cloud" else status
            model_list = ", ".join(p.models[:3])
            if len(p.models) > 3:
                model_list += f" [dim]+{len(p.models)-3}[/dim]"
            t.add_row(p.name, p.type, label, model_list)
        self.console.print(Panel(t, title="LLM Providers"))
        self.console.print("[dim]/provider add <name> <local|cloud> [endpoint][/dim]")
        self.console.print("[dim]/provider key <name> <api_key>          (fetches models)[/dim]")
        self.console.print("[dim]/provider refresh <name>                (re-check + fetch models)[/dim]")
        self.console.print("[dim]/provider remove <name>[/dim]")

    async def _banner(self):
        self.console.clear()
        tw = shutil.get_terminal_size().columns
        self.console.print(f"[bold cyan]{_BANNER}[/bold cyan]")
        self.console.print(f"[dim]v{__version__} — {datetime.now().strftime('%a %b %d %H:%M')}[/dim]".center(tw))
        self.console.print(f"[dim]{len(self.orchestrator.agent_router._agents)} agents | /help[/dim]".center(tw) + "\n")

    async def _stream_response(self, task_type: str, prompt: str, system_prompt: str, label: str) -> tuple[str, str]:
        full = ""
        model = ""
        header = Text(f" {label} ", style="bold green")
        with Live(Panel(Markdown(""), title=header), refresh_per_second=20, console=self.console) as live:
            async for chunk in self.router.route_stream(task_type, prompt, system_prompt):
                token = chunk.get("token", "")
                if token:
                    full += token
                    live.update(Panel(Markdown(full), title=header))
                m = chunk.get("model", "")
                if m and m != "none":
                    model = m
                    header = Text(f" {label} ({model}) ", style="bold green")
                    live.update(Panel(Markdown(full), title=header))
        return full, model

    async def _read_multiline(self) -> str:
        lines = []
        self.console.print("[dim](multi-line — press Ctrl+D on empty line to send)[/dim]")
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, lambda: input("... "))
                if not line and lines:
                    break
                lines.append(line)
            except EOFError:
                break
        return "\n".join(lines)

    async def _listen_input(self) -> str:
        if self.voice_mode:
            self.console.print("[dim]🎤 Listening...[/dim]")
            text = await self.stt.listen(timeout=8.0, phrase_time=5.0)
            if text:
                self.console.print(f"[dim]You: {text}[/dim]")
            return text.strip()
        return (await asyncio.get_event_loop().run_in_executor(
            None, lambda: input("[bold yellow]>>> [/bold yellow]")
        )).strip()

    async def run(self):
        await self.orchestrator.initialize()
        await self._banner()
        while True:
            try:
                raw = await self._listen_input()
                if not raw:
                    continue

                if raw.lower() in ("exit", "quit", ":q"):
                    await self.orchestrator.persistence.save_all()
                    self.console.print("[dim]Saved. Goodbye.[/dim]")
                    break

                if raw.lower() in ("clear", "cls"):
                    await self._banner()
                    continue

                if raw.lower() == "/help":
                    self.console.print(_HELP)
                    continue

                if raw.lower() == "/agents":
                    await self._agents()
                    continue

                if raw.lower() == "/status":
                    await self._status()
                    continue

                if raw.lower() == "/save":
                    await self.orchestrator.persistence.save_all()
                    self.console.print("[dim]Saved.[/dim]")
                    continue

                if raw.lower() == "/history":
                    await self._history_cmd()
                    continue

                if raw.lower() == "/voice":
                    self.voice_mode = not self.voice_mode
                    status = "ON" if self.voice_mode else "OFF"
                    self.console.print(f"[dim]Voice mode {status}[/dim]")
                    if self.voice_mode and not self.tts.available:
                        self.console.print("[yellow]Warning: no TTS engine available[/yellow]")
                    continue

                if raw.lower() == "/speak":
                    if self._last_output:
                        await self.tts.speak(self._last_output)
                    else:
                        self.console.print("[dim]Nothing to speak[/dim]")
                    continue

                if raw.lower() == "/plugins":
                    pl = self.orchestrator.plugin_manager.list_plugins()
                    if pl:
                        t = Table(show_header=True, box=box.SIMPLE)
                        t.add_column("Plugin", style="cyan")
                        t.add_column("Version", style="yellow")
                        t.add_column("Description")
                        for p in pl:
                            t.add_row(p["name"], p["version"], p["description"])
                        self.console.print(t)
                    else:
                        self.console.print("[dim]No plugins loaded[/dim]")
                    continue

                if raw.lower() == "/providers":
                    await self._providers()
                    continue

                if raw.lower().startswith("/provider add"):
                    parts = raw.split()
                    if len(parts) >= 3:
                        name = parts[2]
                        ptype = parts[3] if len(parts) > 3 else "cloud"
                        endpoint = parts[4] if len(parts) > 4 else ""
                        await self.router.add_provider(name, ptype, endpoint=endpoint)
                        if endpoint:
                            status = await self.router.check_status(name)
                            self.console.print(f"[green]Added {name} ({ptype}) — status: {status}[/green]")
                        else:
                            self.console.print(f"[green]Added {name} ({ptype}). Set its API key: /provider key {name} <key>[/green]")
                    else:
                        self.console.print("[yellow]Usage: /provider add <name> <local|cloud> [endpoint][/yellow]")
                    continue

                if raw.lower().startswith("/provider remove"):
                    parts = raw.split()
                    if len(parts) >= 3 and await self.router.remove_provider(parts[2]):
                        self.console.print(f"[green]Removed {parts[2]}[/green]")
                    else:
                        self.console.print("[yellow]Cannot remove or not found[/yellow]")
                    continue

                if raw.lower().startswith("/provider key"):
                    parts = raw.split(maxsplit=2)
                    if len(parts) >= 3:
                        name, key = parts[1], parts[2]
                        await self.router.set_key(name, key)
                        status = await self.router.check_status(name)
                        models = await self.router.fetch_models(name)
                        msg = f"[green]{name} key set — status: {status}[/green]"
                        if models:
                            msg += f" [dim]({len(models)} models fetched)[/dim]"
                        self.console.print(msg)
                    else:
                        self.console.print("[yellow]Usage: /provider key <name> <api_key>[/yellow]")
                    continue

                if raw.lower().startswith("/provider refresh"):
                    parts = raw.split()
                    if len(parts) >= 3:
                        name = parts[2]
                        if await self.router.refresh(name):
                            p = self.router.get_provider(name)
                            self.console.print(f"[green]{name} refreshed — status: {p.status}, {len(p.models)} models[/green]")
                        else:
                            self.console.print(f"[yellow]Provider {name} not found[/yellow]")
                    else:
                        self.console.print("[yellow]Usage: /provider refresh <name>[/yellow]")
                    continue

                # Multi-line input detection
                if raw.startswith("```") or raw.startswith("'''") or raw.endswith(":") or raw.endswith("{"):
                    rest = await self._read_multiline()
                    raw = raw + "\n" + rest

                # Process through orchestrator (routes to agent, calls handle(), streams result)
                self.console.print("[dim]Processing...[/dim]")
                result = await self.orchestrator.process(raw)
                output = result.output
                self._last_output = output
                self.console.print(Markdown(output))
                self.history.append({
                    "input": raw,
                    "output": output,
                    "agent": result.agent,
                })

                # Speak response in voice mode
                if self.voice_mode and self.tts.available:
                    await self.tts.speak(output)

            except (EOFError, KeyboardInterrupt):
                await self.orchestrator.persistence.save_all()
                self.console.print("\n[dim]Saved. Goodbye.[/dim]")
                break
            except Exception as e:
                self.console.print(f"[red]{e}[/red]")
