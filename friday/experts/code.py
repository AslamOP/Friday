from friday._agent import Agent
from friday._registry import Catalog

_CODE = """You are FRIDAY's software engineering division.
You write, debug, and understand code. You have shell and file access.
Write idiomatic, correct code. Address the user as "sir"."""


@Catalog.tag("expert", "code")
def code_expert(engine, model, *, procs=None, **kw):
    return Agent(engine, model, procs=procs, prompt=_CODE, temp=kw.pop("temp", 0.2), tokens=kw.pop("tokens", 4096), **kw)
