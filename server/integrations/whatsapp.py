"""
VIKARMA — WhatsApp Integration
Via WhatsApp Business Cloud API (Meta)
🔱 Om Namah Shivaya — For All Humanity
"""

import os
import json
import logging
from typing import Optional, Callable
import httpx

logger = logging.getLogger("vikarma.whatsapp")


class WhatsAppGateway:
    """
    WhatsApp Business Cloud API integration.
    Receive and send messages via WhatsApp.

    Setup:
    1. Create Meta Developer account
    2. Create WhatsApp Business App
    3. Get WHATSAPP_TOKEN and WHATSAPP_PHONE_ID
    4. Set webhook URL to your Vikarma server /webhook/whatsapp
    """

    API_BASE = "https://graph.facebook.com/v18.0"

    def __init__(
        self,
        token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        verify_token: Optional[str] = None,
        ai_handler: Optional[Callable] = None,
        tool_handler: Optional[Callable] = None,
    ):
        self.token = token or os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_ID")
        self.verify_token = verify_token or os.getenv("WHATSAPP_VERIFY_TOKEN", "vikarma_sacred")
        self.ai_handler = ai_handler
        self.tool_handler = tool_handler

    # ── Send Messages ──────────────────────────────────────────────────────

    async def send_text(self, to: str, text: str) -> dict:
        """Send text message"""
        return await self._send({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text[:4096]},
        })

    async def send_template(self, to: str, template_name: str, language: str = "en_US") -> dict:
        """Send template message"""
        return await self._send({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {"name": template_name, "language": {"code": language}},
        })

    async def send_interactive(self, to: str, body: str, buttons: list[str]) -> dict:
        """Send interactive button message"""
        return await self._send({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": f"btn_{i}", "title": btn[:20]}}
                        for i, btn in enumerate(buttons[:3])
                    ]
                }
            }
        })

    async def _send(self, payload: dict) -> dict:
        """Send via WhatsApp API"""
        if not self.token or not self.phone_number_id:
            return {"error": "WHATSAPP_TOKEN or WHATSAPP_PHONE_ID not configured"}
        url = f"{self.API_BASE}/{self.phone_number_id}/messages"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(url, json=payload, headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            })
            return r.json()

    # ── Webhook Handler ────────────────────────────────────────────────────

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify webhook (GET request from Meta)"""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    async def handle_webhook(self, payload: dict) -> dict:
        """Handle incoming webhook payload"""
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])

            for message in messages:
                await self.process_message(message, value)

            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {"status": "error", "detail": str(e)}

    async def process_message(self, message: dict, context: dict) -> None:
        """Process a single incoming message"""
        msg_type = message.get("type", "")
        from_number = message.get("from", "")
        msg_id = message.get("id", "")

        if msg_type == "text":
            text = message["text"]["body"]
            await self.handle_text_message(from_number, text)

        elif msg_type == "interactive":
            reply = message.get("interactive", {}).get("button_reply", {})
            button_id = reply.get("id", "")
            button_title = reply.get("title", "")
            await self.handle_button_reply(from_number, button_id, button_title)

        elif msg_type == "audio":
            await self.send_text(from_number, "🎵 Voice messages coming soon! Please send text for now.")

        elif msg_type == "image":
            await self.send_text(from_number, "🖼️ Image processing coming soon! Please send text for now.")

    async def handle_text_message(self, from_number: str, text: str) -> None:
        """Handle text message"""
        text = text.strip()

        # Commands
        if text.lower() in ["/start", "start", "hello", "hi", "helo"]:
            await self.send_interactive(
                from_number,
                "🔱 *VIKARMA* — Free AI for All Humanity\n\nI am Tvaṣṭā, your AI companion.\nWhat would you like to do?",
                ["Chat with AI", "Run Command", "Web Search"]
            )
            return

        if text.lower().startswith("/shell ") or text.lower().startswith("$ "):
            cmd = text.replace("/shell ", "").replace("$ ", "").strip()
            if self.tool_handler:
                result = await self.tool_handler("shell", {"command": cmd})
                output = result.get("stdout", "") + result.get("stderr", "")
                await self.send_text(from_number, f"⚡ `{cmd}`\n\n```\n{output[:2000] or '(no output)'}\n```")
            else:
                await self.send_text(from_number, "⚠️ Tool gateway not connected")
            return

        if text.lower().startswith("/search "):
            query = text.replace("/search ", "").strip()
            if self.tool_handler:
                result = await self.tool_handler("web_search", {"query": query})
                results = result.get("results", [])
                if results:
                    lines = [f"🔍 *{query}*\n"]
                    for r in results[:3]:
                        lines.append(f"• {r.get('title','')[:50]}\n  {r.get('snippet','')[:80]}")
                    await self.send_text(from_number, "\n".join(lines))
                else:
                    await self.send_text(from_number, "No results found.")
            return

        # Default: chat with AI
        if self.ai_handler:
            try:
                response = await self.ai_handler(text, provider="claude")
                # WhatsApp 4096 char limit
                for chunk in [response[i:i+4000] for i in range(0, len(response), 4000)]:
                    await self.send_text(from_number, chunk)
            except Exception as e:
                await self.send_text(from_number, f"❌ AI error: {str(e)}")
        else:
            await self.send_text(from_number,
                f"🔱 Message received!\n\n_{text}_\n\nAI handler not connected. Start full Vikarma server.\n\nOm Namah Shivaya 🕉️"
            )

    async def handle_button_reply(self, from_number: str, button_id: str, title: str) -> None:
        """Handle button reply"""
        if "chat" in title.lower():
            await self.send_text(from_number, "💬 Just type your message and I'll respond! 🔱")
        elif "command" in title.lower():
            await self.send_text(from_number, "🖥️ Send commands with prefix:\n`/shell <command>`\ne.g. `/shell ls -la`")
        elif "search" in title.lower():
            await self.send_text(from_number, "🔍 Send search with prefix:\n`/search <query>`\ne.g. `/search latest AI news`")
