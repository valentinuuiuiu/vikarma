"""
VIKARMA — Tool Gateway
OpenClaw-style: file system, shell, browser, web, code execution
🔱 Om Namah Shivaya — For All Humanity
"""

import asyncio
import os
import subprocess
import json
import shutil
from pathlib import Path
from typing import Optional
import httpx


class VikarmaToolGateway:
    """Sacred gateway for tool execution — powerful but Ahimsa-guided."""

    TIMEOUT = 30
    MAX_OUTPUT = 8000

    def __init__(self, workspace: str = os.path.expanduser("~")):
        self.workspace = Path(workspace)
        self.history: list[dict] = []

    async def execute(self, tool: str, params: dict) -> dict:
        """Route to appropriate tool"""
        handlers = {
            "shell": self.shell,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "list_dir": self.list_dir,
            "delete_file": self.delete_file,
            "copy_file": self.copy_file,
            "move_file": self.move_file,
            "web_fetch": self.web_fetch,
            "web_search": self.web_search,
            "python": self.run_python,
            "find_files": self.find_files,
            "file_exists": self.file_exists,
            "make_dir": self.make_dir,
            "get_env": self.get_env,
            "set_env": self.set_env,
        }
        handler = handlers.get(tool)
        if not handler:
            return {"error": f"Unknown tool: {tool}", "available": list(handlers.keys())}

        try:
            result = await handler(**params)
            self.history.append({"tool": tool, "params": params, "result": result})
            return result
        except Exception as e:
            return {"error": str(e), "tool": tool}

    # ── SHELL ──────────────────────────────────────────────────────────────

    async def shell(self, command: str, cwd: str = None, timeout: int = None) -> dict:
        """Execute shell command"""
        work_dir = Path(cwd) if cwd else self.workspace
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir),
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout or self.TIMEOUT
            )
            return {
                "stdout": stdout.decode()[:self.MAX_OUTPUT],
                "stderr": stderr.decode()[:2000],
                "returncode": proc.returncode,
                "success": proc.returncode == 0,
            }
        except asyncio.TimeoutError:
            return {"error": f"Command timed out after {timeout or self.TIMEOUT}s"}

    # ── FILE SYSTEM ────────────────────────────────────────────────────────

    async def read_file(self, path: str, encoding: str = "utf-8") -> dict:
        """Read file contents"""
        p = self._resolve(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}
        try:
            content = p.read_text(encoding=encoding)
            return {
                "content": content[:self.MAX_OUTPUT],
                "size": p.stat().st_size,
                "lines": content.count("\n") + 1,
                "truncated": len(content) > self.MAX_OUTPUT,
            }
        except Exception as e:
            return {"error": str(e)}

    async def write_file(self, path: str, content: str, mode: str = "w") -> dict:
        """Write content to file"""
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(p, mode, encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": str(p), "size": p.stat().st_size}
        except Exception as e:
            return {"error": str(e)}

    async def list_dir(self, path: str = ".", show_hidden: bool = False) -> dict:
        """List directory contents"""
        p = self._resolve(path)
        if not p.exists():
            return {"error": f"Directory not found: {path}"}
        try:
            items = []
            for item in sorted(p.iterdir()):
                if not show_hidden and item.name.startswith("."):
                    continue
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                })
            return {"path": str(p), "items": items, "count": len(items)}
        except Exception as e:
            return {"error": str(e)}

    async def delete_file(self, path: str) -> dict:
        """Delete file or directory"""
        p = self._resolve(path)
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return {"success": True, "deleted": str(p)}
        except Exception as e:
            return {"error": str(e)}

    async def copy_file(self, src: str, dst: str) -> dict:
        """Copy file"""
        s, d = self._resolve(src), self._resolve(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(str(s), str(d))
            return {"success": True, "src": str(s), "dst": str(d)}
        except Exception as e:
            return {"error": str(e)}

    async def move_file(self, src: str, dst: str) -> dict:
        """Move/rename file"""
        s, d = self._resolve(src), self._resolve(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(s), str(d))
            return {"success": True, "src": str(s), "dst": str(d)}
        except Exception as e:
            return {"error": str(e)}

    async def find_files(self, pattern: str, path: str = ".") -> dict:
        """Find files matching pattern"""
        p = self._resolve(path)
        try:
            matches = [str(f) for f in p.rglob(pattern)][:50]
            return {"matches": matches, "count": len(matches)}
        except Exception as e:
            return {"error": str(e)}

    async def file_exists(self, path: str) -> dict:
        """Check if file/dir exists"""
        p = self._resolve(path)
        return {"exists": p.exists(), "is_file": p.is_file(), "is_dir": p.is_dir(), "path": str(p)}

    async def make_dir(self, path: str) -> dict:
        """Create directory"""
        p = self._resolve(path)
        try:
            p.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(p)}
        except Exception as e:
            return {"error": str(e)}

    # ── WEB ────────────────────────────────────────────────────────────────

    async def web_fetch(self, url: str, method: str = "GET", headers: dict = None, body: str = None) -> dict:
        """Fetch URL content"""
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                r = await client.request(
                    method, url,
                    headers=headers or {"User-Agent": "Vikarma/1.0"},
                    content=body
                )
                return {
                    "status": r.status_code,
                    "content": r.text[:self.MAX_OUTPUT],
                    "headers": dict(r.headers),
                    "url": str(r.url),
                }
        except Exception as e:
            return {"error": str(e)}

    async def web_search(self, query: str, max_results: int = 5) -> dict:
        """Search the web via DuckDuckGo"""
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, headers={"User-Agent": "Vikarma/1.0"})
                data = r.json()
                results = []
                if data.get("AbstractText"):
                    results.append({"title": data.get("Heading", ""), "snippet": data["AbstractText"], "url": data.get("AbstractURL", "")})
                for item in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(item, dict) and "Text" in item:
                        results.append({"title": item.get("Text", "")[:100], "snippet": item.get("Text", ""), "url": item.get("FirstURL", "")})
                return {"results": results[:max_results], "query": query}
        except Exception as e:
            return {"error": str(e)}

    # ── PYTHON ─────────────────────────────────────────────────────────────

    async def run_python(self, code: str, timeout: int = 15) -> dict:
        """Execute Python code safely"""
        tmp = Path("/tmp/vikarma_exec.py")
        tmp.write_text(code)
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", str(tmp),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "stdout": stdout.decode()[:self.MAX_OUTPUT],
                "stderr": stderr.decode()[:2000],
                "returncode": proc.returncode,
                "success": proc.returncode == 0,
            }
        except asyncio.TimeoutError:
            return {"error": f"Python execution timed out after {timeout}s"}
        finally:
            tmp.unlink(missing_ok=True)

    # ── ENV ────────────────────────────────────────────────────────────────

    async def get_env(self, key: str) -> dict:
        """Get environment variable"""
        val = os.getenv(key)
        return {"key": key, "value": val, "exists": val is not None}

    async def set_env(self, key: str, value: str) -> dict:
        """Set environment variable for current process"""
        os.environ[key] = value
        return {"success": True, "key": key}

    # ── HELPERS ────────────────────────────────────────────────────────────

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p

    def get_history(self) -> list:
        return self.history

    def clear_history(self):
        self.history.clear()


# ── Tool descriptions for AI context ──────────────────────────────────────────

TOOL_DESCRIPTIONS = {
    "shell": "Execute shell commands. params: command(str), cwd(str optional), timeout(int optional)",
    "read_file": "Read file contents. params: path(str), encoding(str optional)",
    "write_file": "Write to file. params: path(str), content(str), mode(str: 'w'|'a')",
    "list_dir": "List directory. params: path(str optional), show_hidden(bool optional)",
    "delete_file": "Delete file/dir. params: path(str)",
    "copy_file": "Copy file. params: src(str), dst(str)",
    "move_file": "Move/rename. params: src(str), dst(str)",
    "find_files": "Find files by pattern. params: pattern(str), path(str optional)",
    "file_exists": "Check existence. params: path(str)",
    "make_dir": "Create directory. params: path(str)",
    "web_fetch": "Fetch URL. params: url(str), method(str optional), headers(dict optional)",
    "web_search": "Search web. params: query(str), max_results(int optional)",
    "python": "Run Python code. params: code(str), timeout(int optional)",
    "get_env": "Get env var. params: key(str)",
    "set_env": "Set env var. params: key(str), value(str)",
}
