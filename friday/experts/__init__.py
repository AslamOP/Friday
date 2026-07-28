import friday.experts.cad  # noqa: F401
import friday.experts.chat  # noqa: F401
import friday.experts.code  # noqa: F401
import friday.experts.research  # noqa: F401
from friday._agent import Agent
from friday._engine import Engine
from friday._registry import Catalog


def build(name: str, engine: Engine, model: str, procs: list | None = None, **kw) -> Agent:
    cls = Catalog.fetch("expert", name)
    return cls(engine, model, procs=procs, **kw)
