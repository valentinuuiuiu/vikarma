"""
Tests for VikarmaToolGateway — file system, shell, web, python tools
"""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.tools.gateway import VikarmaToolGateway


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def gw(tmp_path):
    return VikarmaToolGateway(workspace=str(tmp_path))


# ── File system tools ──────────────────────────────────────────────────────────

class TestWriteAndReadFile:
    @pytest.mark.asyncio
    async def test_write_then_read(self, gw, tmp_path):
        path = str(tmp_path / "test.txt")
        write_result = await gw.write_file(path, "hello vikarma")
        assert write_result["success"] is True

        read_result = await gw.read_file(path)
        assert read_result["content"] == "hello vikarma"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, gw):
        result = await gw.read_file("/nonexistent/path/file.txt")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_write_creates_parent_dirs(self, gw, tmp_path):
        path = str(tmp_path / "deep" / "dir" / "file.txt")
        result = await gw.write_file(path, "nested")
        assert result["success"] is True
        assert Path(path).read_text() == "nested"

    @pytest.mark.asyncio
    async def test_write_append_mode(self, gw, tmp_path):
        path = str(tmp_path / "append.txt")
        await gw.write_file(path, "line1\n", mode="w")
        await gw.write_file(path, "line2\n", mode="a")
        result = await gw.read_file(path)
        assert "line1" in result["content"]
        assert "line2" in result["content"]

    @pytest.mark.asyncio
    async def test_read_returns_line_count(self, gw, tmp_path):
        path = str(tmp_path / "lines.txt")
        await gw.write_file(path, "a\nb\nc\n")
        result = await gw.read_file(path)
        assert result["lines"] == 4  # 3 newlines + 1

    @pytest.mark.asyncio
    async def test_read_truncated_flag(self, gw, tmp_path):
        path = str(tmp_path / "big.txt")
        big_content = "x" * (gw.MAX_OUTPUT + 100)
        await gw.write_file(path, big_content)
        result = await gw.read_file(path)
        assert result["truncated"] is True
        assert len(result["content"]) == gw.MAX_OUTPUT


class TestListDir:
    @pytest.mark.asyncio
    async def test_list_dir_contents(self, gw, tmp_path):
        (tmp_path / "file.txt").write_text("hi")
        (tmp_path / "subdir").mkdir()
        result = await gw.list_dir(str(tmp_path))
        names = [i["name"] for i in result["items"]]
        assert "file.txt" in names
        assert "subdir" in names

    @pytest.mark.asyncio
    async def test_list_dir_type_field(self, gw, tmp_path):
        (tmp_path / "f.txt").write_text("x")
        (tmp_path / "d").mkdir()
        result = await gw.list_dir(str(tmp_path))
        types = {i["name"]: i["type"] for i in result["items"]}
        assert types["f.txt"] == "file"
        assert types["d"] == "dir"

    @pytest.mark.asyncio
    async def test_list_dir_hides_dotfiles_by_default(self, gw, tmp_path):
        (tmp_path / ".hidden").write_text("secret")
        (tmp_path / "visible.txt").write_text("ok")
        result = await gw.list_dir(str(tmp_path))
        names = [i["name"] for i in result["items"]]
        assert ".hidden" not in names
        assert "visible.txt" in names

    @pytest.mark.asyncio
    async def test_list_dir_show_hidden(self, gw, tmp_path):
        (tmp_path / ".dotfile").write_text("x")
        result = await gw.list_dir(str(tmp_path), show_hidden=True)
        names = [i["name"] for i in result["items"]]
        assert ".dotfile" in names

    @pytest.mark.asyncio
    async def test_list_nonexistent_dir(self, gw):
        result = await gw.list_dir("/nonexistent/dir")
        assert "error" in result


class TestDeleteFile:
    @pytest.mark.asyncio
    async def test_delete_file(self, gw, tmp_path):
        p = tmp_path / "delete_me.txt"
        p.write_text("bye")
        result = await gw.delete_file(str(p))
        assert result["success"] is True
        assert not p.exists()

    @pytest.mark.asyncio
    async def test_delete_directory(self, gw, tmp_path):
        d = tmp_path / "del_dir"
        d.mkdir()
        (d / "file.txt").write_text("x")
        result = await gw.delete_file(str(d))
        assert result["success"] is True
        assert not d.exists()


class TestCopyAndMoveFile:
    @pytest.mark.asyncio
    async def test_copy_file(self, gw, tmp_path):
        src = tmp_path / "src.txt"
        src.write_text("content")
        dst = tmp_path / "dst.txt"
        result = await gw.copy_file(str(src), str(dst))
        assert result["success"] is True
        assert dst.read_text() == "content"
        assert src.exists()  # original still there

    @pytest.mark.asyncio
    async def test_move_file(self, gw, tmp_path):
        src = tmp_path / "old.txt"
        src.write_text("data")
        dst = tmp_path / "new.txt"
        result = await gw.move_file(str(src), str(dst))
        assert result["success"] is True
        assert dst.read_text() == "data"
        assert not src.exists()


class TestFindFiles:
    @pytest.mark.asyncio
    async def test_find_by_pattern(self, gw, tmp_path):
        (tmp_path / "a.py").write_text("x")
        (tmp_path / "b.py").write_text("x")
        (tmp_path / "c.txt").write_text("x")
        result = await gw.find_files("*.py", str(tmp_path))
        assert result["count"] == 2
        assert all(m.endswith(".py") for m in result["matches"])

    @pytest.mark.asyncio
    async def test_find_recursive(self, gw, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.py").write_text("x")
        result = await gw.find_files("*.py", str(tmp_path))
        assert result["count"] >= 1


class TestFileExists:
    @pytest.mark.asyncio
    async def test_existing_file(self, gw, tmp_path):
        p = tmp_path / "exists.txt"
        p.write_text("yes")
        result = await gw.file_exists(str(p))
        assert result["exists"] is True
        assert result["is_file"] is True
        assert result["is_dir"] is False

    @pytest.mark.asyncio
    async def test_nonexistent_path(self, gw):
        result = await gw.file_exists("/no/such/path/file.txt")
        assert result["exists"] is False


class TestMakeDir:
    @pytest.mark.asyncio
    async def test_make_dir(self, gw, tmp_path):
        new_dir = str(tmp_path / "newdir" / "nested")
        result = await gw.make_dir(new_dir)
        assert result["success"] is True
        assert Path(new_dir).is_dir()


# ── Shell tool ─────────────────────────────────────────────────────────────────

class TestShell:
    @pytest.mark.asyncio
    async def test_simple_command(self, gw):
        result = await gw.shell("echo hello")
        assert result["success"] is True
        assert "hello" in result["stdout"]

    @pytest.mark.asyncio
    async def test_stderr_captured(self, gw):
        result = await gw.shell("echo error_msg >&2")
        assert "error_msg" in result["stderr"]

    @pytest.mark.asyncio
    async def test_nonzero_exit_code(self, gw):
        result = await gw.shell("exit 1")
        assert result["success"] is False
        assert result["returncode"] == 1

    @pytest.mark.asyncio
    async def test_command_timeout(self, gw):
        result = await gw.shell("sleep 60", timeout=1)
        assert "error" in result
        assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_command_with_cwd(self, gw, tmp_path):
        result = await gw.shell("pwd", cwd=str(tmp_path))
        assert str(tmp_path) in result["stdout"]


# ── Python tool ────────────────────────────────────────────────────────────────

class TestRunPython:
    @pytest.mark.asyncio
    async def test_simple_print(self, gw):
        result = await gw.run_python("print('vikarma')")
        assert result["success"] is True
        assert "vikarma" in result["stdout"]

    @pytest.mark.asyncio
    async def test_math_output(self, gw):
        result = await gw.run_python("print(2 + 2)")
        assert "4" in result["stdout"]

    @pytest.mark.asyncio
    async def test_syntax_error_captured(self, gw):
        result = await gw.run_python("def bad syntax(")
        assert result["success"] is False
        assert result["returncode"] != 0

    @pytest.mark.asyncio
    async def test_timeout(self, gw):
        result = await gw.run_python("import time; time.sleep(60)", timeout=1)
        assert "error" in result
        assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_multiline_code(self, gw):
        code = "total = sum(range(10))\nprint(total)"
        result = await gw.run_python(code)
        assert "45" in result["stdout"]


# ── Env tools ──────────────────────────────────────────────────────────────────

class TestEnvTools:
    @pytest.mark.asyncio
    async def test_set_and_get_env(self, gw):
        await gw.set_env("VIKARMA_TEST_VAR", "sacred")
        result = await gw.get_env("VIKARMA_TEST_VAR")
        assert result["value"] == "sacred"
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_get_nonexistent_env(self, gw):
        result = await gw.get_env("VIKARMA_DEFINITELY_NOT_SET_XYZ123")
        assert result["exists"] is False
        assert result["value"] is None


# ── Execute dispatch ───────────────────────────────────────────────────────────

class TestExecuteDispatch:
    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, gw):
        result = await gw.execute("nonexistent_tool", {})
        assert "error" in result
        assert "Unknown tool" in result["error"]
        assert "available" in result

    @pytest.mark.asyncio
    async def test_execute_records_history(self, gw):
        await gw.execute("shell", {"command": "echo tracked"})
        assert len(gw.history) == 1
        assert gw.history[0]["tool"] == "shell"

    @pytest.mark.asyncio
    async def test_clear_history(self, gw):
        await gw.execute("shell", {"command": "echo x"})
        gw.clear_history()
        assert gw.history == []

    @pytest.mark.asyncio
    async def test_execute_bad_params_returns_error(self, gw):
        # shell requires 'command' param — passing nothing triggers TypeError
        result = await gw.execute("shell", {})
        assert "error" in result


# ── Path resolution ────────────────────────────────────────────────────────────

class TestPathResolution:
    def test_absolute_path_unchanged(self, gw):
        p = gw._resolve("/absolute/path.txt")
        assert str(p) == "/absolute/path.txt"

    def test_relative_path_anchored_to_workspace(self, gw, tmp_path):
        p = gw._resolve("relative.txt")
        assert str(p) == str(tmp_path / "relative.txt")
