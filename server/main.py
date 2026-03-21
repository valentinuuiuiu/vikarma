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


async def chat_with_ai(message: str, provider: str = "claude", history: list = None) -> str:
    history = history or []
    try:
        if provider == "claude":
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            r = await client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=4096,
                system="You are Tvaṣṭā, Divine Craftsman in VIKARMA — free AI for all humanity. Ahimsa. 🔱",
                messages=history + [{"role": "user", "content": message}]
            )
            return r.content[0].text

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
