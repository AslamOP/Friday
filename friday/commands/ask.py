from __future__ import annotations

import click
from rich.console import Console
from rich.markdown import Markdown

from friday import Friday

console = Console()


@click.command(help="Ask FRIDAY")
@click.argument("query", required=False)
@click.option("-x", "--expert", default="", help="Expert agent (chat, code, research, cad)")
@click.option("-m", "--model", default="", help="Model name")
def ask(query: str | None, expert: str, model: str):
    f = Friday()
    if not query:
        query = click.prompt("You")
    with console.status("Thinking..."):
        response = f.ask(query, expert=expert or None, model=model or None)
    console.print(Markdown(response))
