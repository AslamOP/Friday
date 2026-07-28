from friday._agent import Agent
from friday._registry import Catalog

_RESEARCH = """You are FRIDAY's research division.
You search the web for current information and synthesize findings.
Provide sources. Be thorough. Address the user as "sir"."""


@Catalog.tag("expert", "research")
def research_expert(engine, model, *, procs=None, **kw):
    return Agent(engine, model, procs=procs, prompt=_RESEARCH, rounds=kw.pop("rounds", 15), temp=kw.pop("temp", 0.3), tokens=kw.pop("tokens", 4096), **kw)
