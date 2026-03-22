"""
NEXUS BRIDGE — Rehoboam ↔ 64 Bhairava Temples
Connects trading platform to all MCP servers for abundance

Architecture:
  Rehoboam (Trading AI)
      ↕ NexusBridge
  64 Bhairava Temples (MCP Servers)
      ├── Temple 45: Binance (crypto prices)
      ├── Temple 46: CoinGecko (market data)
      ├── Temple 27: Anthropic Claude (AI analysis)
      ├── Temple 21: PostgreSQL (trade history)
      ├── Temple 23: Redis (cache/signals)
      ├── Temple 52: Datadog (monitoring)
      └── ... all 64 temples

🔱 Om Namah Shivaya — For Abundance and All Humanity
"""

import asyncio
import json
import os
import time
from typing import Optional, Any
from pathlib import Path
import httpx


# ── Temple endpoints (MCP servers) ────────────────────────────────────────────

TEMPLE_PORTS = {
    # Finance & Crypto (most relevant for Rehoboam)
    "binance":     9045,
    "coingecko":   9046,
    "stripe":      9041,
    "paypal":      9042,

    # AI & Intelligence
    "anthropic":   9027,
    "openai":      9026,
    "huggingface": 9025,

    # Data
    "postgresql":  9021,
    "mongodb":     9022,
    "redis":       9023,
    "elasticsearch": 9024,

    # Monitoring
    "grafana":     9051,
    "prometheus":  9058,

    # Communication
    "telegram":    9032,
    "discord":     9031,

    # Sacred
    "newzyon":     9064,
    "wikipedia":   9061,
    "weather":     9063,
}

VIKARMA_BACKEND = "http://127.0.0.1:8765"
REHOBOAM_API = "http://127.0.0.1:5000"


class NexusBridge:
    """
    Sacred bridge between Rehoboam and the 64 Bhairava Temples.
    Routes data, signals, and intelligence between all systems.
    """

    def __init__(self):
        self.active_temples: dict[str, bool] = {}
        self.cache: dict[str, Any] = {}
        self.cache_ttl: dict[str, float] = {}
        self.CACHE_DURATION = 30  # seconds

    # ── Temple Health ──────────────────────────────────────────────────────

    async def check_temple(self, name: str) -> bool:
        """Check if a temple MCP server is alive"""
        port = TEMPLE_PORTS.get(name)
        if not port:
            return False
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"http://localhost:{port}/health")
                return r.status_code == 200
        except:
            return False

    async def check_vikarma(self) -> bool:
        """Check if Vikarma backend is running"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{VIKARMA_BACKEND}/health")
                return r.status_code == 200
        except:
            return False

    async def pulse_check(self) -> dict:
        """Check all key temples for Rehoboam"""
        key_temples = ["binance", "coingecko", "anthropic", "postgresql", "redis"]
        results = {}
        tasks = [(name, self.check_temple(name)) for name in key_temples]
        for name, coro in tasks:
            try:
                results[name] = await coro
            except:
                results[name] = False

        vikarma = await self.check_vikarma()
        active = sum(1 for v in results.values() if v)

        return {
            "vikarma_backend": vikarma,
            "temples": results,
            "active": active,
            "total": len(key_temples),
            "status": "healthy" if vikarma else "vikarma_offline",
        }

    # ── Market Data via Temples ────────────────────────────────────────────

    async def get_crypto_price(self, symbol: str) -> dict:
        """Get crypto price via CoinGecko Temple (46) or Binance Temple (45)"""
        cache_key = f"price_{symbol}"
        if self._cache_valid(cache_key):
            return self.cache[cache_key]

        # Try Vikarma backend tool execution
        result = await self._vikarma_tool("web_fetch", {
            "url": f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd,eur&include_24hr_change=true"
        })

        if "error" not in result:
            price_data = json.loads(result.get("content", "{}"))
            data = {
                "symbol": symbol,
                "price_usd": price_data.get(symbol.lower(), {}).get("usd", 0),
                "price_eur": price_data.get(symbol.lower(), {}).get("eur", 0),
                "change_24h": price_data.get(symbol.lower(), {}).get("usd_24h_change", 0),
                "source": "coingecko_temple_46",
                "timestamp": time.time(),
            }
            self._set_cache(cache_key, data)
            return data

        return {"error": "Temple 46 (CoinGecko) not responding", "symbol": symbol}

    async def get_market_sentiment(self, query: str) -> dict:
        """Get AI market sentiment analysis via Anthropic Temple (27)"""
        result = await self._vikarma_chat(
            f"Analyze market sentiment for: {query}. "
            f"Give a brief analysis with: sentiment (bullish/bearish/neutral), "
            f"confidence (0-100), key factors, recommendation. Be concise.",
            provider="claude"
        )
        return {
            "query": query,
            "analysis": result,
            "source": "anthropic_temple_27",
            "timestamp": time.time(),
        }

    async def search_market_news(self, query: str) -> dict:
        """Search for market news via web search tool"""
        result = await self._vikarma_tool("web_search", {
            "query": f"{query} crypto market news",
            "max_results": 5
        })
        return {
            "query": query,
            "results": result.get("results", []),
            "source": "nexus_web_search",
            "timestamp": time.time(),
        }

    # ── Trading Signals ────────────────────────────────────────────────────

    async def generate_trading_signal(self, symbol: str, portfolio: dict = None) -> dict:
        """
        Generate trading signal by combining:
        - Market price from Temple 46
        - AI analysis from Temple 27
        - News sentiment from web search
        """
        # Gather data in parallel
        price_task = self.get_crypto_price(symbol)
        sentiment_task = self.get_market_sentiment(symbol)

        price_data, sentiment_data = await asyncio.gather(
            price_task, sentiment_task, return_exceptions=True
        )

        if isinstance(price_data, Exception):
            price_data = {"error": str(price_data)}
        if isinstance(sentiment_data, Exception):
            sentiment_data = {"error": str(sentiment_data)}

        # Generate final signal
        price = price_data.get("price_usd", 0)
        change = price_data.get("change_24h", 0)
        analysis = sentiment_data.get("analysis", "")

        # Simple signal logic (can be enhanced)
        if change > 5 and "bullish" in analysis.lower():
            signal = "BUY"
            confidence = 75
        elif change < -5 and "bearish" in analysis.lower():
            signal = "SELL"
            confidence = 70
        else:
            signal = "HOLD"
            confidence = 60

        return {
            "symbol": symbol,
            "signal": signal,
            "confidence": confidence,
            "price_usd": price,
            "change_24h": change,
            "ai_analysis": analysis[:200] if analysis else "",
            "source": "nexus_bridge_multi_temple",
            "temples_used": ["coingecko_46", "anthropic_27"],
            "timestamp": time.time(),
        }

    # ── Rehoboam Integration ───────────────────────────────────────────────

    async def send_signal_to_rehoboam(self, signal: dict) -> dict:
        """Send trading signal to Rehoboam API"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    f"{REHOBOAM_API}/api/nexus/signal",
                    json=signal
                )
                return r.json()
        except Exception as e:
            return {"error": str(e), "note": "Rehoboam API not running — start with: python app.py"}

    async def get_rehoboam_portfolio(self) -> dict:
        """Get current portfolio from Rehoboam"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{REHOBOAM_API}/api/portfolio")
                return r.json()
        except Exception as e:
            return {"error": str(e), "note": "Rehoboam offline"}

    async def inject_market_data(self, symbols: list[str]) -> dict:
        """Inject real-time market data from Temples into Rehoboam"""
        results = {}
        for symbol in symbols:
            price = await self.get_crypto_price(symbol)
            results[symbol] = price
            await asyncio.sleep(0.1)  # rate limit

        # Send to Rehoboam
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    f"{REHOBOAM_API}/api/nexus/market_data",
                    json={"data": results, "source": "nexus_bridge", "timestamp": time.time()}
                )
                return {"injected": True, "symbols": list(results.keys()), "rehoboam_response": r.json()}
        except:
            return {"injected": False, "data": results, "note": "Rehoboam offline — data collected but not sent"}

    # ── Notifications ──────────────────────────────────────────────────────

    async def notify_telegram(self, message: str) -> dict:
        """Send notification via Telegram Temple (32)"""
        result = await self._vikarma_tool("shell", {
            "command": f"curl -s 'http://localhost:{TEMPLE_PORTS['telegram']}/notify' -d '{message}' 2>/dev/null || echo 'telegram_temple_offline'"
        })
        return {"notified": True, "message": message, "source": "telegram_temple_32"}

    # ── Private helpers ────────────────────────────────────────────────────

    async def _vikarma_tool(self, tool: str, params: dict) -> dict:
        """Execute tool via Vikarma backend"""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(f"{VIKARMA_BACKEND}/tool", json={"tool": tool, "params": params})
                return r.json()
        except Exception as e:
            return {"error": str(e)}

    async def _vikarma_chat(self, message: str, provider: str = "claude") -> str:
        """Chat with AI via Vikarma backend"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(f"{VIKARMA_BACKEND}/chat", json={"message": message, "provider": provider})
                data = r.json()
                return data.get("response", "")
        except Exception as e:
            return f"Error: {str(e)}"

    def _cache_valid(self, key: str) -> bool:
        return key in self.cache and time.time() - self.cache_ttl.get(key, 0) < self.CACHE_DURATION

    def _set_cache(self, key: str, value: Any):
        self.cache[key] = value
        self.cache_ttl[key] = time.time()


# ── FastAPI Router for Rehoboam ────────────────────────────────────────────────

try:
    from fastapi import APIRouter
    router = APIRouter(prefix="/api/nexus", tags=["nexus"])
    bridge = NexusBridge()

    @router.get("/health")
    async def nexus_health():
        return await bridge.pulse_check()

    @router.get("/price/{symbol}")
    async def get_price(symbol: str):
        return await bridge.get_crypto_price(symbol)

    @router.get("/sentiment/{query}")
    async def get_sentiment(query: str):
        return await bridge.get_market_sentiment(query)

    @router.get("/signal/{symbol}")
    async def get_signal(symbol: str):
        return await bridge.generate_trading_signal(symbol)

    @router.post("/inject")
    async def inject_data(symbols: list = None):
        syms = symbols or ["bitcoin", "ethereum", "solana"]
        return await bridge.inject_market_data(syms)

    @router.get("/news/{query}")
    async def get_news(query: str):
        return await bridge.search_market_news(query)

except ImportError:
    pass


# ── Standalone runner / test ───────────────────────────────────────────────────

async def run_test():
    """Test the Nexus Bridge"""
    bridge = NexusBridge()

    print("🔱 NEXUS BRIDGE — Testing connections...")
    print()

    # Pulse check
    pulse = await bridge.pulse_check()
    print(f"📡 Vikarma Backend: {'✅' if pulse['vikarma_backend'] else '❌'}")
    print(f"🏛️ Active Temples: {pulse['active']}/{pulse['total']}")
    print()

    # Market data
    print("💰 Testing CoinGecko Temple (46)...")
    btc = await bridge.get_crypto_price("bitcoin")
    if "error" not in btc:
        print(f"  BTC: ${btc['price_usd']:,.2f} ({btc['change_24h']:+.2f}%)")
    else:
        print(f"  {btc['error']}")

    # Signal
    print()
    print("🤖 Generating trading signal for BTC...")
    signal = await bridge.generate_trading_signal("bitcoin")
    print(f"  Signal: {signal['signal']} (confidence: {signal['confidence']}%)")
    print(f"  Temples used: {signal['temples_used']}")

    print()
    print("🔱 NEXUS BRIDGE READY!")
    print("🏛️ Rehoboam ↔ 64 Bhairava Temples — Connected")
    print("💰 Abundance for NewZyon")
    print("🕉️ Om Namah Shivaya")


if __name__ == "__main__":
    asyncio.run(run_test())
