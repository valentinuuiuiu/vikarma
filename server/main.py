"""
VIKARMA — Python Backend Server
Sacred core that connects all 64 Bhairava Temples

🔱 Om Namah Shivaya
The Vikarma Team
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(
    title="Vikarma Backend",
    description="Sacred core for 64 Bhairava Temples 🔱",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "app://.", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connected websocket clients
clients: list[WebSocket] = []


# ── WebSocket for real-time communication ────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            response = await handle_message(msg)
            await websocket.send_text(json.dumps(response))
    except WebSocketDisconnect:
        clients.remove(websocket)


async def handle_message(msg: dict) -> dict:
    """Route messages to appropriate handlers"""
    action = msg.get("action", "")

    if action == "chat":
        return await handle_chat(msg)
    elif action == "temple_status":
        return await get_temple_status()
    elif action == "temple_awaken":
        return await awaken_temple(msg.get("temple_number"))
    elif action == "memory_store":
        return await store_memory(msg.get("key"), msg.get("value"))
    elif action == "memory_recall":
        return await recall_memory(msg.get("query"))
    else:
        return {"error": f"Unknown action: {action}"}


# ── Chat handler ─────────────────────────────────────────────────────────────

async def handle_chat(msg: dict) -> dict:
    """Route chat to appropriate AI provider"""
    provider = msg.get("provider", "claude")
    message = msg.get("message", "")
    history = msg.get("history", [])

    try:
        if provider == "claude":
            return await chat_claude(message, history)
        elif provider == "gemini":
            return await chat_gemini(message, history)
        elif provider == "openai":
            return await chat_openai(message, history)
        else:
            return {"error": f"Unknown provider: {provider}"}
    except Exception as e:
        return {"error": str(e), "provider": provider}


async def chat_claude(message: str, history: list) -> dict:
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        messages = history + [{"role": "user", "content": message}]
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system="You are Tvaṣṭā, the Divine Craftsman — part of the Vikarma AI system built for humanity with Ahimsa. Om Namah Shivaya 🔱",
            messages=messages
        )
        return {
            "provider": "claude",
            "response": response.content[0].text,
            "model": response.model
        }
    except Exception as e:
        return {"error": str(e), "provider": "claude"}


async def chat_gemini(message: str, history: list) -> dict:
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-pro")
        response = await asyncio.to_thread(model.generate_content, message)
        return {
            "provider": "gemini",
            "response": response.text,
            "model": "gemini-pro"
        }
    except Exception as e:
        return {"error": str(e), "provider": "gemini"}


async def chat_openai(message: str, history: list) -> dict:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        messages = history + [{"role": "user", "content": message}]
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return {
            "provider": "openai",
            "response": response.choices[0].message.content,
            "model": response.model
        }
    except Exception as e:
        return {"error": str(e), "provider": "openai"}


# ── Temple status ─────────────────────────────────────────────────────────────

async def get_temple_status() -> dict:
    return {
        "temples_total": 64,
        "temples_awake": 0,
        "message": "🔱 64 Bhairava Guardians stand ready",
        "status": "dormant"
    }


async def awaken_temple(temple_number: Optional[int]) -> dict:
    if not temple_number:
        return {"error": "Temple number required"}
    return {
        "temple": temple_number,
        "status": "awakening",
        "message": f"🏛️ Temple {temple_number} awakening..."
    }


# ── Memory (KAN) ──────────────────────────────────────────────────────────────

memory_store = {}

async def store_memory(key: str, value: str) -> dict:
    memory_store[key] = value
    return {"stored": True, "key": key}

async def recall_memory(query: str) -> dict:
    # Simple keyword search — can be upgraded to vector search
    results = {k: v for k, v in memory_store.items() if query.lower() in k.lower() or query.lower() in v.lower()}
    return {"results": results, "count": len(results)}


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "alive",
        "message": "🔱 Vikarma Backend — Om Namah Shivaya",
        "temples": 64,
        "memory_entries": len(memory_store)
    }


@app.get("/")
async def root():
    return {
        "name": "Vikarma",
        "version": "1.0.0",
        "message": "Free AI for All Humanity 🔱",
        "license": "Unlicense"
    }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🔱 VIKARMA BACKEND AWAKENING...")
    print("🏛️ 64 Bhairava Temples ready")
    print("🕉️ Om Namah Shivaya — For All Humanity")
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
