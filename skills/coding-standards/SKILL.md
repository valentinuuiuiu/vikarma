---
name: coding-standards
description: Python/FastAPI coding standards for the Vikarma codebase. Use when writing new code, reviewing existing code, or onboarding.
origin: ECC-adapted-for-Vikarma
---

# Coding Standards — Vikarma Python

## Core Principles

1. **Readability first** — code is read more than written
2. **Async everywhere** — all I/O must be `async/await`
3. **Return dicts** — all tool methods return `dict`
4. **Ahimsa** — no harmful, deceptive, or manipulative code
5. **YAGNI** — don't build what isn't needed yet

## Python Standards

### Naming

```python
# Functions: verb_noun, lowercase_snake
async def execute_tool(tool: str, params: dict) -> dict: ...
async def remember_fact(key: str, value: Any) -> dict: ...

# Classes: PascalCase
class VikarmaToolGateway: ...
class KANMemory: ...

# Constants: UPPER_SNAKE
MAX_ITERATIONS = 10
CACHE_DURATION = 30

# Private methods: _underscore
def _resolve(self, path: str) -> Path: ...
def _cache_valid(self, key: str) -> bool: ...
```

### Type Hints — Required on All Public Methods

```python
# ALWAYS
async def shell(self, command: str, cwd: str = None, timeout: int = None) -> dict:
    ...

# NEVER
async def shell(self, command, cwd=None, timeout=None):
    ...
```

### Async Pattern

```python
# ALWAYS async for I/O
async def web_fetch(self, url: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        return {"status": r.status_code, "content": r.text[:self.MAX_OUTPUT]}

# NEVER blocking I/O in async context
async def bad_fetch(self, url: str) -> dict:
    import requests
    r = requests.get(url)  # BLOCKS the event loop!
    return {"content": r.text}
```

### Error Handling

```python
# Tool methods: always return error dict, never raise to caller
async def execute(self, tool: str, params: dict) -> dict:
    try:
        result = await handler(**params)
        return result
    except Exception as e:
        logger.error(f"Tool {tool} failed: {e}", exc_info=True)
        return {"error": str(e), "tool": tool}  # caller sees error key

# Internal methods: may raise, let execute() catch
async def _do_thing(self) -> str:
    raise ValueError("something went wrong")  # execute() will catch
```

### Tool Return Format

Every tool must return a `dict`. Standard keys:

```python
# Success
{"success": True, "data": ..., "key": value}

# File content
{"content": "...", "size": 123, "lines": 10, "truncated": False}

# Shell result
{"stdout": "...", "stderr": "...", "returncode": 0, "success": True}

# Error
{"error": "description of what went wrong", "tool": "tool_name"}
```

### File / Function Size Limits

| Thing | Limit |
|-------|-------|
| Function body | 50 lines |
| Class file | 400 lines |
| Tool result string | `MAX_OUTPUT = 8000` chars |

### Module Structure

```python
"""
Module docstring — one line description.
🔱 Om Namah Shivaya
"""

import asyncio       # stdlib first
import json
import os

import httpx          # third-party second

from .kan_memory import KANMemory  # local last

logger = logging.getLogger(__name__)  # module-level logger

CONSTANT = value  # module-level constants

class MyClass:     # class definitions
    ...

async def helper() -> dict:  # module-level helpers last
    ...
```

## Anti-Patterns to Avoid

```python
# NEVER: silent except
try:
    do_thing()
except:
    pass  # hides bugs

# ALWAYS: specific exception + log
try:
    do_thing()
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
    return {"error": str(e)}
```

```python
# NEVER: mutable default argument
def func(items=[]):     # shared across calls!
    items.append(1)

# ALWAYS: None default
def func(items=None):
    items = items or []
    items.append(1)
```

```python
# NEVER: star import
from server.nexus_bridge import *

# ALWAYS: explicit
from server.nexus_bridge import NexusBridge, TEMPLE_PORTS
```

## FastAPI Endpoint Pattern

```python
from pydantic import BaseModel

class ToolRequest(BaseModel):
    tool: str
    params: dict = {}

@app.post("/tool")
async def run_tool(req: ToolRequest):
    result = await gateway.execute(req.tool, req.params)
    return result
```

Never accept raw `Request` and parse `.json()` manually.
Always use Pydantic models for request validation.
