import logging
from dataclasses import dataclass, field

logger = logging.getLogger("friday.browser")


@dataclass
class BrowserResult:
    success: bool
    output: str = ""
    url: str = ""
    title: str = ""
    error: str = ""


class BrowserTool:
    def __init__(self):
        self._playwright = None
        self._browser = None

    async def _ensure(self):
        if self._browser is not None:
            return
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
        except Exception as e:
            logger.warning("Playwright not available: %s", e)
            raise

    async def navigate(self, url: str, timeout: float = 15.0) -> BrowserResult:
        try:
            await self._ensure()
            page = await self._browser.new_page()
            await page.goto(url, timeout=int(timeout * 1000), wait_until="domcontentloaded")
            title = await page.title()
            content = await page.evaluate("document.body.innerText")
            await page.close()
            return BrowserResult(success=True, output=content[:5000], url=url, title=title)
        except Exception as e:
            return BrowserResult(success=False, error=str(e), url=url)

    async def screenshot(self, url: str, path: str = "/tmp/friday_screenshot.png") -> BrowserResult:
        try:
            await self._ensure()
            page = await self._browser.new_page(viewport={"width": 1280, "height": 720})
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            title = await page.title()
            await page.screenshot(path=path, full_page=False)
            await page.close()
            return BrowserResult(success=True, output=path, url=url, title=title)
        except Exception as e:
            return BrowserResult(success=False, error=str(e), url=url)

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
