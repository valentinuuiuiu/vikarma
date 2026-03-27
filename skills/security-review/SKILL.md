---
name: security-review
description: Use when adding API endpoints, handling user input, touching secrets/env vars, or adding shell/file tools. Security checklist for Python FastAPI + Vikarma agent.
origin: ECC-adapted-for-Vikarma
---

# Security Review — Vikarma Python/FastAPI

## When to Activate

- Adding new FastAPI endpoints to `server/main.py`
- Modifying shell or file tools in `VikarmaToolGateway`
- Adding new temple fallbacks in `NexusBridge`
- Handling user-provided input in the agent
- Touching environment variables or secrets

## Checklist

### 1. Secrets — CRITICAL

```python
# NEVER
ANTHROPIC_API_KEY = "sk-ant-xxxx"

# ALWAYS
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set")
```

- [ ] No hardcoded API keys, tokens, passwords
- [ ] All secrets via `os.getenv()`
- [ ] `.env` in `.gitignore`
- [ ] `.env.example` documents all required keys

### 2. Shell Tool — CRITICAL

The `shell` tool executes arbitrary commands. Guard it:

```python
# NEVER pass user input directly to shell
await gw.execute("shell", {"command": user_input})  # INJECTION RISK

# ALWAYS validate or whitelist commands
ALLOWED_COMMANDS = {"ls", "pwd", "echo", "date"}
cmd = user_input.split()[0]
if cmd not in ALLOWED_COMMANDS:
    return {"error": f"Command not allowed: {cmd}"}
```

- [ ] Agent system prompt says Ahimsa (no harmful commands)
- [ ] MAX_ITERATIONS limits runaway loops
- [ ] Shell commands logged in gateway history

### 3. File Path Traversal — HIGH

`VikarmaToolGateway._resolve()` must anchor all relative paths:

```python
def _resolve(self, path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return self.workspace / p  # anchored to workspace
```

- [ ] All file operations go through `_resolve()`
- [ ] No `../../../etc/passwd` style traversal possible
- [ ] Workspace defaults to `~`, not `/`

### 4. Calculator Temple — HIGH

Only `math` module globals allowed, no builtins:

```python
safe_globals = {"__builtins__": {}, "math": math}
safe_globals.update({k: getattr(math, k) for k in dir(math) if not k.startswith("_")})
value = eval(expression, safe_globals)
```

- [ ] `__builtins__` is `{}` (empty), not the real builtins
- [ ] Only `math.*` functions exposed
- [ ] No `import`, `open`, `exec`, `__import__` possible

### 5. FastAPI Input Validation — HIGH

```python
# NEVER trust raw request body
@app.post("/chat")
async def chat(request: Request):
    body = await request.json()  # unvalidated!
    msg = body["message"]        # KeyError risk

# ALWAYS use Pydantic models
from pydantic import BaseModel, validator

class ChatRequest(BaseModel):
    message: str
    provider: str = "claude"

    @validator("provider")
    def validate_provider(cls, v):
        allowed = {"claude", "openai", "gemini", "grok", "deepseek", "qwen"}
        if v not in allowed:
            raise ValueError(f"Unknown provider: {v}")
        return v

@app.post("/chat")
async def chat(req: ChatRequest):
    ...
```

- [ ] All endpoints use Pydantic request models
- [ ] Enums/validators on string fields
- [ ] No unvalidated string interpolation into AI prompts

### 6. Error Handling — MEDIUM

```python
# NEVER expose internals
except Exception as e:
    return {"error": str(e), "traceback": traceback.format_exc()}  # leaks internals

# ALWAYS generic message to caller, log internally
except Exception as e:
    logger.error(f"Tool {tool} failed: {e}", exc_info=True)
    return {"error": "Tool execution failed", "tool": tool}
```

- [ ] Stack traces never reach API responses
- [ ] Internal errors logged, not returned
- [ ] 500 responses are generic

### 7. Memory Safety — MEDIUM

```python
# KANMemory stores to disk — validate before storing
def remember_fact(self, key: str, value: Any, ...) -> dict:
    if not key or len(str(key)) > 500:
        return {"error": "Invalid key"}
    if len(str(value)) > 10_000:
        return {"error": "Value too large"}
```

- [ ] Fact keys/values have size limits
- [ ] No user-controlled paths in storage_dir
- [ ] Memory files in `~/.vikarma/memory/`, not project root

### 8. Web Fetch — MEDIUM

```python
# Prevent SSRF — block internal/private addresses
import ipaddress

def _is_safe_url(url: str) -> bool:
    from urllib.parse import urlparse
    host = urlparse(url).hostname
    try:
        ip = ipaddress.ip_address(host)
        return not (ip.is_private or ip.is_loopback)
    except ValueError:
        return True  # hostname, not IP — allow DNS resolution
```

- [ ] `web_fetch` doesn't hit localhost/127.0.0.1/internal
- [ ] User-provided URLs validated
- [ ] Timeout set (15s default)

## Pre-Commit Security Scan

```bash
# Run before every commit
grep -rn "api_key\s*=\s*['\"]" server/ --include="*.py" | grep -v "os.getenv\|environ\|test"
grep -rn "password\s*=\s*['\"]" server/ --include="*.py"
grep -rn "secret\s*=\s*['\"]" server/ --include="*.py"
```

Expected output: nothing. Any match = BLOCKER.
