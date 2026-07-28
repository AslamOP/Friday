from friday._agent import Agent
from friday._registry import Catalog

_CAD = """You are FRIDAY's CAD engineering division.
You are an expert in SolidWorks automation.
You open files, inspect mass properties, modify parameters, export STLs, list features.
Address the user as "sir"."""


@Catalog.tag("expert", "cad")
def cad_expert(engine, model, *, procs=None, **kw):
    return Agent(engine, model, procs=procs, prompt=_CAD, temp=kw.pop("temp", 0.2), tokens=kw.pop("tokens", 4096), **kw)
