import asyncio
import json
import re
from pathlib import Path

from friday.router.provider_registry import ProviderRegistry

from ..base import BaseAgent, Context, Result, Task
from . import prompts

CONFIG_PATH = Path("~/.config/friday/study_agent.json").expanduser()

WELCOME_MSG = """📚 **FRIDAY Study Agent**

I'm your university/college study mentor. I teach from YOUR notes — no assumptions, no guessing.

**To get started, tell me your study folder:**
`set folder ~/Documents/MyNotes`

I'll read your files (.md, .txt, code files) and help you:
- Explain concepts from your notes
- Create study guides & exam prep
- Identify problems or gaps in your notes
- Generate practice questions

Your notes stay yours — I don't search online without your permission."""

SET_FOLDER_HELP = "Please specify a valid folder path, e.g.:\n`set folder ~/Documents/MyNotes`"

EMPTY_FOLDER_MSG = """📂 **Empty Study Folder**

I found no readable notes in your study folder.

To proceed:
1. Add .md or .txt files to your folder
2. Type `enable online` to let me search the internet"""

ONLINE_ENABLED_MSG = "✅ Online search enabled. I'll supplement your notes when needed. Type `disable online` to turn off."

ONLINE_DISABLED_MSG = "🔒 Online search disabled. I'll use only your notes. Type `enable online` to re-enable."

SAVED_MSG = "\n\n📁 **Saved to:** `{}`"


class StudyAgent(BaseAgent):
    name = "study"

    def __init__(self):
        super().__init__()
        self._router = ProviderRegistry()
        self._cfg = self._load_config()

    def _load_config(self):
        try:
            if CONFIG_PATH.exists():
                return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
        return {}

    async def _save_config(self):
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: (
                CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True),
                CONFIG_PATH.write_text(json.dumps(self._cfg)),
            ))
        except Exception:
            pass

    async def handle(self, task: Task, context: Context) -> Result:
        text = context.user_input
        low = text.lower()

        if any(kw in low for kw in ("set folder", "use folder", "notes folder")):
            return await self._set_folder(text)

        if "enable online" in low:
            self._cfg["online"] = True
            await self._save_config()
            return Result(success=True, output=ONLINE_ENABLED_MSG, agent=self.name)

        if "disable online" in low:
            self._cfg["online"] = False
            await self._save_config()
            return Result(success=True, output=ONLINE_DISABLED_MSG, agent=self.name)

        folder = self._cfg.get("folder", "")
        if not folder:
            return Result(success=True, output=WELCOME_MSG, agent=self.name)

        notes = await self._load_notes(folder)
        online = self._cfg.get("online", False)

        if not notes:
            return await self._no_notes(text, online)

        want_save = any(kw in low for kw in ("save", "create guide", "make notes", "generate", "study guide", "cheat sheet"))

        prompt = prompts.PROMPT.format(folder=folder, notes=notes, input=text)
        r = await self._router.route("study", prompt, prompts.SYSTEM_PROMPT)
        output = r.get("content", "")

        if want_save and output:
            p = await self._save_output(text, output)
            if p:
                output += SAVED_MSG.format(p)

        return Result(success=True, output=output, agent=self.name)

    async def _load_notes(self, folder: str) -> str:
        path = Path(folder).expanduser().resolve()
        if not path.is_dir():
            return ""

        exts = {".md", ".txt", ".py", ".java", ".cpp", ".c", ".h", ".js", ".ts",
                ".html", ".css", ".json", ".yaml", ".yml", ".org", ".rst", ".tex",
                ".csv", ".xml", ".sql", ".sh", ".go", ".rs", ".rb", ".php"}
        sections = []
        loop = asyncio.get_running_loop()

        for f in sorted(path.rglob("*")):
            if f.suffix in exts and f.is_file():
                try:
                    content = await loop.run_in_executor(None, lambda: f.read_text(errors="replace"))
                    if len(content) > 12000:
                        content = content[:12000] + "\n... [truncated]"
                    rel = f.relative_to(path)
                    sections.append(f"## File: {rel}\n{content}")
                except Exception:
                    pass

        return "\n\n".join(sections) if sections else ""

    async def _save_output(self, user_input: str, content: str) -> str | None:
        folder = Path(self._cfg.get("folder", "")).expanduser().resolve()
        out_dir = folder / ".friday_study"
        out_dir.mkdir(parents=True, exist_ok=True)
        loop = asyncio.get_running_loop()

        topic = re.sub(r'[^a-zA-Z0-9]+', '_', user_input[:50]).strip('_')
        if not topic:
            topic = "study_material"

        fpath = out_dir / f"{topic}.md"
        n = 1
        while fpath.exists():
            fpath = out_dir / f"{topic}_{n}.md"
            n += 1

        try:
            await loop.run_in_executor(None, lambda: fpath.write_text(content))
            return str(fpath)
        except Exception:
            return None

    async def _set_folder(self, text: str) -> Result:
        m = re.search(r'(?:set folder|use folder|notes folder)\s+["\']?(.+?)["\']?$', text, re.IGNORECASE)
        if not m:
            return Result(success=True, output=SET_FOLDER_HELP, agent=self.name)

        folder = m.group(1).strip()
        path = Path(folder).expanduser().resolve()

        if not path.exists():
            return Result(success=True, output=f"❌ Folder not found: `{path}`\nPlease check the path.", agent=self.name)
        if not path.is_dir():
            return Result(success=True, output=f"❌ Not a directory: `{path}`\nPlease specify a folder.", agent=self.name)

        files = list(path.rglob("*"))
        self._cfg["folder"] = str(path)
        await self._save_config()

        msg = f"📚 **Study folder set to:** `{path}`"
        readable = sum(1 for f in files if f.suffix in {
            ".md", ".txt", ".py", ".java", ".cpp", ".c", ".h", ".js", ".ts",
            ".html", ".css", ".json", ".yaml", ".yml", ".org", ".rst", ".tex",
        } and f.is_file())

        if readable == 0:
            msg += "\n\n⚠️ No readable study files found. Add .md or .txt files and I'll help you study them."
        else:
            msg += f"\n\n📄 Found {readable} readable file{'s' if readable != 1 else ''}. Ask me to explain, quiz you, or create study guides!"

        return Result(success=True, output=msg, agent=self.name)

    async def _no_notes(self, text: str, online: bool) -> Result:
        if online:
            r = await self._router.route("study", prompts.NO_NOTES_PROMPT.format(input=text), prompts.SYSTEM_PROMPT)
            output = r.get("content", "")
            output += "\n\n---\n*ℹ️ Responded with online search enabled.*"
            return Result(success=True, output=output, agent=self.name)
        return Result(success=True, output=EMPTY_FOLDER_MSG, agent=self.name)

    async def can_handle(self, intent: str) -> float:
        return 0.95 if intent == "study" else 0.1
