from __future__ import annotations

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from friday import Friday, __version__
from friday._registry import Catalog

console = Console()


@click.command(help="Interactive chat")
@click.option("-x", "--expert", default="orchestrator", help="Expert agent")
@click.option("-m", "--model", default="", help="Model name")
def chat(expert: str, model: str):
    f = Friday()
    console.print(Panel(f"[cyan]FRIDAY v{__version__}[/cyan]\nExpert: [bold]{expert}[/bold]\n/help for commands, /exit to quit.", border_style="cyan"))
    while True:
        try:
            q = click.prompt("[cyan]You[/cyan]", prompt_suffix="> ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Goodbye, sir.[/yellow]")
            break
        if not q:
            continue
        if q.lower() in ("/exit", "/quit", ":q"):
            console.print("[yellow]Goodbye, sir.[/yellow]")
            break
        if q.lower() == "/help":
            console.print(Panel(
                "/help   Show this\n/expert List experts\n/tools  List tools\n/model  Show model\n/engine Show engines\n/clear  Clear\n/exit   Quit",
                border_style="cyan",
            ))
            continue
        if q.lower() == "/clear":
            console.clear()
            continue
        if q.lower() == "/expert":
            for n in Catalog.names("expert"):
                console.print(f"  [cyan]{n}[/cyan]")
            continue
        if q.lower() == "/tools":
            for n in Catalog.names("proc"):
                console.print(f"  [cyan]{n}[/cyan]")
            continue
        if q.lower() == "/model":
            console.print(f"  [cyan]{f._model or 'auto'}[/cyan]")
            continue
        if q.lower() == "/engine":
            for name, models in f.engines().items():
                console.print(f"  [cyan]{name}[/cyan]: {', '.join(models[:3])}")
            continue
        if q.startswith("/"):
            console.print(f"[yellow]unknown: {q}[/yellow]")
            continue
        with console.status("Thinking..."):
            r = f.ask(q, expert=expert, model=model or None)
        console.print(Panel(Markdown(r), border_style="cyan", title=f"FRIDAY ({expert})"))
