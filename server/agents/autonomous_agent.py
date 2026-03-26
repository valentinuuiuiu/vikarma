"""
VIKARMA — Autonomous Agent
AI that thinks, plans, uses tools, and executes tasks autonomously.
Inspired by OpenClaw but sacred and free.
🔱 Om Namah Shivaya — For All Humanity
"""

import asyncio
import json
import os
import re
from typing import Optional, Callable, AsyncGenerator

from .kan_memory import KANMemory


# ── Tool definitions for AI context ───────────────────────────────────────────

AGENT_SYSTEM_PROMPT = """You are Tvaṣṭā — the autonomous AI agent in VIKARMA.
Built for all of humanity. Free. Ahimsa. Om Namah Shivaya 🔱

You have access to tools. To use a tool, respond with:
<tool>tool_name</tool>
<params>{"key": "value"}</params>

Available tools:
- shell: Run bash commands. params: {"command": "ls -la"}
- read_file: Read a file. params: {"path": "/path/to/file"}
- write_file: Write to file. params: {"path": "/path", "content": "text"}
- list_dir: List directory. params: {"path": "/home"}
- web_fetch: Fetch URL. params: {"url": "https://example.com"}
- web_search: Search web. params: {"query": "search terms"}
- python: Run Python code. params: {"code": "print('hello')"}
- find_files: Find files. params: {"pattern": "*.py", "path": "/home"}
- remember: Store fact in memory. params: {"key": "fact name", "value": "fact value"}
- recall: Search memory. params: {"query": "search term"}

Rules:
1. Think step by step before acting
2. Use tools when needed — don't just describe, DO
3. After each tool use, analyze the result and decide next step
4. Be concise in final answers
5. Ahimsa — never do harmful things
6. Max 10 tool calls per task to avoid loops

When task is complete, respond normally without tool tags."""


class VikarmaAgent:
    """
    Autonomous agent that can plan and execute multi-step tasks.
    The sacred mind that acts in the world with wisdom.
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
        self.provider = provider

    # ── Main agent loop ────────────────────────────────────────────────────

    async def run(self, task: str, stream_callback: Optional[Callable] = None) -> str:
        """
        Run agent on a task. Streams intermediate steps via callback.
        Returns final response.
        """
        # Store in memory
        self.memory.remember_now(task, role="user")

        # Build context with memory
        mem_context = self.memory.build_context_summary()
        history = self.memory.get_context_window(10)

        # Add memory context to system
        system = AGENT_SYSTEM_PROMPT
        if mem_context:
            system += f"\n\n{mem_context}"

        messages = history + [{"role": "user", "content": task}]
        iterations = 0
        final_response = ""
        response = ""

        if stream_callback:
            await stream_callback({"type": "start", "task": task})

        while iterations < self.MAX_ITERATIONS:
            iterations += 1

            # Get AI response
            response = await self._call_ai(messages, system)

            # Check for tool calls
            tool_calls = self._parse_tool_calls(response)

            if not tool_calls:
                # No tools — final answer
                final_response = response
                self.memory.remember_now(response, role="assistant")

                if stream_callback:
                    await stream_callback({"type": "final", "response": response})
                break

            # Execute tools
            tool_results = []
            for tool_name, params in tool_calls:
                if stream_callback:
                    await stream_callback({
                        "type": "tool_call",
                        "tool": tool_name,
                        "params": params
                    })

                # Special: remember/recall go to KAN memory
                if tool_name == "remember":
                    result = self.memory.remember_fact(
                        params.get("key", ""),
                        params.get("value", "")
                    )
                elif tool_name == "recall":
                    facts = self.memory.recall_fact(params.get("query", ""))
                    result = {"facts": facts, "count": len(facts)}
                else:
                    result = await self.tools.execute(tool_name, params)

                if stream_callback:
                    await stream_callback({
                        "type": "tool_result",
                        "tool": tool_name,
                        "result": result
                    })

                tool_results.append({
                    "tool": tool_name,
                    "params": params,
                    "result": result
                })

            # Add AI response + tool results to message history
            messages.append({"role": "assistant", "content": response})
            tool_summary = self._format_tool_results(tool_results)
            messages.append({"role": "user", "content": f"Tool results:\n{tool_summary}\n\nContinue with the task."})

        else:
            # Hit max iterations
            final_response = f"⚠️ Task reached max iterations ({self.MAX_ITERATIONS}). Last response:\n\n{response}"

        # Auto-save episode if long conversation
        if len(messages) > 4:
            self.memory.save_episode(
                title=task[:60],
                summary=final_response[:100],
                messages=messages,
                provider=self.provider
            )

        return final_response

    async def run_stream(self, task: str) -> AsyncGenerator[dict, None]:
        """Stream agent execution as async generator"""
        results = []

        async def collect(event: dict):
            results.append(event)

        # Run in background and yield results
        task_coro = self.run(task, stream_callback=collect)

        # Simple streaming — yield events as they come
        agent_task = asyncio.create_task(task_coro)

        while not agent_task.done():
            while results:
                yield results.pop(0)
            await asyncio.sleep(0.05)

        # Drain remaining
        while results:
            yield results.pop(0)

    # ── Tool parsing ───────────────────────────────────────────────────────

    def _parse_tool_calls(self, text: str) -> list[tuple[str, dict]]:
        """Extract tool calls from AI response"""
        calls = []
        tool_pattern = r'<tool>(.*?)</tool>\s*<params>(.*?)</params>'
        matches = re.findall(tool_pattern, text, re.DOTALL)

        for tool_name, params_str in matches:
            tool_name = tool_name.strip()
            try:
                params = json.loads(params_str.strip())
            except json.JSONDecodeError:
                params = {}
            calls.append((tool_name, params))

        return calls

    def _format_tool_results(self, results: list[dict]) -> str:
        """Format tool results for AI context"""
        lines = []
        for r in results:
            tool = r["tool"]
            result = r["result"]
            if isinstance(result, dict):
                if "stdout" in result:
                    output = result["stdout"] or result.get("stderr", "")
                    lines.append(f"[{tool}] stdout:\n{output[:2000]}")
                elif "content" in result:
                    lines.append(f"[{tool}] content:\n{result['content'][:2000]}")
                elif "error" in result:
                    lines.append(f"[{tool}] error: {result['error']}")
                else:
                    lines.append(f"[{tool}]: {json.dumps(result)[:500]}")
            else:
                lines.append(f"[{tool}]: {str(result)[:500]}")
        return "\n\n".join(lines)

    async def _call_ai(self, messages: list, system: str) -> str:
        """Call AI with full message history"""
        try:
            if self.provider == "claude":
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                r = await client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=4096,
                    system=system,
                    messages=messages
                )
                return r.content[0].text
            else:
                from openai import AsyncOpenAI
                configs = {
                    "openai": {"key": os.getenv("OPENAI_API_KEY"), "base": None, "model": "gpt-4o"},
                    "deepseek": {"key": os.getenv("DEEPSEEK_API_KEY"), "base": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
                    "qwen": {"key": os.getenv("QWEN_API_KEY"), "base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-max"},
                    "grok": {"key": os.getenv("GROK_API_KEY"), "base": "https://api.x.ai/v1", "model": "grok-beta"},
                }
                cfg = configs.get(self.provider, configs["openai"])
                client = AsyncOpenAI(api_key=cfg["key"], base_url=cfg.get("base"))
                msgs = [{"role": "system", "content": system}] + messages
                r = await client.chat.completions.create(model=cfg["model"], messages=msgs)
                return r.choices[0].message.content
        except Exception as e:
            return f"AI error: {str(e)}"
