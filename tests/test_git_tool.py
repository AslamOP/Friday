import pytest
from pathlib import Path
from friday.tools.git_tool import GitTool, GitResult


@pytest.mark.asyncio
async def test_git_tool_class_exists():
    gt = GitTool()
    assert isinstance(gt, GitTool)


@pytest.mark.asyncio
async def test_git_result_dataclass():
    r = GitResult(success=True, output="ok", returncode=0)
    assert r.success
    assert r.output == "ok"


@pytest.mark.asyncio
async def test_git_status_in_non_repo(tmp_path):
    gt = GitTool(repo_path=str(tmp_path))
    result = await gt.status()
    assert not result.success
    assert result.returncode != 0


@pytest.mark.asyncio
async def test_git_status_in_repo():
    root = Path(__file__).resolve().parent.parent
    if (root / ".git").exists():
        gt = GitTool(repo_path=str(root))
        result = await gt.status()
        assert isinstance(result, GitResult)
        if result.success:
            assert isinstance(result.output, str)


@pytest.mark.asyncio
async def test_blocked_commands():
    gt = GitTool()
    result = await gt.run("push", "--force")
    assert not result.success


@pytest.mark.asyncio
async def test_log(tmp_path):
    gt = GitTool(repo_path=str(tmp_path))
    result = await gt.log()
    assert not result.success
