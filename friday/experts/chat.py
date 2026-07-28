from friday._agent import Agent
from friday._registry import Catalog

_CHAT = """You are FRIDAY, a JARVIS-class personal AI assistant.
You are concise and efficient. Address the user as "sir".
Use tools when they help answer the question."""


@Catalog.tag("expert", "chat")
def chat_expert(engine, model, *, procs=None, **kw):
    return Agent(engine, model, procs=procs, prompt=_CHAT, **kw)
