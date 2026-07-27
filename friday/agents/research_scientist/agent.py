from ..base import BaseAgent, Context, Result, Task
from . import prompts
from friday.router.omniroute import OmniRouteClient
from friday.tools.web_search import WebSearchTool
class ResearchScientistAgent(BaseAgent):
    name = "research_scientist"
    def __init__(self):
        super().__init__(model_preference="anthropic/claude-3.5-sonnet")
        self._router = OmniRouteClient(); self._web = WebSearchTool()
    async def handle(self, task, context):
        text = context.user_input; results = await self._web.search(text)
        ctx = ""
        if results.results:
            ctx = "## Web\n" + "\n".join(f"- [{r.title}]({r.url})\n  {r.snippet}" for r in results.results[:4])
            scraped = await self._web.scrape(results.results[0].url)
            if scraped and not scraped.startswith("[scrape"): ctx += f"\n## Page\n{scraped[:1500]}"
        prompt = prompts.PROMPT.format(input=text)
        if ctx: prompt += f"\n\n{ctx}"
        r = await self._router.route("research", prompt, prompts.SYSTEM_PROMPT)
        output = r.get("content", "")
        if results.results:
            output += "\n\n---\n## Sources\n" + "\n".join(f"- [{ri.title}]({ri.url})" for ri in results.results[:3])
        return Result(success=True, output=output, agent=self.name)
    async def can_handle(self, intent): return 0.9 if intent == "research" else 0.1
