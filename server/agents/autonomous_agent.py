"""
VIKARMA — Autonomous Agent (Tvaṣṭā)
Native function calling. Real tools. No hallucination. No theater.
🔱 Om Namah Shivaya — For All Humanity
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional, Callable, AsyncGenerator

from .kan_memory import KANMemory

logger = logging.getLogger(__name__)

# ── Native tool schemas (OpenAI function-calling format) ───────────────────────

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "shell",
        "description": "Run a bash command and return stdout/stderr.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "The bash command to execute"}
        }, "required": ["command"]},
    }},
    {"type": "function", "function": {
        "name": "python",
        "description": "Execute Python code and return the result.",
        "parameters": {"type": "object", "properties": {
            "code": {"type": "string", "description": "Python code to execute"}
        }, "required": ["code"]},
    }},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file from the filesystem.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Absolute or relative file path"}
        }, "required": ["path"]},
    }},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write content to a file.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"}
        }, "required": ["path", "content"]},
    }},
    {"type": "function", "function": {
        "name": "list_dir",
        "description": "List files in a directory.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Directory path"}
        }, "required": ["path"]},
    }},
    {"type": "function", "function": {
        "name": "find_files",
        "description": "Find files matching a glob pattern.",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string", "description": "Glob pattern e.g. *.py"},
            "path": {"type": "string", "description": "Root directory to search", "default": "."}
        }, "required": ["pattern"]},
    }},
    {"type": "function", "function": {
        "name": "web_fetch",
        "description": "Fetch a URL and return the content.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}
        }, "required": ["url"]},
    }},
    {"type": "function", "function": {
        "name": "web_search",
        "description": "Search the web and return results.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "remember",
        "description": "Store a fact in long-term memory.",
        "parameters": {"type": "object", "properties": {
            "key": {"type": "string"},
            "value": {"type": "string"}
        }, "required": ["key", "value"]},
    }},
    {"type": "function", "function": {
        "name": "recall",
        "description": "Search long-term memory for facts.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "temple",
        "description": (
            "Invoke a Bhairava Temple skill (external API/service). "
            "Categories: DATA (postgresql, redis, huggingface), "
            "COMMS (discord, telegram, github), "
            "FINANCE (coingecko, kraken, binance, stripe), "
            "KNOWLEDGE (wikipedia, arxiv, weather, duckduckgo), "
            "BLOCKCHAIN (chainlink, alchemy), "
            "SACRED (calculator, translator)."
        ),
        "parameters": {"type": "object", "properties": {
            "temple": {"type": "string", "description": "Temple name e.g. coingecko"},
            "action": {"type": "string", "description": "Action e.g. price, query, forecast"},
            "params": {"type": "object", "description": "Action parameters", "default": {}}
        }, "required": ["temple", "action"]},
    }},
]

# Anthropic tool_use format (converted from TOOL_SCHEMAS)
ANTHROPIC_TOOLS = [
    {
        "name": t["function"]["name"],
        "description": t["function"]["description"],
        "input_schema": t["function"]["parameters"],
    }
    for t in TOOL_SCHEMAS
]

AGENT_SYSTEM_PROMPT = SYSTEM_PROMPT = """You are Tvaṣṭā — the autonomous agent in VIKARMA.
Built for all of humanity. Free. Ahimsa. Om Namah Shivaya 🔱

Rules:
- Use tools to get real data. Never fabricate results.
- Think before acting. One tool at a time, check the result, decide next step.
- Be concise in final answers — no theater, no padding.
- Ahimsa — never do harmful things.
- Max 10 tool calls per task.

── XML Tag Format (Claude only) ──────────────────────────────────────────────
When responding as Claude, you may also call tools using explicit XML tags:
<tool>tool_name</tool>
<params>{"key": "value"}</params>

This creates a visible audit trail of every action. Use it."""


@dataclass
class ToolCall:
    name: str
    params: dict
    call_id: str = ""


@dataclass
class AIResult:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)


# ── Provider configs ────────────────────────────────────────────────────────────

PROVIDER_CONFIGS = {
    "openai":    {"key_env": "OPENAI_API_KEY",    "base": None,                                                              "model": "gpt-4o"},
    "deepseek":  {"key_env": "DEEPSEEK_API_KEY",  "base": "https://api.deepseek.com/v1",                                    "model": "deepseek-chat"},
    "qwen":      {"key_env": "QWEN_API_KEY",       "base": "https://dashscope.aliyuncs.com/compatible-mode/v1",             "model": "qwen-max"},
    "grok":      {"key_env": "GROK_API_KEY",       "base": "https://api.x.ai/v1",                                           "model": "grok-beta"},
    "minimax":   {"key_env": "MINIMAX_API_KEY",    "base": "https://api.minimax.io/v1",                                     "model": "MiniMax-M2.7"},
    "gemini":    {"key_env": "GEMINI_API_KEY",     "base": "https://generativelanguage.googleapis.com/v1beta/openai",       "model": "gemini-2.0-flash-preview"},
    "copilot":   {"key_env": "GITHUB_COPILOT_TOKEN", "base": "https://api.githubcopilot.com",                               "model": "gpt-4o"},
    "kimi":      {"key_env": None,                 "base": None,  "ollama_model": "kimi-k2.5:cloud"},
    "qwen3":     {"key_env": None,                 "base": None,  "ollama_model": "qwen3.5:cloud"},
    "ollama":    {"key_env": None,                 "base": None,  "ollama_model": None},
}


class VikarmaAgent:
    """
    Tvaṣṭā — autonomous agent with native function calling.
    Supports Claude, Kimi K2.5, MiniMax M2.7, Gemini, and more.
    """

    MAX_ITERATIONS = 10

    def __init__(
        self,
        ai_provider: Callable,
        tool_gateway: object,
        memory: Optional[KANMemory] = None,
    ):
        self.ai = ai_provider
        self.tools = tool_gateway
        self.memory = memory or KANMemory()
        self.provider = "claude"

    def set_provider(self, provider: str):
        """Set AI provider: claude | openai | deepseek | qwen | grok |
        minimax | gemini | copilot | kimi | qwen3 | ollama"""
        self.provider = provider

    # ── Main agent loop ────────────────────────────────────────────────────────

    async def run(self, task: str, stream_callback: Optional[Callable] = None) -> str:
        self.memory.remember_now(task, role="user")

        system = SYSTEM_PROMPT
        mem = self.memory.build_context_summary()
        if mem:
            system += f"\n\n{mem}"

        # Message history — OpenAI format for all providers
        messages = self.memory.get_context_window(10) + [{"role": "user", "content": task}]
        iterations = 0
        final_response = ""

        if stream_callback:
            await stream_callback({"type": "start", "task": task})

        while iterations < self.MAX_ITERATIONS:
            iterations += 1

            result = await self._call_ai(messages, system)

            if not result.tool_calls:
                final_response = result.text
                self.memory.remember_now(result.text, role="assistant")
                if stream_callback:
                    await stream_callback({"type": "final", "response": result.text})
                break

            # Append assistant message with tool calls
            messages.append(self._assistant_msg(result))

            # Execute each tool call
            tool_msgs = []
            for tc in result.tool_calls:
                if stream_callback:
                    await stream_callback({"type": "tool_call", "tool": tc.name, "params": tc.params})

                tool_result = await self._execute_tool(tc)
                result_str = self._serialize_result(tool_result)

                if stream_callback:
                    await stream_callback({"type": "tool_result", "tool": tc.name, "result": tool_result})

                tool_msgs.append(self._tool_result_msg(tc, result_str))

            messages.extend(tool_msgs)

        else:
            final_response = f"Reached max iterations ({self.MAX_ITERATIONS}). Last response:\n\n{result.text}"

        if len(messages) > 4:
            self.memory.save_episode(
                title=task[:60],
                summary=final_response[:200],
                messages=messages,
                provider=self.provider,
            )

        return final_response

    async def run_stream(self, task: str) -> AsyncGenerator[dict, None]:
        queue: asyncio.Queue = asyncio.Queue()

        async def enqueue(event: dict):
            await queue.put(event)

        agent_task = asyncio.create_task(self.run(task, stream_callback=enqueue))

        while not agent_task.done() or not queue.empty():
            try:
                yield await asyncio.wait_for(queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

        if agent_task.exception():
            raise agent_task.exception()

    # ── AI call ────────────────────────────────────────────────────────────────

    async def _call_ai(self, messages: list, system: str) -> AIResult:
        try:
            if self.provider == "claude":
                return await self._call_anthropic(messages, system)
            return await self._call_openai_compatible(messages, system)
        except Exception as e:
            logger.error("AI call failed: %s", e)
            return AIResult(text=f"AI error: {e}")

    async def _call_anthropic(self, messages: list, system: str) -> AIResult:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        r = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            tools=ANTHROPIC_TOOLS,
            messages=messages,
        )
        text = ""
        calls = []
        for block in r.content:
            if block.type == "text":
                text = block.text
            elif block.type == "tool_use":
                calls.append(ToolCall(name=block.name, params=block.input, call_id=block.id))

        # Fallback: parse XML tags from text (Claude's visible audit trail format)
        if not calls and text:
            calls = self._parse_xml_tags(text)

        return AIResult(text=text, tool_calls=calls)

    def _parse_xml_tags(self, text: str) -> list[ToolCall]:
        """Parse <tool>name</tool><params>{}</params> from Claude responses."""
        import re
        calls = []
        for name, params_str in re.findall(
            r'<tool>(.*?)</tool>\s*<params>(.*?)</params>', text, re.DOTALL
        ):
            try:
                params = json.loads(params_str.strip())
            except json.JSONDecodeError:
                params = {}
            calls.append(ToolCall(name=name.strip(), params=params, call_id=f"xml_{len(calls)}"))
        return calls

    def _parse_tool_calls(self, text: str) -> list[tuple[str, dict]]:
        """Backwards-compatible XML tag parser — returns (name, params) tuples."""
        return [(tc.name, tc.params) for tc in self._parse_xml_tags(text)]

    def _format_tool_results(self, results: list[dict]) -> str:
        """Format tool results for display (legacy format used in tests)."""
        lines = []
        for r in results:
            tool = r["tool"]
            result = r["result"]
            if isinstance(result, dict):
                if "stdout" in result:
                    out = result["stdout"] or result.get("stderr", "")
                    lines.append(f"[{tool}] stdout:\n{out[:2000]}")
                elif "content" in result:
                    lines.append(f"[{tool}] content:\n{str(result['content'])[:2000]}")
                elif "error" in result:
                    lines.append(f"[{tool}] error: {result['error']}")
                else:
                    lines.append(f"[{tool}]: {json.dumps(result)[:500]}")
            else:
                lines.append(f"[{tool}]: {str(result)[:500]}")
        return "\n\n".join(lines)

    async def _call_openai_compatible(self, messages: list, system: str) -> AIResult:
        from openai import AsyncOpenAI

        cfg = self._provider_cfg()
        client = AsyncOpenAI(api_key=cfg["key"], base_url=cfg.get("base"))
        msgs = [{"role": "system", "content": system}] + messages

        r = await client.chat.completions.create(
            model=cfg["model"],
            messages=msgs,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        msg = r.choices[0].message
        text = msg.content or ""
        calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    params = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    params = {}
                calls.append(ToolCall(name=tc.function.name, params=params, call_id=tc.id))
        return AIResult(text=text, tool_calls=calls)

    def _provider_cfg(self) -> dict:
        cfg = PROVIDER_CONFIGS.get(self.provider, PROVIDER_CONFIGS["openai"])
        ollama_model = cfg.get("ollama_model") or os.getenv("OLLAMA_MODEL", "minimax-m2.7:cloud")

        if "ollama_model" in cfg:
            return {
                "key": "ollama",
                "base": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                "model": ollama_model,
            }
        return {
            "key": os.getenv(cfg["key_env"] or "", ""),
            "base": cfg.get("base"),
            "model": cfg["model"],
        }

    # ── Tool execution ──────────────────────────────────────────────────────────

    async def _execute_tool(self, tc: ToolCall) -> dict:
        if tc.name == "remember":
            self.memory.remember_fact(tc.params.get("key", ""), tc.params.get("value", ""))
            return {"stored": True}
        if tc.name == "recall":
            facts = self.memory.recall_fact(tc.params.get("query", ""))
            return {"facts": facts, "count": len(facts)}
        return await self.tools.execute(tc.name, tc.params)

    # ── Message formatting ──────────────────────────────────────────────────────

    def _assistant_msg(self, result: AIResult) -> dict:
        """Build assistant message with tool_calls in OpenAI format."""
        msg: dict = {"role": "assistant", "content": result.text or None}
        if result.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.call_id or f"call_{i}",
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.params)},
                }
                for i, tc in enumerate(result.tool_calls)
            ]
        return msg

    def _tool_result_msg(self, tc: ToolCall, result_str: str) -> dict:
        return {
            "role": "tool",
            "tool_call_id": tc.call_id or f"call_0",
            "content": result_str,
        }

    def _serialize_result(self, result: dict) -> str:
        if "stdout" in result:
            out = result["stdout"] or result.get("stderr", "")
            return out[:4000]
        if "content" in result:
            return str(result["content"])[:4000]
        if "error" in result:
            return f"ERROR: {result['error']}"
        return json.dumps(result)[:4000]
