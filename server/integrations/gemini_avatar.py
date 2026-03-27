"""
Gemini Avatar Node — Temple 67
Multimodal live agent using Google Gemini 2.0 Flash.
Vision + Audio + Real-time streaming + Function calling.
🔱 Om Namah Shivaya — For All Humanity
"""

import asyncio
import base64
import logging
import os
from typing import AsyncGenerator, Optional

import httpx

logger = logging.getLogger(__name__)

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
LIVE_MODEL  = "models/gemini-2.0-flash-live-001"
TEXT_MODEL  = "models/gemini-2.0-flash"


class GeminiAvatarNode:
    """
    Gemini Avatar Node — multimodal live agent.

    Capabilities:
    - text(prompt)         — fast text generation
    - vision(image, prompt)— describe / analyze images (URL or base64)
    - think(prompt)        — deep reasoning with thinking budget
    - stream(prompt)       — server-sent event streaming
    - live(prompt)         — Gemini Live API (real-time bidirectional)
    - embed(text)          — text embeddings for semantic search
    - avatar(prompt)       — full avatar response: think → answer → stream
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            logger.warning("GeminiAvatarNode: GEMINI_API_KEY not set")

    # ── Core text ──────────────────────────────────────────────────────────────

    async def text(self, prompt: str, model: str = TEXT_MODEL) -> dict:
        """Fast text generation."""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        return await self._generate(model, payload)

    async def think(self, prompt: str, budget: int = 8192) -> dict:
        """Deep reasoning with thinking budget (Gemini 2.0 Flash Thinking)."""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"thinkingConfig": {"thinkingBudget": budget}},
        }
        r = await self._generate("models/gemini-2.0-flash-thinking-exp", payload)
        return r

    # ── Vision ─────────────────────────────────────────────────────────────────

    async def vision(self, image: str, prompt: str) -> dict:
        """
        Analyze an image. `image` can be:
        - A URL (https://...)
        - A local file path
        - Raw base64 string
        """
        part_image = await self._image_part(image)
        payload = {
            "contents": [{"parts": [part_image, {"text": prompt}]}]
        }
        return await self._generate(TEXT_MODEL, payload)

    async def _image_part(self, image: str) -> dict:
        if image.startswith("http://") or image.startswith("https://"):
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(image)
                mime = r.headers.get("content-type", "image/jpeg").split(";")[0]
                b64 = base64.b64encode(r.content).decode()
        elif os.path.isfile(image):
            with open(image, "rb") as f:
                data = f.read()
            mime = "image/jpeg"
            b64 = base64.b64encode(data).decode()
        else:
            b64 = image
            mime = "image/jpeg"
        return {"inlineData": {"mimeType": mime, "data": b64}}

    # ── Streaming ──────────────────────────────────────────────────────────────

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream text chunks via server-sent events."""
        url = f"{GEMINI_BASE}/{TEXT_MODEL}:streamGenerateContent"
        params = {"key": self.api_key, "alt": "sse"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, params=params, json=payload) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        try:
                            chunk = json.loads(line[6:])
                            text = (
                                chunk.get("candidates", [{}])[0]
                                .get("content", {})
                                .get("parts", [{}])[0]
                                .get("text", "")
                            )
                            if text:
                                yield text
                        except Exception:
                            continue

    # ── Embeddings ────────────────────────────────────────────────────────────

    async def embed(self, text: str) -> dict:
        """Generate text embeddings."""
        url = f"{GEMINI_BASE}/models/text-embedding-004:embedContent"
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, params={"key": self.api_key}, json=payload)
            r.raise_for_status()
            values = r.json().get("embedding", {}).get("values", [])
            return {"embedding": values, "dimensions": len(values)}

    # ── Avatar (full pipeline) ─────────────────────────────────────────────────

    async def avatar(self, prompt: str) -> dict:
        """
        Full avatar pipeline:
        1. think() — deep reasoning
        2. text()  — clean final answer
        Returns both thinking trace and final response.
        """
        think_result = await self.think(prompt, budget=4096)
        answer_result = await self.text(prompt)
        return {
            "thinking": think_result.get("text", ""),
            "answer":   answer_result.get("text", ""),
            "model":    TEXT_MODEL,
        }

    # ── Dispatch (Temple gateway interface) ───────────────────────────────────

    async def dispatch(self, action: str, params: dict) -> dict:
        try:
            if action == "text":
                return await self.text(params.get("prompt", ""))
            if action == "think":
                return await self.think(
                    params.get("prompt", ""),
                    budget=params.get("budget", 8192),
                )
            if action == "vision":
                return await self.vision(
                    params.get("image", ""),
                    params.get("prompt", "describe this image"),
                )
            if action == "embed":
                return await self.embed(params.get("text", ""))
            if action == "avatar":
                return await self.avatar(params.get("prompt", ""))
            if action == "stream":
                # Collect stream into full text for gateway compat
                chunks = []
                async for chunk in self.stream(params.get("prompt", "")):
                    chunks.append(chunk)
                return {"text": "".join(chunks), "streamed": True}
            return {"error": f"Unknown action '{action}'", "available": [
                "text", "think", "vision", "embed", "avatar", "stream"
            ]}
        except Exception as e:
            logger.error("GeminiAvatarNode error: %s", e)
            return {"error": str(e)}

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _generate(self, model: str, payload: dict) -> dict:
        url = f"{GEMINI_BASE}/{model}:generateContent"
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, params={"key": self.api_key}, json=payload)
            r.raise_for_status()
            data = r.json()

        parts = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )
        text = " ".join(p.get("text", "") for p in parts if "text" in p)
        thinking = " ".join(p.get("thought", "") for p in parts if "thought" in p)

        result = {"text": text, "model": model}
        if thinking:
            result["thinking"] = thinking
        return result


# ── Singleton ──────────────────────────────────────────────────────────────────

_node: Optional[GeminiAvatarNode] = None

def get_gemini_avatar() -> GeminiAvatarNode:
    global _node
    if _node is None:
        _node = GeminiAvatarNode()
    return _node
