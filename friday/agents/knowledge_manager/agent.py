from ..base import BaseAgent, Context, Result, Task
from . import prompts
from friday.router.provider_registry import ProviderRegistry

KG = None
VS = None
UP = None
PM = None
CS = None
IDX = None


def _lazy_imports():
    global KG, VS, UP, PM, CS, IDX
    if KG is None:
        from friday.memory.knowledge_graph import KnowledgeGraph
        KG = KnowledgeGraph()
    if VS is None:
        from friday.memory.vector_store import VectorStore
        VS = VectorStore()
    if UP is None:
        from friday.memory.user_profile import UserProfile
        UP = UserProfile()
    if PM is None:
        from friday.memory.project_memory import ProjectMemory
        PM = ProjectMemory()
    if CS is None:
        from friday.memory.conversation_store import ConversationStore
        CS = ConversationStore()


class KnowledgeManagerAgent(BaseAgent):
    name = "knowledge_manager"

    def __init__(self):
        super().__init__(model_preference="openai/gpt-4o-mini")
        self._router = ProviderRegistry()

    async def handle(self, task, context):
        _lazy_imports()
        text = context.user_input.lower().strip()
        parts = text.split(None, 1)
        cmd = parts[0] if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        # --- VIEW commands ---
        if cmd in ("show", "list", "view"):
            if "profile" in text:
                return Result(success=True, output=self._fmt_dict("USER PROFILE", UP.get_profile()), agent=self.name)
            if "project" in text:
                return Result(success=True, output=self._fmt_projects(), agent=self.name)
            if "conversation" in text or "chat" in text:
                return await self._show_conversations(args)
            if "study" in text:
                return Result(success=True, output=self._fmt_study(), agent=self.name)
            if "all" in text or "memory" in text:
                return await self._show_all(text)
            if "search" in text or "find" in text:
                return await self._search_memory(args)
            # default: show KG + VS summary
            return await self._show_all(text)

        # --- SEARCH ---
        if cmd in ("search", "find"):
            return await self._search_memory(args)

        # --- DELETE ---
        if cmd in ("delete", "remove", "forget"):
            kg_count = len(KG._graph)
            if "all" in text or "everything" in text or "clear" in text:
                KG._graph.clear()
                KG._relations.clear()
                VS._collection.delete(where={}) if hasattr(VS, '_collection') else None
                return Result(success=True, output="All memory cleared.", agent=self.name)
            if args:
                deleted = 0
                for eid in list(KG._graph.keys()):
                    if args.lower() in eid.lower():
                        KG._graph.pop(eid, None)
                        deleted += 1
                return Result(success=True, output=f"Deleted {deleted} matching entries.", agent=self.name)
            return Result(success=True, output="Specify what to forget, e.g. 'delete <topic>'", agent=self.name)

        # --- UPDATE ---
        if cmd in ("update", "set"):
            if "profile" in text:
                # parse key=value pairs
                import re
                pairs = re.findall(r'(\w+)\s*=\s*(.+)', args)
                if pairs:
                    for k, v in pairs:
                        UP.update_profile({k.strip(): v.strip()})
                    return Result(success=True, output="Profile updated.", agent=self.name)
                return Result(success=True, output="Usage: update profile name=John title=dr", agent=self.name)
            return Result(success=True, output="Only profile updates are supported. Try 'update profile name=value'", agent=self.name)

        # fallback — route to LLM with memory context
        return await self._llm_respond(context.user_input)

    async def _show_all(self, text):
        kg = KG._graph
        vs_count = 0
        if hasattr(VS, '_collection') and hasattr(VS._collection, 'count'):
            try:
                vs_count = VS._collection.count()
            except Exception:
                vs_count = len(VS._ids) if hasattr(VS, '_ids') else 0
        profile = UP.get_profile()
        projects = PM.list_projects()
        lines = [
            f"KNOWLEDGE GRAPH: {len(kg)} entities, {len(KG._relations)} relations",
            f"VECTOR STORE: {vs_count} documents",
            f"PROJECTS: {len(projects)}",
            f"PROFILE: {profile.get('name', 'N/A')} ({profile.get('title', '')})",
        ]
        if kg:
            lines.append("\nEntities:")
            for eid, edata in list(kg.items())[:10]:
                lines.append(f"  • {eid} ({edata.get('type', '?')})")
            if len(kg) > 10:
                lines.append(f"  ... and {len(kg) - 10} more")
        return Result(success=True, output="\n".join(lines), agent=self.name)

    async def _show_conversations(self, args):
        try:
            history = await CS.get_history(limit=15)
            if not history:
                return Result(success=True, output="No conversation history.", agent=self.name)
            lines = ["RECENT CONVERSATIONS:"]
            for m in history[-15:]:
                role = m.get("role", "?")
                content = m.get("content", "")[:80]
                lines.append(f"  [{role}] {content}")
            return Result(success=True, output="\n".join(lines), agent=self.name)
        except Exception as e:
            return Result(success=True, output=f"Conversations unavailable: {e}", agent=self.name)

    async def _search_memory(self, query):
        if not query:
            return Result(success=True, output="Specify a search query.", agent=self.name)
        results = []
        kg_matches = KG.search(query)
        if kg_matches:
            for e in kg_matches[:5]:
                results.append(f"[KG] {e['id']} ({e.get('type', '?')})")
        try:
            vs_matches = VS.search(query, top_k=5)
            if vs_matches:
                for r in vs_matches[:5]:
                    text_snip = r.get("text", "")[:100]
                    results.append(f"[VS] ({r.get('score', 0):.2f}) {text_snip}")
        except Exception:
            pass
        if not results:
            return Result(success=True, output=f"No memories found for '{query}'", agent=self.name)
        return Result(success=True, output="\n".join(results), agent=self.name)

    async def _llm_respond(self, text):
        kg = KG._graph
        profile = UP.get_profile()
        ctx_parts = [f"KG entities: {len(kg)}"]
        if profile:
            ctx_parts.append(f"Profile: {profile.get('name', '')} - {profile.get('title', '')}")
        ctx = " | ".join(ctx_parts)
        prompt = f"""{text}

Current memory state: {ctx}

Help the user understand or modify FRIDAY's memory. Stay local — no internet."""
        r = await self._router.route("knowledge", prompt, prompts.SYSTEM_PROMPT)
        return Result(success=True, output=r.get("content", ""), agent=self.name)

    def _fmt_dict(self, title, d):
        lines = [f"{title}:"]
        for k, v in d.items():
            if isinstance(v, dict):
                lines.append(f"  {k}:")
                for sk, sv in v.items():
                    lines.append(f"    {sk}: {sv}")
            elif isinstance(v, list):
                lines.append(f"  {k}: {', '.join(str(x) for x in v) if v else '(empty)'}")
            else:
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    def _fmt_projects(self):
        projects = PM.list_projects()
        if not projects:
            return "No projects."
        lines = ["PROJECTS:"]
        for p in projects:
            name = p.get("name", "?")
            desc = p.get("description", "")[:60]
            lines.append(f"  • {name} — {desc}")
        return "\n".join(lines)

    def _fmt_study(self):
        from pathlib import Path
        import json
        cfg_path = Path("~/.config/friday/study_agent.json").expanduser()
        if not cfg_path.exists():
            return "Study config: not set up yet."
        cfg = json.loads(cfg_path.read_text())
        folder = cfg.get("folder", "not set")
        online = "enabled" if cfg.get("online", False) else "disabled"
        return f"STUDY CONFIG:\n  Folder: {folder}\n  Online: {online}"

    async def can_handle(self, intent):
        return 0.9 if intent == "knowledge" else 0.15
