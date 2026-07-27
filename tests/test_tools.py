import pytest
from pathlib import Path
from friday.tools.file_ops import FileOps
from friday.tools.shell_sandbox import ShellSandbox


@pytest.mark.asyncio
class TestFileOps:
    async def test_read_write(self, tmp_path):
        fo = FileOps(workspace=str(tmp_path))
        res = await fo.write("test.txt", "hello world")
        assert res.success
        res = await fo.read("test.txt")
        assert res.success
        assert res.output == "hello world"

    async def test_read_missing(self, tmp_path):
        fo = FileOps(workspace=str(tmp_path))
        res = await fo.read("nope.txt")
        assert not res.success
        assert "Not found" in res.output

    async def test_info(self, tmp_path):
        fo = FileOps(workspace=str(tmp_path))
        f = tmp_path / "info.txt"
        f.write_text("x")
        res = await fo.info(str(f))
        assert res.success

    async def test_search(self, tmp_path):
        fo = FileOps(workspace=str(tmp_path))
        (tmp_path / "abc.txt").write_text("x")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "def.py").write_text("y")
        res = await fo.search("*.txt")
        assert res.success
        assert "abc.txt" in res.output

    async def test_tree(self, tmp_path):
        fo = FileOps(workspace=str(tmp_path))
        (tmp_path / "top.txt").write_text("x")
        res = await fo.tree()
        assert res.success
        assert "top.txt" in res.output


@pytest.mark.asyncio
class TestShellSandbox:
    async def test_echo(self, tmp_path):
        ss = ShellSandbox(workspace=str(tmp_path))
        res = await ss.run("echo hello")
        assert res.success
        assert "hello" in res.output

    async def test_failure(self, tmp_path):
        ss = ShellSandbox(workspace=str(tmp_path))
        res = await ss.run("exit 1")
        assert not res.success

    async def test_blocked_commands(self, tmp_path):
        ss = ShellSandbox(workspace=str(tmp_path))
        res = await ss.run("rm -rf /")
        assert not res.success
        assert "Blocked" in res.error

    async def test_timeout(self, tmp_path):
        ss = ShellSandbox(workspace=str(tmp_path))
        res = await ss.run("sleep 10", timeout=1)
        assert not res.success
        assert "Timeout" in res.error
