"""Web search via DuckDuckGo."""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from friday._registry import Catalog
from friday._tools import Outcome, Proc, Spec


@Catalog.tag("proc", "search")
class SearchProc(Proc):
    label = "search"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="search",
            desc="Search the web for current info",
            params={
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Search query"},
                    "n": {"type": "integer", "description": "Max results", "default": 5},
                },
                "required": ["q"],
            },
        )

    def run(self, **kw) -> Outcome:
        q = kw.get("q", "")
        n = kw.get("n", 5)
        try:
            r = httpx.get("https://html.duckduckgo.com/html/", params={"q": q}, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            items = []
            for el in soup.select(".result__body")[:n]:
                t = el.select_one(".result__title")
                sn = el.select_one(".result__snippet")
                if t:
                    items.append(f"{t.get_text(strip=True)}: {sn.get_text(strip=True) if sn else ''}")
            return Outcome(action="search", text="\n".join(items) if items else "no results")
        except Exception as e:
            return Outcome(action="search", text=f"error: {e}", ok=False)
