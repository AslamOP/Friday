from __future__ import annotations
import asyncio
import logging
import shutil
from datetime import datetime

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from friday import __version__
from friday.core.orchestrator import Orchestrator

logger = logging.getLogger("friday.cli")

_BANNER = """
  _____ _____ ___   _   _ _____
 |  ___|  ___/ _ \\ | \\ | |  __\\
 | |__ | |_ | | | ||  \\| | |  |
 |  __||  _|| |_| || . ` | |  |
 | |___| |   \\___/ | |\\  | |__| |
 |____/|_|        |_| \\_|_____/
"""

class FridayREPL:
    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator
        self.console = Console()
        self._running = True

    async def run(self):
        self.console.clear()
        self.console.print(f"[bold cyan]{_BANNER}[/bold cyan]")
        self.console.print(f"[dim]FRIDAY v{__version__} — JARVIS-class AI Operating System[/dim]\n")

        while self._running:
            try:
                raw = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("[bold cyan]┌─[/bold cyan] [bold white](friday)[/bold white]\n[bold cyan]└─[/bold cyan] ").strip()
                )
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[yellow]Shutting down...[/yellow]")
                break

            if not raw:
                continue

            if raw.lower() in ("exit", "quit", ":q"):
                self.console.print("[yellow]Goodbye, sir.[/yellow]")
                break

            if raw.lower() == "/help":
                self._show_help()
                continue

            if raw.lower() == "/clear":
                self.console.clear()
                continue

            if raw.lower() == "/agents":
                self._show_agents()
                continue

            if raw.lower().startswith("/learn"):
                lessons = self.orchestrator.learning.learn()
                if lessons:
                    for l in lessons:
                        self.console.print(f"[green]• {l}[/green]")
                else:
                    self.console.print("[dim]No new lessons learned.[/dim]")
                continue

            if raw.lower().startswith("/feedback"):
                parts = raw.split()
                if len(parts) == 2 and parts[1].isdigit():
                    score = int(parts[1])
                    self.orchestrator.learning.feedback(score)
                    self.console.print(f"[green]Feedback recorded: {score}/5[/green]")
                else:
                    self.console.print("[yellow]Usage: /feedback <1-5>[/yellow]")
                continue

            if raw.lower() == "/history":
                history = self.orchestrator.memory.get_history(10)
                if not history:
                    self.console.print("[dim]No conversation history.[/dim]")
                else:
                    for h in history:
                        self.console.print(f"[dim]{h['timestamp'][:19]}[/dim]")
                        self.console.print(f"  [bold]You:[/bold] {h['user'][:120]}")
                        self.console.print(f"  [bold cyan]FRIDAY:[/bold cyan] {h['assistant'][:120]}")
                        self.console.print("")
                continue

            if raw.lower() == "/status":
                self._show_status()
                continue

            self.console.print("[dim]Processing...[/dim]")
            try:
                response = await self.orchestrator.process(raw)
                self.console.print(Panel(
                    Markdown(response),
                    border_style="cyan",
                    title="FRIDAY",
                    title_align="left",
                ))
            except Exception as e:
                logger.exception("Process error")
                self.console.print(f"[red]Error: {e}[/red]")

    def _show_help(self):
        help_text = f"""[bold cyan]FRIDAY v{__version__}[/bold cyan]

[bold cyan]💬 Chat[/bold cyan]
  <ask anything>     Natural conversation with FRIDAY
  exit / quit        Shutdown

[bold cyan]🔍 Commands[/bold cyan]
  /agents            List all agents
  /status            System state
  /history           Recent conversation
  /learn             Self-reflect & extract lessons
  /feedback <1-5>    Rate last response
  /clear             Clear screen
  /help              This help

[bold cyan]🔌 Presets[/bold cyan]
  friday --preset research   Deep research mode
  friday --preset code        Code assistant mode"""

        self.console.print(Panel(help_text, border_style="cyan"))

    def _show_agents(self):
        table = Table(box=box.SIMPLE, border_style="cyan")
        table.add_column("Agent", style="cyan")
        table.add_column("Description", style="white")
        agents = [
            ("chat", "General conversation with tools"),
            ("research", "Deep research with web search"),
            ("code", "Software engineering"),
            ("study", "Study mentor"),
            ("planner", "Project planning"),
            ("gaming", "Gaming strategies"),
        ]
        for name, desc in agents:
            table.add_row(name, desc)
        self.console.print(table)

    def _show_status(self):
        agents = ["chat", "research", "code", "study", "planner", "gaming"]
        history = self.orchestrator.memory.get_history(1)
        last_active = history[0]["timestamp"][:19] if history else "Never"

        table = Table(box=box.SIMPLE, border_style="cyan")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_row("Version", __version__)
        table.add_row("Agents", str(len(agents)))
        table.add_row("Interactions", str(len(self.orchestrator.memory.get_all())))
        table.add_row("Lessons", str(len(self.orchestrator.learning.get_lessons())))
        table.add_row("Last Active", last_active)
        self.console.print(table)
