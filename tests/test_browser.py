import pytest
from friday.tools.browser import BrowserTool, BrowserResult


@pytest.mark.asyncio
async def test_browser_tool_class_exists():
    bt = BrowserTool()
    assert isinstance(bt, BrowserTool)


@pytest.mark.asyncio
async def test_browser_result_dataclass():
    r = BrowserResult(success=True, output="content", url="https://example.com", title="Example")
    assert r.success
    assert r.title == "Example"
    assert r.url == "https://example.com"


@pytest.mark.asyncio
async def test_browser_navigate():
    bt = BrowserTool()
    result = await bt.navigate("https://example.com")
    assert result.success
    assert "Example Domain" in result.output
    assert result.title == "Example Domain"
    await bt.close()


@pytest.mark.asyncio
async def test_browser_screenshot(tmp_path):
    bt = BrowserTool()
    path = str(tmp_path / "ss.png")
    result = await bt.screenshot("https://example.com", path=path)
    assert result.success
    import os
    assert os.path.exists(path)
    await bt.close()
