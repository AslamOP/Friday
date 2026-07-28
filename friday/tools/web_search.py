from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
from friday.core.tool import Tool

class WebSearch(Tool):
    name = "web_search"
    description = "Search the web for current information"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "count": {"type": "integer", "description": "Number of results", "default": 5},
        },
        "required": ["query"],
    }
    
    def run(self, query: str, count: int = 5) -> str:
        try:
            resp = httpx.get("https://html.duckduckgo.com/html/", params={"q": query}, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            for r in soup.select(".result__body")[:count]:
                title = r.select_one(".result__title")
                snippet = r.select_one(".result__snippet")
                if title:
                    results.append(f"{title.get_text(strip=True)}: {snippet.get_text(strip=True) if snippet else ''}")
            return "\n".join(results) if results else "No results found."
        except Exception as e:
            return f"Search error: {e}"

class WebFetch(Tool):
    name = "web_fetch"
    description = "Fetch and extract text content from a URL"
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
        },
        "required": ["url"],
    }
    
    def run(self, url: str) -> str:
        try:
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return text[:4000]
        except Exception as e:
            return f"Fetch error: {e}"
