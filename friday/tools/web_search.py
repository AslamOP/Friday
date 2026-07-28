import logging
import re
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("friday.web_search")
_USER = "Mozilla/5.0 (X11; Linux x86_64) FRIDAY/2.6"
_DDG = "https://html.duckduckgo.com/html"


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    content: str = ""


@dataclass
class SearchResponse:
    results: list[SearchResult] = field(default_factory=list)
    error: str = ""


_clean = re.compile(r"<[^>]+>")


def _strip(text: str) -> str:
    return _clean.sub("", text).strip()


class WebSearchTool:
    async def search(self, query: str, max_results: int = 5) -> SearchResponse:
        try:
            r = await httpx.AsyncClient(timeout=15.0, follow_redirects=True).post(
                _DDG, data={"q": query}, headers={"User-Agent": _USER}
            )
            r.raise_for_status()
            return self._parse(r.text, max_results)
        except Exception as e:
            return SearchResponse(error=str(e))

    def _parse(self, html: str, limit: int) -> SearchResponse:
        results = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.select("a.result__a, a.result-link, h2 a, .result__title a"):
                if len(results) >= limit:
                    break
                t, u = _strip(a.get_text()), a.get("href", "")
                if t and u:
                    results.append(SearchResult(title=t, url=u))
            snippet_selectors = [".result__snippet", ".result-snippet", ".snippet", ".result__snippet span"]
            for sel in snippet_selectors:
                snips = soup.select(sel)
                if snips:
                    for i, s in enumerate(snips):
                        if i < len(results):
                            results[i].snippet = _strip(s.get_text())
                    break
        except Exception as e:
            logger.warning("Parse: %s", e)
        return SearchResponse(results=results)

    async def scrape(self, url: str, max_chars: int = 3000) -> str:
        try:
            r = await httpx.AsyncClient(timeout=10.0, follow_redirects=True).get(url, headers={"User-Agent": _USER})
            r.raise_for_status()
            return self._extract(r.text, max_chars)
        except Exception as e:
            return f"[error: {e}]"

    def _extract(self, html: str, limit: int) -> str:
        try:
            soup = BeautifulSoup(html, "html.parser")
            for t in soup(["script", "style", "nav", "footer", "header"]):
                t.decompose()
            lines = soup.get_text(separator="\n").splitlines()
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            return "\n".join(cleaned_lines)[:limit]
        except Exception as e:
            logger.warning("Extract: %s", e)
        return ""
