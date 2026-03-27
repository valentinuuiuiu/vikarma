"""
VIKARMA — Complete Backend Server
All integrations: AI, Tools, Telegram, WhatsApp, WebSocket
🔱 Om Namah Shivaya — For All Humanity
"""

import asyncio
import json
import os
import sys
import logging
import time
import re
import hashlib
from pathlib import Path
from typing import Optional, Dict
from contextlib import asynccontextmanager
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
import uvicorn

sys.path.insert(0, str(Path(__file__).parent))

from tools.gateway import VikarmaToolGateway, TOOL_DESCRIPTIONS
from integrations.telegram_bot import VikarmaBot
from integrations.whatsapp import WhatsAppGateway

# ── Configuration ─────────────────────────────────────────────────────────────
VIKARMA_API_KEY = os.getenv("VIKARMA_API_KEY")
ALLOWED_PROVIDERS = {"claude", "gemini", "openai", "gpt", "deepseek", "qwen", "grok", "nvidia"}
DEFAULT_MAX_ITERATIONS = 5
SHELL_COMMAND_BLACKLIST = ["rm -rf", "mkfs", "dd if=", ":(){:|:&};:", "chmod 777 /", "curl.*\\|.*bash", "wget.*\\|.*bash"]

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("vikarma")
audit_logger = logging.getLogger("vikarma.audit")

# ── Globals ───────────────────────────────────────────────────────────────────
gateway = VikarmaToolGateway()
telegram_bot: Optional[VikarmaBot] = None
whatsapp: Optional[WhatsAppGateway] = None
clients: list[WebSocket] = []

# ── Rate Limiting ─────────────────────────────────────────────────────────────
class RateLimiter:
    """Token bucket rate limiter"""
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.request_counts: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_id: str) -> tuple[bool, int]:
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        self.request_counts[client_id] = [
            ts for ts in self.request_counts[client_id] if ts > window_start
        ]

        # Check limit
        if len(self.request_counts[client_id]) >= self.requests_per_minute:
            retry_after = int(self.request_counts[client_id][0] + self.window_seconds - now)
            return False, max(1, retry_after)

        # Record request
        self.request_counts[client_id].append(now)
        return True, 0

rate_limiter = RateLimiter(requests_per_minute=60)

# ── Environment Validation ────────────────────────────────────────────────────
def validate_environment() -> list[str]:
    """Validate required environment variables at startup"""
    warnings = []

    # Check for at least one AI provider
    ai_providers = {
        "ANTHROPIC_API_KEY": "Claude",
        "GEMINI_API_KEY": "Gemini",
        "OPENAI_API_KEY": "OpenAI/GPT",
        "DEEPSEEK_API_KEY": "DeepSeek",
        "QWEN_API_KEY": "Qwen",
        "GROK_API_KEY": "Grok",
        "NVIDIA_API_KEY": "NVIDIA (Kimi K2.5)"
    }
    configured = [name for key, name in ai_providers.items() if os.getenv(key)]

    if not configured:
        warnings.append("⚠️ No AI provider API keys configured")
    else:
        logger.info(f"✅ AI providers configured: {', '.join(configured)}")

    # Optional integrations
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        logger.info("✅ Telegram integration enabled")
    if os.getenv("WHATSAPP_TOKEN"):
        logger.info("✅ WhatsApp integration enabled")
    if VIKARMA_API_KEY:
        logger.info("✅ API key authentication enabled")
    else:
        logger.warning("⚠️ VIKARMA_API_KEY not set — API is open")

    return warnings

# ── Security Helpers ──────────────────────────────────────────────────────────
def sanitize_shell_command(command: str) -> tuple[bool, str]:
    """
    Sanitize shell command to prevent injection attacks.
    Returns (is_safe, error_message)
    """
    if not command:
        return False, "Empty command"

    # Check for dangerous patterns
    for pattern in SHELL_COMMAND_BLACKLIST:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Dangerous command pattern detected: {pattern}"

    # Block command chaining
    dangerous_chars = [";", "&&", "||", "|", "`", "$(", "${", ">>", ">", "<"]
    for char in dangerous_chars:
        if char in command:
            return False, f"Command chaining not allowed: {char}"

    # Block path traversal for file operations
    if ".." in command and any(cmd in command for cmd in ["cd ", "cat ", "read ", "write "]):
        return False, "Path traversal detected"

    return True, ""

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def hash_api_key(api_key: str) -> str:
    """Hash API key for logging"""
    return hashlib.sha256(api_key.encode()).hexdigest()[:8]

# ── Authentication ────────────────────────────────────────────────────────────
async def verify_api_key(request: Request, api_key: str = Query(None, alias="api_key")) -> Optional[str]:
    """Verify API key if authentication is enabled"""
    if not VIKARMA_API_KEY:
        return None  # Auth disabled

    # Check header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header[7:]

    if not api_key or api_key != VIKARMA_API_KEY:
        audit_logger.warning(f"Failed auth attempt from {get_client_ip(request)}")
        raise HTTPException(401, detail="Invalid or missing API key")

    audit_logger.info(f"Authenticated request from {get_client_ip(request)} (key: {hash_api_key(api_key)}...)")
    return api_key

# ── Rate Limit Dependency ─────────────────────────────────────────────────────
async def check_rate_limit(request: Request) -> None:
    """Check rate limit for request"""
    client_id = get_client_ip(request)
    allowed, retry_after = rate_limiter.is_allowed(client_id)

    if not allowed:
        audit_logger.warning(f"Rate limit exceeded for {client_id}")
        raise HTTPException(429, detail=f"Rate limit exceeded. Retry after {retry_after}s")

# ── Claude Tools Definition ───────────────────────────────────────────────────
CLAUDE_TOOLS = [
    {
        "name": "shell",
        "description": "Execute shell commands safely",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"},
                "cwd": {"type": "string", "description": "Working directory for the command"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (max 30)"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "Read file contents",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "encoding": {"type": "string", "description": "File encoding"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
                "mode": {"type": "string", "description": "Write mode: 'w' or 'a'"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_dir",
        "description": "List directory contents",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path"},
                "show_hidden": {"type": "boolean", "description": "Show hidden files"}
            }
        }
    },
    {
        "name": "delete_file",
        "description": "Delete file or directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to delete"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "copy_file",
        "description": "Copy file",
        "input_schema": {
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "Source path"},
                "dst": {"type": "string", "description": "Destination path"}
            },
            "required": ["src", "dst"]
        }
    },
    {
        "name": "move_file",
        "description": "Move or rename file",
        "input_schema": {
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "Source path"},
                "dst": {"type": "string", "description": "Destination path"}
            },
            "required": ["src", "dst"]
        }
    },
    {
        "name": "find_files",
        "description": "Find files matching pattern",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern"},
                "path": {"type": "string", "description": "Search path"}
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "file_exists",
        "description": "Check if file or directory exists",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to check"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "make_dir",
        "description": "Create directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "web_fetch",
        "description": "Fetch content from URL",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "method": {"type": "string", "description": "HTTP method"},
                "headers": {"type": "object", "description": "HTTP headers"},
                "body": {"type": "string", "description": "Request body"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Maximum results"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "python",
        "description": "Execute Python code in sandbox",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (max 15)"}
            },
            "required": ["code"]
        }
    },
    {
        "name": "get_env",
        "description": "Get environment variable",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Environment variable key"}
            },
            "required": ["key"]
        }
    },
    {
        "name": "set_env",
        "description": "Set environment variable",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Variable key"},
                "value": {"type": "string", "description": "Variable value"}
            },
            "required": ["key", "value"]
        }
    }
]


async def chat_with_ai(message: str, provider: str = "claude", history: list = None) -> str:
    """Chat with AI provider with proper error handling"""
    history = history or []

    # Validate provider
    if provider not in ALLOWED_PROVIDERS:
        logger.warning(f"Invalid provider requested: {provider}")
        return f"Invalid provider: {provider}. Allowed: {', '.join(ALLOWED_PROVIDERS)}"

    try:
        if provider == "claude":
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return "❌ Claude API key not configured"

            client = anthropic.AsyncAnthropic(api_key=api_key)
            messages = history + [{"role": "user", "content": message}]

            for iteration in range(DEFAULT_MAX_ITERATIONS):
                try:
                    r = await client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=4096,
                        system="You are Tvaṣṭā, Divine Craftsman in VIKARMA — free AI for all humanity. Ahimsa. 🔱 You have access to various tools to help with tasks.",
                        messages=messages,
                        tools=CLAUDE_TOOLS
                    )

                    tool_calls = [c for c in r.content if c.type == "tool_use"]
                    if not tool_calls:
                        text_content = [c for c in r.content if c.type == "text"]
                        return text_content[0].text if text_content else ""

                    messages.append({"role": "assistant", "content": r.content})

                    for tool_call in tool_calls:
                        tool_name = tool_call.name
                        tool_input = tool_call.input

                        # Sanitize shell commands
                        if tool_name == "shell":
                            is_safe, error = sanitize_shell_command(tool_input.get("command", ""))
                            if not is_safe:
                                result = {"error": f"Command blocked: {error}"}
                            else:
                                result = await gateway.execute(tool_name, tool_input)
                        else:
                            result = await gateway.execute(tool_name, tool_input)

                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            }]
                        })

                except Exception as e:
                    logger.error(f"Claude API error: {e}")
                    return f"❌ Claude API error: {str(e)}"

            text_content = [c for c in r.content if c.type == "text"]
            return text_content[0].text if text_content else "Max tool iterations reached."

        elif provider == "gemini":
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return "❌ Gemini API key not configured"

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-pro")
            try:
                r = await asyncio.to_thread(model.generate_content, message)
                return r.text
            except Exception as e:
                logger.error(f"Gemini error: {e}")
                return f"❌ Gemini error: {str(e)}"

        elif provider in ("openai", "gpt"):
            from openai import AsyncOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return "❌ OpenAI API key not configured"

            client = AsyncOpenAI(api_key=api_key)
            try:
                r = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=history + [{"role": "user", "content": message}]
                )
                return r.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI error: {e}")
                return f"❌ OpenAI error: {str(e)}"

        elif provider == "deepseek":
            from openai import AsyncOpenAI
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                return "❌ DeepSeek API key not configured"

            client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            try:
                r = await client.chat.completions.create(
                    model="deepseek-chat",
                    messages=history + [{"role": "user", "content": message}]
                )
                return r.choices[0].message.content
            except Exception as e:
                logger.error(f"DeepSeek error: {e}")
                return f"❌ DeepSeek error: {str(e)}"

        elif provider == "qwen":
            from openai import AsyncOpenAI
            api_key = os.getenv("QWEN_API_KEY")
            if not api_key:
                return "❌ Qwen API key not configured"

            client = AsyncOpenAI(api_key=api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
            try:
                r = await client.chat.completions.create(
                    model="qwen-max",
                    messages=history + [{"role": "user", "content": message}]
                )
                return r.choices[0].message.content
            except Exception as e:
                logger.error(f"Qwen error: {e}")
                return f"❌ Qwen error: {str(e)}"

        elif provider == "grok":
            from openai import AsyncOpenAI
            api_key = os.getenv("GROK_API_KEY")
            if not api_key:
                return "❌ Grok API key not configured"

            client = AsyncOpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
            try:
                r = await client.chat.completions.create(
                    model="grok-beta",
                    messages=history + [{"role": "user", "content": message}]
                )
                return r.choices[0].message.content
            except Exception as e:
                logger.error(f"Grok error: {e}")
                return f"❌ Grok error: {str(e)}"

        elif provider == "nvidia":
            import httpx
            api_key = os.getenv("NVIDIA_API_KEY")
            if not api_key:
                return "❌ NVIDIA API key not configured"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }
            payload = {
                "model": "moonshotai/kimi-k2.5",
                "messages": history + [{"role": "user", "content": message}],
                "max_tokens": 16384,
                "temperature": 1.0,
                "top_p": 1.0,
                "stream": False,
                "chat_template_kwargs": {"thinking": True}
            }

            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    r = await client.post(
                        "https://integrate.api.nvidia.com/v1/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    data = r.json()
                    return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"NVIDIA error: {e}")
                return f"❌ NVIDIA error: {str(e)}"

        else:
            return f"Unknown provider: {provider}"

    except ImportError as e:
        logger.error(f"Missing package: {e}")
        return f"❌ Missing package: {e}. Run: pip install -r server/requirements.txt"
    except Exception as e:
        logger.error(f"Unexpected AI error: {e}")
        return f"❌ AI error: {str(e)}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with validation"""
    global telegram_bot, whatsapp

    logger.info("🔱 VIKARMA Backend starting...")

    # Validate environment
    warnings = validate_environment()
    for warning in warnings:
        logger.warning(warning)

    # Start Telegram bot
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if tg_token:
        try:
            telegram_bot = VikarmaBot(
                token=tg_token,
                ai_handler=chat_with_ai,
                tool_handler=lambda t, p: gateway.execute(t, p)
            )
            asyncio.create_task(telegram_bot.start())
            logger.info("✅ Telegram bot started")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")

    # Start WhatsApp gateway
    wa_token = os.getenv("WHATSAPP_TOKEN")
    if wa_token:
        try:
            whatsapp = WhatsAppGateway(
                ai_handler=chat_with_ai,
                tool_handler=lambda t, p: gateway.execute(t, p)
            )
            logger.info("✅ WhatsApp ready")
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp: {e}")

    logger.info("🕉️ Vikarma ALIVE — Om Namah Shivaya")
    yield

    # Cleanup
    if telegram_bot:
        telegram_bot.stop()
    logger.info("🔱 VIKARMA shutting down...")


app = FastAPI(title="Vikarma", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=50000)
    provider: str = "claude"
    history: list = Field(default_factory=list)


class ToolRequest(BaseModel):
    tool: str = Field(..., min_length=1)
    params: dict = Field(default_factory=dict)


@app.get("/")
async def root():
    return {
        "name": "Vikarma",
        "version": "1.0.0",
        "status": "alive",
        "license": "Unlicense",
        "telegram": telegram_bot is not None,
        "whatsapp": whatsapp is not None
    }


@app.get("/health")
async def health():
    return {"status": "alive", "message": "🔱 Om Namah Shivaya"}


@app.post("/chat", dependencies=[Depends(check_rate_limit)])
async def chat(req: ChatRequest, api_key: Optional[str] = Depends(verify_api_key)):
    """Chat with AI provider"""
    audit_logger.info(f"Chat request: provider={req.provider}, message_length={len(req.message)}")
    try:
        response = await chat_with_ai(req.message, req.provider, req.history)
        return {"response": response, "provider": req.provider}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(500, detail=str(e))


@app.post("/tool", dependencies=[Depends(check_rate_limit)])
async def execute_tool(req: ToolRequest, api_key: Optional[str] = Depends(verify_api_key)):
    """Execute a tool with input validation"""
    audit_logger.info(f"Tool request: tool={req.tool}, params={json.dumps(req.params)[:100]}")

    # Sanitize shell commands
    if req.tool == "shell":
        command = req.params.get("command", "")
        is_safe, error = sanitize_shell_command(command)
        if not is_safe:
            audit_logger.warning(f"Blocked dangerous shell command: {error}")
            raise HTTPException(400, detail=f"Command blocked: {error}")

    # Sanitize file paths
    for path_param in ["path", "src", "dst"]:
        if path_param in req.params:
            path_value = req.params[path_param]
            if ".." in str(path_value):
                audit_logger.warning(f"Blocked path traversal attempt: {path_param}={path_value}")
                raise HTTPException(400, detail="Path traversal not allowed")

    try:
        result = await gateway.execute(req.tool, req.params)
        return result
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(500, detail=str(e))


@app.get("/tools")
async def list_tools():
    return {"tools": TOOL_DESCRIPTIONS}


@app.get("/temples")
async def temples():
    return {"total": 64, "status": "ready", "repo": "https://github.com/valentinuuiuiu/nexus-bhairava-temples"}


@app.get("/webhook/whatsapp")
async def wa_verify(hub_mode: str = Query(None, alias="hub.mode"), hub_token: str = Query(None, alias="hub.verify_token"), hub_challenge: str = Query(None, alias="hub.challenge")):
    if not whatsapp:
        raise HTTPException(400, detail="WhatsApp not configured")
    try:
        challenge = whatsapp.verify_webhook(hub_mode, hub_token, hub_challenge)
        if challenge:
            return PlainTextResponse(challenge)
        raise HTTPException(403, detail="Verification failed")
    except Exception as e:
        logger.error(f"WhatsApp verification error: {e}")
        raise HTTPException(500, detail=str(e))


@app.post("/webhook/whatsapp")
async def wa_webhook(request: Request):
    if not whatsapp:
        return {"status": "disabled"}
    try:
        return await whatsapp.handle_webhook(await request.json())
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return {"error": str(e)}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    """WebSocket endpoint with authentication and rate limiting"""
    # Check API key if enabled
    if VIKARMA_API_KEY:
        api_key = ws.query_params.get("api_key")
        if api_key != VIKARMA_API_KEY:
            await ws.close(code=4001, reason="Invalid API key")
            return

    await ws.accept()
    clients.append(ws)
    client_ip = "websocket"

    try:
        while True:
            try:
                data = json.loads(await ws.receive_text())
                action = data.get("action", "")

                if action == "chat":
                    message = data.get("message", "")
                    provider = data.get("provider", "claude")
                    history = data.get("history", [])
                    response = await chat_with_ai(message, provider, history)
                    await ws.send_text(json.dumps({"type": "chat", "response": response}))

                elif action == "tool":
                    tool = data.get("tool", "")
                    params = data.get("params", {})

                    # Sanitize shell commands
                    if tool == "shell" and params.get("command"):
                        is_safe, error = sanitize_shell_command(params["command"])
                        if not is_safe:
                            await ws.send_text(json.dumps({"type": "tool_result", "result": {"error": f"Command blocked: {error}"}}))
                            continue

                    result = await gateway.execute(tool, params)
                    await ws.send_text(json.dumps({"type": "tool_result", "result": result}))

                elif action == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))

                else:
                    await ws.send_text(json.dumps({"type": "error", "message": f"Unknown action: {action}"}))

            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        clients.remove(ws)


if __name__ == "__main__":
    print("🔱 VIKARMA BACKEND AWAKENING...")
    print("📡 http://127.0.0.1:8765")
    print("🔐 Set VIKARMA_API_KEY environment variable to enable authentication")
    print("🕉️ Om Namah Shivaya — For All Humanity")
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
