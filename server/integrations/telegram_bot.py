"""
VIKARMA — Telegram Bot Integration
Remote control via Telegram — sacred messenger 🔱
"""

import asyncio
import os
import json
import logging
from typing import Optional, Callable
import httpx

logger = logging.getLogger("vikarma.telegram")


class VikarmaBot:
    """
    Telegram bot for remote Vikarma control.
    Control your AI agent from anywhere via Telegram.
    """

    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(
        self,
        token: Optional[str] = None,
        allowed_users: Optional[list[int]] = None,
        ai_handler: Optional[Callable] = None,
        tool_handler: Optional[Callable] = None,
    ):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.allowed_users = allowed_users or []
        self.ai_handler = ai_handler
        self.tool_handler = tool_handler
        self.offset = 0
        self.running = False
        self._base = self.API_BASE.format(token=self.token)

    def _is_allowed(self, user_id: int) -> bool:
        if not self.allowed_users:
            return True  # Allow all if no restrictions
        return user_id in self.allowed_users

    # ── API Methods ────────────────────────────────────────────────────────

    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> dict:
        """Send a message"""
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{self._base}/sendMessage", json={
                "chat_id": chat_id,
                "text": text[:4096],  # Telegram limit
                "parse_mode": parse_mode,
            })
            return r.json()

    async def send_long_message(self, chat_id: int, text: str) -> None:
        """Send long text split into chunks"""
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            await self.send_message(chat_id, chunk)
            await asyncio.sleep(0.1)

    async def get_updates(self) -> list:
        """Get pending updates (long polling)"""
        async with httpx.AsyncClient(timeout=35) as client:
            try:
                r = await client.get(f"{self._base}/getUpdates", params={
                    "offset": self.offset,
                    "timeout": 30,
                    "allowed_updates": ["message"],
                })
                data = r.json()
                return data.get("result", [])
            except Exception as e:
                logger.error(f"Get updates error: {e}")
                return []

    async def get_me(self) -> dict:
        """Get bot info"""
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self._base}/getMe")
            return r.json().get("result", {})

    # ── Message Handler ────────────────────────────────────────────────────

    async def handle_message(self, message: dict) -> None:
        """Process incoming message"""
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        username = message["from"].get("username", "unknown")
        text = message.get("text", "")

        if not self._is_allowed(user_id):
            await self.send_message(chat_id, "⛔ Access denied. This is a private Vikarma instance.")
            return

        if not text:
            return

        logger.info(f"Message from @{username} ({user_id}): {text[:50]}")

        # Handle commands
        if text.startswith("/"):
            await self.handle_command(chat_id, user_id, text)
        else:
            await self.handle_chat(chat_id, user_id, text)

    async def handle_command(self, chat_id: int, user_id: int, text: str) -> None:
        """Handle bot commands"""
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "/start":
            await self.send_message(chat_id,
                "🔱 *VIKARMA* — Free AI for All Humanity\n\n"
                "I am Tvaṣṭā, your AI companion.\n\n"
                "*Commands:*\n"
                "/chat — Chat with AI\n"
                "/shell `<command>` — Execute shell command\n"
                "/file `<path>` — Read file\n"
                "/ls `<path>` — List directory\n"
                "/search `<query>` — Web search\n"
                "/status — System status\n"
                "/help — Show this message\n\n"
                "Or just type any message to chat with Claude! 🔱\n\n"
                "_Om Namah Shivaya_ 🕉️"
            )

        elif cmd == "/help":
            await self.send_message(chat_id,
                "🔱 *VIKARMA Commands*\n\n"
                "💬 Just type to chat with AI\n"
                "🖥️ `/shell ls -la` — Run commands\n"
                "📄 `/file path/to/file` — Read files\n"
                "📁 `/ls /home` — List directory\n"
                "🔍 `/search query` — Web search\n"
                "⚙️ `/status` — System info\n"
                "🏛️ `/temples` — Temple status\n"
                "❌ `/cancel` — Cancel current task"
            )

        elif cmd == "/status":
            import platform
            import psutil
            try:
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                await self.send_message(chat_id,
                    f"⚙️ *System Status*\n\n"
                    f"🖥️ OS: {platform.system()} {platform.release()}\n"
                    f"💻 CPU: {cpu}%\n"
                    f"🧠 RAM: {mem.percent}% ({mem.used//1024//1024}MB / {mem.total//1024//1024}MB)\n"
                    f"💾 Disk: {disk.percent}% used\n"
                    f"🔱 Vikarma: ONLINE\n"
                    f"🏛️ Temples: 64 ready"
                )
            except ImportError:
                import shutil
                total, used, free = shutil.disk_usage("/")
                await self.send_message(chat_id,
                    f"⚙️ *System Status*\n"
                    f"🔱 Vikarma: ONLINE\n"
                    f"🏛️ 64 Bhairava Temples ready\n"
                    f"💾 Disk free: {free//1024//1024//1024}GB\n"
                    f"_Om Namah Shivaya_ 🕉️"
                )

        elif cmd == "/shell":
            if not args:
                await self.send_message(chat_id, "Usage: `/shell <command>`")
                return
            await self.send_message(chat_id, f"⚡ Running: `{args}`")
            if self.tool_handler:
                result = await self.tool_handler("shell", {"command": args})
                output = result.get("stdout", "") + result.get("stderr", "")
                await self.send_long_message(chat_id, f"```\n{output or '(no output)'}\n```")
            else:
                await self.send_message(chat_id, "⚠️ Tool gateway not connected")

        elif cmd == "/file":
            if not args:
                await self.send_message(chat_id, "Usage: `/file <path>`")
                return
            if self.tool_handler:
                result = await self.tool_handler("read_file", {"path": args})
                if "error" in result:
                    await self.send_message(chat_id, f"❌ {result['error']}")
                else:
                    content = result["content"]
                    await self.send_long_message(chat_id, f"📄 `{args}`:\n```\n{content}\n```")
            else:
                await self.send_message(chat_id, "⚠️ Tool gateway not connected")

        elif cmd == "/ls":
            path = args or "."
            if self.tool_handler:
                result = await self.tool_handler("list_dir", {"path": path})
                if "error" in result:
                    await self.send_message(chat_id, f"❌ {result['error']}")
                else:
                    items = result["items"]
                    lines = [f"📁 *{path}* ({result['count']} items)\n"]
                    for item in items[:30]:
                        icon = "📁" if item["type"] == "dir" else "📄"
                        size = f" ({item['size']} bytes)" if item.get("size") else ""
                        lines.append(f"{icon} {item['name']}{size}")
                    await self.send_message(chat_id, "\n".join(lines))
            else:
                await self.send_message(chat_id, "⚠️ Tool gateway not connected")

        elif cmd == "/search":
            if not args:
                await self.send_message(chat_id, "Usage: `/search <query>`")
                return
            await self.send_message(chat_id, f"🔍 Searching: _{args}_")
            if self.tool_handler:
                result = await self.tool_handler("web_search", {"query": args})
                results = result.get("results", [])
                if not results:
                    await self.send_message(chat_id, "No results found.")
                else:
                    lines = [f"🔍 *Results for '{args}'*\n"]
                    for r in results[:5]:
                        title = r.get("title", "")[:60]
                        snippet = r.get("snippet", "")[:100]
                        url = r.get("url", "")
                        lines.append(f"• *{title}*\n  {snippet}\n  {url}\n")
                    await self.send_message(chat_id, "\n".join(lines))

        elif cmd == "/temples":
            await self.send_message(chat_id,
                "🏛️ *64 Bhairava Temples*\n\n"
                "• Temple 1-10: Productivity (Jira, GitHub, Slack...)\n"
                "• Temple 11-20: Cloud (AWS, GCP, Azure...)\n"
                "• Temple 21-30: Data & AI (Claude, Gemini...)\n"
                "• Temple 31-40: Communication\n"
                "• Temple 41-50: Commerce & Finance\n"
                "• Temple 51-60: Monitoring\n"
                "• Temple 61-64: Sacred (Wikipedia, News, KAN)\n\n"
                "🌐 [Live Monitor](https://valentinuuiuiu.github.io/nexus-bhairava-temples/)\n\n"
                "_Om Namah Shivaya_ 🔱"
            )

        else:
            await self.send_message(chat_id, f"Unknown command: `{cmd}`\nType /help for available commands.")

    async def handle_chat(self, chat_id: int, user_id: int, text: str) -> None:
        """Handle regular chat messages"""
        await self.send_message(chat_id, "🔱 _Thinking..._")
        if self.ai_handler:
            try:
                response = await self.ai_handler(text, provider="claude")
                await self.send_long_message(chat_id, response)
            except Exception as e:
                await self.send_message(chat_id, f"❌ AI error: {str(e)}")
        else:
            await self.send_message(chat_id,
                f"🔱 Message received: _{text}_\n\n"
                "AI handler not connected. Start the full Vikarma server."
            )

    # ── Main Loop ──────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the bot polling loop"""
        if not self.token:
            logger.error("No TELEGRAM_BOT_TOKEN set")
            return

        me = await self.get_me()
        bot_name = me.get("username", "unknown")
        logger.info(f"🤖 Vikarma Bot @{bot_name} started!")
        print(f"🔱 Telegram Bot @{bot_name} is LIVE!")

        self.running = True
        while self.running:
            try:
                updates = await self.get_updates()
                for update in updates:
                    self.offset = update["update_id"] + 1
                    if "message" in update:
                        asyncio.create_task(self.handle_message(update["message"]))
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)

    def stop(self):
        self.running = False


# ── Standalone runner ──────────────────────────────────────────────────────────

async def run_standalone():
    """Run bot standalone for testing"""
    from server.tools.gateway import VikarmaToolGateway

    gateway = VikarmaToolGateway()

    async def tool_handler(tool: str, params: dict) -> dict:
        return await gateway.execute(tool, params)

    bot = VikarmaBot(tool_handler=tool_handler)
    await bot.start()


if __name__ == "__main__":
    asyncio.run(run_standalone())
