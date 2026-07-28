import re
from pathlib import Path

from friday.router.provider_registry import ProviderRegistry
from friday.tools.file_ops import FileOps
from friday.tools.web_search import WebSearchTool

from ..base import BaseAgent, Result
from . import prompts


class ResearchScientistAgent(BaseAgent):
    name = "research_scientist"

    def __init__(self):
        super().__init__(model_preference="anthropic/claude-3.5-sonnet")
        self._router = ProviderRegistry()
        self._web = WebSearchTool()
        self._fs = FileOps()
        self._project_dir = Path.cwd() / "research"

    async def handle(self, task, context):
        text = context.user_input

        # detect project name for folder-based saving
        proj_match = re.search(r'(?:project|for)\s+["\']?(.+?)["\']?(?:\s|$)', text, re.IGNORECASE)
        proj_name = None
        if proj_match:
            proj_name = proj_match.group(1).strip().replace(" ", "_")
            self._project_dir = Path.cwd() / "research" / proj_name
            self._project_dir.mkdir(parents=True, exist_ok=True)

        # search the web
        results = await self._web.search(text)
        ctx = ""
        sources = []

        if results.results:
            ctx = "## Web Search Results\n" + "\n".join(
                f"- [{r.title}]({r.url})\n  {r.snippet}" for r in results.results[:5]
            )
            sources = results.results[:3]
            # scrape first result for deeper context
            if sources:
                scraped = await self._web.scrape(sources[0].url)
                if scraped and not scraped.startswith("[scrape"):
                    ctx += f"\n## Detailed Page\n{scraped[:2000]}"

        prompt = prompts.PROMPT.format(input=text)
        if ctx:
            prompt += f"\n\n{ctx}"

        r = await self._router.route("research", prompt, prompts.SYSTEM_PROMPT)
        output = r.get("content", "")

        # append sources
        if sources:
            output += "\n\n---\n## Sources\n" + "\n".join(
                f"- [{s.title}]({s.url})" for s in sources
            )

        # save to project folder if project name detected
        if proj_name:
            safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', text[:40]).strip('_') or "research"
            fpath = self._project_dir / f"{safe_name}.md"
            n = 1
            while fpath.exists():
                fpath = self._project_dir / f"{safe_name}_{n}.md"
                n += 1
            await self._fs.write(str(fpath), f"# Research: {text[:80]}\n\n{output}")
            output += f"\n\n📁 **Saved to:** `{fpath}`"

        return Result(success=True, output=output, agent=self.name)

    async def can_handle(self, intent):
        return 0.9 if intent == "research" else 0.1
