"""
Tests for VikarmaAgent — autonomous agent loop, tool parsing, streaming
"""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.agents.autonomous_agent import VikarmaAgent, AGENT_SYSTEM_PROMPT, AIResult, ToolCall, TOOL_SCHEMAS
from server.agents.kan_memory import KANMemory


def ai_result(text="", tool_calls=None):
    """Helper: build AIResult from text (parses XML tags) or plain text."""
    agent = VikarmaAgent(AsyncMock(), MagicMock())
    calls = [ToolCall(name=n, params=p, call_id=f"t{i}") for i, (n, p) in enumerate(agent._parse_tool_calls(text))]
    return AIResult(text=text, tool_calls=calls or (tool_calls or []))


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def mem(tmp_path):
    return KANMemory(storage_dir=str(tmp_path))


def make_agent(ai_response, mem, tool_result=None):
    """Build agent with mocked AI and tool gateway."""
    mock_tools = MagicMock()
    mock_tools.execute = AsyncMock(return_value=tool_result or {"stdout": "ok", "returncode": 0, "success": True})
    agent = VikarmaAgent(ai_provider=AsyncMock(), tool_gateway=mock_tools, memory=mem)
    agent._call_ai = AsyncMock(return_value=ai_result(ai_response))
    return agent


# ── Tool parsing ───────────────────────────────────────────────────────────────

class TestParseToolCalls:
    def setup_method(self):
        self.agent = VikarmaAgent(
            ai_provider=AsyncMock(),
            tool_gateway=MagicMock(),
        )

    def test_no_tool_calls_returns_empty(self):
        result = self.agent._parse_tool_calls("Just a plain text response.")
        assert result == []

    def test_single_tool_call(self):
        text = '<tool>shell</tool>\n<params>{"command": "ls -la"}</params>'
        calls = self.agent._parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0] == ("shell", {"command": "ls -la"})

    def test_multiple_tool_calls(self):
        text = (
            '<tool>read_file</tool><params>{"path": "/etc/hosts"}</params>\n'
            '<tool>shell</tool><params>{"command": "pwd"}</params>'
        )
        calls = self.agent._parse_tool_calls(text)
        assert len(calls) == 2
        assert calls[0][0] == "read_file"
        assert calls[1][0] == "shell"

    def test_malformed_json_params_yields_empty_dict(self):
        text = '<tool>shell</tool><params>not json at all</params>'
        calls = self.agent._parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0] == ("shell", {})

    def test_tool_name_stripped(self):
        text = '<tool>  shell  </tool><params>{"command":"echo hi"}</params>'
        calls = self.agent._parse_tool_calls(text)
        assert calls[0][0] == "shell"

    def test_multiline_params(self):
        text = (
            '<tool>write_file</tool>\n'
            '<params>{\n  "path": "/tmp/test.txt",\n  "content": "hello"\n}</params>'
        )
        calls = self.agent._parse_tool_calls(text)
        assert calls[0] == ("write_file", {"path": "/tmp/test.txt", "content": "hello"})

    def test_tool_call_with_surrounding_text(self):
        text = (
            "I'll run a shell command:\n"
            '<tool>shell</tool><params>{"command": "date"}</params>\n'
            "This will show the current date."
        )
        calls = self.agent._parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0][0] == "shell"


# ── Tool result formatting ─────────────────────────────────────────────────────

class TestFormatToolResults:
    def setup_method(self):
        self.agent = VikarmaAgent(
            ai_provider=AsyncMock(),
            tool_gateway=MagicMock(),
        )

    def test_stdout_result(self):
        results = [{"tool": "shell", "params": {}, "result": {"stdout": "file1\nfile2", "stderr": ""}}]
        out = self.agent._format_tool_results(results)
        assert "[shell] stdout:" in out
        assert "file1" in out

    def test_stderr_fallback(self):
        results = [{"tool": "shell", "params": {}, "result": {"stdout": "", "stderr": "error msg"}}]
        out = self.agent._format_tool_results(results)
        assert "error msg" in out

    def test_content_result(self):
        results = [{"tool": "read_file", "params": {}, "result": {"content": "file contents here"}}]
        out = self.agent._format_tool_results(results)
        assert "[read_file] content:" in out
        assert "file contents here" in out

    def test_error_result(self):
        results = [{"tool": "shell", "params": {}, "result": {"error": "command not found"}}]
        out = self.agent._format_tool_results(results)
        assert "[shell] error:" in out
        assert "command not found" in out

    def test_generic_dict_result(self):
        results = [{"tool": "web_search", "params": {}, "result": {"results": ["a", "b"]}}]
        out = self.agent._format_tool_results(results)
        assert "[web_search]" in out

    def test_string_result(self):
        results = [{"tool": "remember", "params": {}, "result": "stored OK"}]
        out = self.agent._format_tool_results(results)
        assert "stored OK" in out

    def test_long_output_truncated(self):
        long_content = "x" * 3000
        results = [{"tool": "read_file", "params": {}, "result": {"content": long_content}}]
        out = self.agent._format_tool_results(results)
        # Should be truncated to 2000 chars + label
        assert len(out) < 2500

    def test_multiple_results_joined(self):
        results = [
            {"tool": "shell", "params": {}, "result": {"stdout": "r1", "stderr": ""}},
            {"tool": "shell", "params": {}, "result": {"stdout": "r2", "stderr": ""}},
        ]
        out = self.agent._format_tool_results(results)
        assert "r1" in out
        assert "r2" in out


# ── Agent run loop ─────────────────────────────────────────────────────────────

class TestAgentRun:
    @pytest.mark.asyncio
    async def test_simple_response_no_tools(self, mem):
        """Agent returns final answer when AI gives no tool calls."""
        agent = VikarmaAgent(AsyncMock(), MagicMock(), mem)
        agent._call_ai = AsyncMock(return_value=ai_result("Hello, I'm Tvaṣṭā!"))
        result = await agent.run("Say hello")
        assert result == "Hello, I'm Tvaṣṭā!"

    @pytest.mark.asyncio
    async def test_tool_call_then_final(self, mem):
        """Agent executes one tool then gives final answer."""
        tool_response = '<tool>shell</tool><params>{"command": "echo hi"}</params>'
        final_response = "The command output was: hi"

        mock_tools = MagicMock()
        mock_tools.execute = AsyncMock(return_value={"stdout": "hi\n", "stderr": "", "returncode": 0, "success": True})

        agent = VikarmaAgent(AsyncMock(), mock_tools, mem)
        agent._call_ai = AsyncMock(side_effect=[ai_result(tool_response), ai_result(final_response)])

        result = await agent.run("Run echo hi")
        assert result == final_response
        mock_tools.execute.assert_called_once_with("shell", {"command": "echo hi"})

    @pytest.mark.asyncio
    async def test_remember_tool_goes_to_memory(self, mem):
        """'remember' tool writes to KANMemory, not tool gateway."""
        remember_call = '<tool>remember</tool><params>{"key": "user", "value": "Bob"}</params>'
        final = "I remembered that."

        mock_tools = MagicMock()
        mock_tools.execute = AsyncMock()
        agent = VikarmaAgent(AsyncMock(), mock_tools, mem)
        agent._call_ai = AsyncMock(side_effect=[ai_result(remember_call), ai_result(final)])

        await agent.run("Remember the user is Bob")
        # Tool gateway should NOT have been called for remember
        mock_tools.execute.assert_not_called()
        # Memory should have the fact
        assert mem.recall_fact("user") != []

    @pytest.mark.asyncio
    async def test_recall_tool_reads_from_memory(self, mem):
        """'recall' tool reads from KANMemory."""
        mem.remember_fact("capital", "Paris")

        recall_call = '<tool>recall</tool><params>{"query": "capital"}</params>'
        final = "The capital is Paris."

        mock_tools = MagicMock()
        mock_tools.execute = AsyncMock()
        agent = VikarmaAgent(AsyncMock(), mock_tools, mem)
        agent._call_ai = AsyncMock(side_effect=[ai_result(recall_call), ai_result(final)])

        result = await agent.run("What is the capital?")
        assert result == final
        mock_tools.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_max_iterations_limit(self, mem):
        """Agent stops after MAX_ITERATIONS and returns warning."""
        # Always return a tool call — never terminates on its own
        tool_call = '<tool>shell</tool><params>{"command": "loop"}</params>'

        mock_tools = MagicMock()
        mock_tools.execute = AsyncMock(return_value={"stdout": "loop\n", "stderr": "", "returncode": 0, "success": True})

        agent = VikarmaAgent(AsyncMock(), mock_tools, mem)
        agent._call_ai = AsyncMock(return_value=ai_result(tool_call))

        result = await agent.run("Infinite loop task")
        assert "max iterations" in result.lower() or "⚠️" in result
        assert agent._call_ai.call_count == VikarmaAgent.MAX_ITERATIONS

    @pytest.mark.asyncio
    async def test_stream_callback_receives_events(self, mem):
        """Stream callback gets start, tool_call, tool_result, and final events."""
        tool_call = '<tool>shell</tool><params>{"command": "date"}</params>'
        final = "Done."

        mock_tools = MagicMock()
        mock_tools.execute = AsyncMock(return_value={"stdout": "Thu\n", "stderr": "", "returncode": 0, "success": True})

        agent = VikarmaAgent(AsyncMock(), mock_tools, mem)
        agent._call_ai = AsyncMock(side_effect=[ai_result(tool_call), ai_result(final)])

        events = []

        async def collect(e):
            events.append(e)

        await agent.run("What day is it?", stream_callback=collect)

        types = [e["type"] for e in events]
        assert "start" in types
        assert "tool_call" in types
        assert "tool_result" in types
        assert "final" in types

    @pytest.mark.asyncio
    async def test_run_stores_in_memory(self, mem):
        """Task and response are stored in short-term memory."""
        agent = VikarmaAgent(AsyncMock(), MagicMock(), mem)
        agent._call_ai = AsyncMock(return_value=ai_result("response text"))

        await agent.run("user task")
        contents = [m["content"] for m in mem.short_term]
        assert "user task" in contents
        assert "response text" in contents

    @pytest.mark.asyncio
    async def test_set_provider(self, mem):
        agent = VikarmaAgent(AsyncMock(), MagicMock(), mem)
        agent.set_provider("openai")
        assert agent.provider == "openai"


# ── Streaming generator ────────────────────────────────────────────────────────

class TestRunStream:
    @pytest.mark.asyncio
    async def test_run_stream_yields_events(self, mem):
        """run_stream yields events from agent execution."""
        mock_tools = MagicMock()
        mock_tools.execute = AsyncMock()
        agent = VikarmaAgent(AsyncMock(), mock_tools, mem)
        agent._call_ai = AsyncMock(return_value=ai_result("Stream answer"))

        events = []
        async for event in agent.run_stream("stream test"):
            events.append(event)

        assert len(events) >= 2  # at least start + final
        types = {e["type"] for e in events}
        assert "start" in types
        assert "final" in types


# ── System prompt ──────────────────────────────────────────────────────────────

class TestSystemPrompt:
    def test_system_prompt_contains_tools(self):
        tool_names = {t["function"]["name"] for t in TOOL_SCHEMAS}
        assert "shell" in tool_names
        assert "read_file" in tool_names
        assert "web_search" in tool_names
        assert "remember" in tool_names
        assert "recall" in tool_names

    def test_system_prompt_contains_rules(self):
        assert "Ahimsa" in AGENT_SYSTEM_PROMPT
        assert "Max 10" in AGENT_SYSTEM_PROMPT
