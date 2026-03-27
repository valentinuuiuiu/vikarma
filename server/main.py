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
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import uvicorn

sys.path.insert(0, str(Path(__file__).parent))

from tools.gateway import VikarmaToolGateway, TOOL_DESCRIPTIONS
from integrations.telegram_bot import VikarmaBot
from integrations.whatsapp import WhatsAppGateway

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("vikarma")

gateway = VikarmaToolGateway()
telegram_bot: Optional[VikarmaBot] = None
whatsapp: Optional[WhatsAppGateway] = None
clients: list[WebSocket] = []
clients: list[WebSocket] = []

# Claude tools definition
CLAUDE_TOOLS = [
    {
        "name": "shell",
        "description": "Execute shell commands",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"},
                "cwd": {"type": "string", "description": "Working directory for the command"},
                "timeout": {"type": "integer", "description": "Timeout in seconds"}
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
        "description": "Execute Python code",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds"}
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
    history = history or []
    try:
        if provider == "claude":
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            messages = history + [{"role": "user", "content": message}]
            max_iterations = 5
            for _ in range(max_iterations):
                r = await client.messages.create(
                    model="claude-sonnet-4-20250514", max_tokens=4096,
                    system="You are Tvaṣṭā, Divine Craftsman in VIKARMA — free AI for all humanity. Ahimsa. 🔱 You have access to various tools to help with tasks.",
                    messages=messages,
                    tools=CLAUDE_TOOLS
                )
                
                # Check if there are tool calls
                tool_calls = [c for c in r.content if c.type == "tool_use"]
                if not tool_calls:
                    # No tool calls, return the text
                    text_content = [c for c in r.content if c.type == "text"]
                    return text_content[0].text if text_content else ""
                
                # Add the assistant's response with tool calls
                messages.append({"role": "assistant", "content": r.content})
                
                # Execute tools and add results
                for tool_call in tool_calls:
                    tool_name = tool_call.name
                    tool_input = tool_call.input
                    result = await gateway.execute(tool_name, tool_input)
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            }
                        ]
                    })
            
            # If max iterations reached, return the last response
            text_content = [c for c in r.content if c.type == "text"]
            return text_content[0].text if text_content else "Max tool iterations reached."

        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-pro")
            r = await asyncio.to_thread(model.generate_content, message)
            return r.text

        elif provider in ("openai", "gpt"):
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            r = await client.chat.completions.create(
                model="gpt-4o",
                messages=history + [{"role": "user", "content": message}]
            )
            return r.choices[0].message.content

        elif provider == "deepseek":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1")
            r = await client.chat.completions.create(
                model="deepseek-chat",
                messages=history + [{"role": "user", "content": message}]
            )
            return r.choices[0].message.content

        elif provider == "qwen":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=os.getenv("QWEN_API_KEY"), base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
            r = await client.chat.completions.create(
                model="qwen-max",
                messages=history + [{"role": "user", "content": message}]
            )
            return r.choices[0].message.content

        elif provider == "grok":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=os.getenv("GROK_API_KEY"), base_url="https://api.x.ai/v1")
            r = await client.chat.completions.create(
                model="grok-beta",
                messages=history + [{"role": "user", "content": message}]
            )
            return r.choices[0].message.content

        else:
            return f"Unknown provider: {provider}"

    except ImportError as e:
        return f"❌ Missing package: {e}. Run: pip install -r server/requirements.txt"
    except Exception as e:
        return f"❌ {provider} error: {str(e)}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_bot, whatsapp
    logger.info("🔱 VIKARMA Backend starting...")

    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if tg_token:
        telegram_bot = VikarmaBot(
            token=tg_token,
            ai_handler=chat_with_ai,
            tool_handler=lambda t, p: gateway.execute(t, p)
        )
        asyncio.create_task(telegram_bot.start())
        logger.info("✅ Telegram bot started")

    wa_token = os.getenv("WHATSAPP_TOKEN")
    if wa_token:
        whatsapp = WhatsAppGateway(
            ai_handler=chat_with_ai,
            tool_handler=lambda t, p: gateway.execute(t, p)
        )
        logger.info("✅ WhatsApp ready")

    logger.info("🕉️ Vikarma ALIVE — Om Namah Shivaya")
    yield
    if telegram_bot:
        telegram_bot.stop()


app = FastAPI(title="Vikarma", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    message: str
    provider: str = "claude"
    history: list = []

class ToolRequest(BaseModel):
    tool: str
    params: dict = {}


@app.get("/")
async def root():
    return {"name": "Vikarma", "version": "1.0.0", "status": "alive", "license": "Unlicense", "telegram": telegram_bot is not None, "whatsapp": whatsapp is not None}

@app.get("/health")
async def health():
    return {"status": "alive", "message": "🔱 Om Namah Shivaya"}

@app.post("/chat")
async def chat(req: ChatRequest):
    response = await chat_with_ai(req.message, req.provider, req.history)
    return {"response": response, "provider": req.provider}

@app.post("/tool")
async def execute_tool(req: ToolRequest):
    return await gateway.execute(req.tool, req.params)

@app.get("/tools")
async def list_tools():
    return {"tools": TOOL_DESCRIPTIONS}

@app.get("/temples")
async def temples():
    return {"total": 64, "status": "ready", "repo": "https://github.com/valentinuuiuiu/nexus-bhairava-temples"}

@app.get("/webhook/whatsapp")
async def wa_verify(hub_mode: str = Query(None, alias="hub.mode"), hub_token: str = Query(None, alias="hub.verify_token"), hub_challenge: str = Query(None, alias="hub.challenge")):
    if not whatsapp:
        raise HTTPException(400, "WhatsApp not configured")
    challenge = whatsapp.verify_webhook(hub_mode, hub_token, hub_challenge)
    if challenge:
        return PlainTextResponse(challenge)
    raise HTTPException(403, "Verification failed")

@app.post("/webhook/whatsapp")
async def wa_webhook(request: Request):
    if not whatsapp:
        return {"status": "disabled"}
    return await whatsapp.handle_webhook(await request.json())

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    try:
        while True:
            data = json.loads(await ws.receive_text())
            action = data.get("action", "")
            if action == "chat":
                response = await chat_with_ai(data.get("message", ""), data.get("provider", "claude"), data.get("history", []))
                await ws.send_text(json.dumps({"type": "chat", "response": response}))
            elif action == "tool":
                result = await gateway.execute(data.get("tool", ""), data.get("params", {}))
                await ws.send_text(json.dumps({"type": "tool_result", "result": result}))
            elif action == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        clients.remove(ws)


if __name__ == "__main__":
    print("🔱 VIKARMA BACKEND AWAKENING...")
    print("📡 http://127.0.0.1:8765")
    print("🕉️ Om Namah Shivaya — For All Humanity")
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
