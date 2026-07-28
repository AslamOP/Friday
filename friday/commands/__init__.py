from __future__ import annotations

import click

import friday
from friday.commands.ask import ask
from friday.commands.chat import chat


@click.group(help="FRIDAY — Personal AI Agent System", invoke_without_command=True)
@click.version_option(version=friday.__version__, prog_name="friday")
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat)


cli.add_command(ask, "ask")
cli.add_command(chat, "chat")


def main():
    cli()
