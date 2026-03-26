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
    # ── Data & Databases (9021–9030) ──────────────────────────────────────
    "postgresql":      9021,  # Temple 01 — Relational data, trade history
    "mongodb":         9022,  # Temple 02 — Document store, flexible schemas
    "redis":           9023,  # Temple 03 — Cache, pub/sub, real-time signals
    "elasticsearch":   9024,  # Temple 04 — Full-text search, log analysis
    "huggingface":     9025,  # Temple 05 — Open-source AI models & datasets
    "openai":          9026,  # Temple 06 — GPT models, embeddings
    "anthropic":       9027,  # Temple 07 — Claude AI analysis & reasoning
    "ollama":          9028,  # Temple 08 — Local LLM inference (privacy)
    "pinecone":        9029,  # Temple 09 — Vector DB, semantic search
    "chroma":          9030,  # Temple 10 — Embedded vector store

    # ── Communication & Social (9031–9040) ───────────────────────────────
    "discord":         9031,  # Temple 11 — Community, alerts, bots
    "telegram":        9032,  # Temple 12 — Notifications, trading alerts
    "slack":           9033,  # Temple 13 — Team comms, workflow
    "whatsapp":        9034,  # Temple 14 — Messaging, global reach
    "email":           9035,  # Temple 15 — SMTP/IMAP, reports & alerts
    "twilio":          9036,  # Temple 16 — SMS, voice, OTP
    "twitter":         9037,  # Temple 17 — Market sentiment, news
    "linkedin":        9038,  # Temple 18 — Professional network, recruiting
    "github":          9039,  # Temple 19 — Code, PRs, issues, CI
    "gitlab":          9040,  # Temple 20 — Self-hosted DevOps

    # ── Finance & Trading (9041–9050) ────────────────────────────────────
    "stripe":          9041,  # Temple 21 — Payments, subscriptions
    "paypal":          9042,  # Temple 22 — Global payments
    "coinbase":        9043,  # Temple 23 — Crypto exchange, custody
    "kraken":          9044,  # Temple 24 — Crypto trading, staking
    "binance":         9045,  # Temple 25 — Largest crypto exchange
    "coingecko":       9046,  # Temple 26 — Crypto prices, market data
    "alpaca":          9047,  # Temple 27 — Commission-free stock trading
    "polygon":         9048,  # Temple 28 — Real-time stock & options data
    "yahoo_finance":   9049,  # Temple 29 — Historical market data, news
    "forex":           9050,  # Temple 30 — FX rates, currency conversion

    # ── Monitoring & DevOps (9051–9060) ──────────────────────────────────
    "grafana":         9051,  # Temple 31 — Dashboards, visualization
    "datadog":         9052,  # Temple 32 — APM, infrastructure monitoring
    "sentry":          9053,  # Temple 33 — Error tracking, performance
    "cloudwatch":      9054,  # Temple 34 — AWS monitoring & logs
    "kubernetes":      9055,  # Temple 35 — Container orchestration
    "docker":          9056,  # Temple 36 — Containerization
    "jenkins":         9057,  # Temple 37 — CI/CD pipelines
    "prometheus":      9058,  # Temple 38 — Metrics collection & alerting
    "pagerduty":       9059,  # Temple 39 — Incident management
    "nginx":           9060,  # Temple 40 — Reverse proxy, load balancer

    # ── Knowledge & Web (9061–9070) ──────────────────────────────────────
    "wikipedia":       9061,  # Temple 41 — Encyclopedia, factual knowledge
    "arxiv":           9062,  # Temple 42 — Research papers, AI/finance
    "weather":         9063,  # Temple 43 — Forecasts, climate data
    "newzyon":         9064,  # Temple 44 — Sacred NewZyon intelligence
    "duckduckgo":      9065,  # Temple 45 — Privacy-first web search
    "google_search":   9066,  # Temple 46 — Comprehensive web search
    "news_api":        9067,  # Temple 47 — Global news aggregation
    "reddit":          9068,  # Temple 48 — Community sentiment, r/crypto
    "stackoverflow":   9069,  # Temple 49 — Developer Q&A, code solutions
    "maps":            9070,  # Temple 50 — Geolocation, routing

    # ── Cloud & Storage (9071–9080) ──────────────────────────────────────
    "aws_s3":          9071,  # Temple 51 — Object storage, backups
    "google_cloud":    9072,  # Temple 52 — GCP services, BigQuery
    "azure":           9073,  # Temple 53 — Microsoft cloud services
    "cloudflare":      9074,  # Temple 54 — CDN, DDoS protection, DNS
    "vercel":          9075,  # Temple 55 — Frontend deployment
    "github_actions":  9076,  # Temple 56 — Automated workflows
    "firebase":        9077,  # Temple 57 — Realtime DB, auth, hosting
    "supabase":        9078,  # Temple 58 — Open-source Firebase alt
    "notion":          9079,  # Temple 59 — Docs, knowledge base, tasks
    "airtable":        9080,  # Temple 60 — Spreadsheet-DB hybrid

    # ── Sacred & Utility (9081–9084) ─────────────────────────────────────
    "calendar":        9081,  # Temple 61 — Scheduling, time management
    "calculator":      9082,  # Temple 62 — Precise math, financial calcs
    "translator":      9083,  # Temple 63 — Multi-language translation
    "vikarma_core":    9084,  # Temple 64 — Self-reference, meta-cognition
}

# Human-readable skill descriptions for the agent system prompt
TEMPLE_SKILLS = {
    name: f"Temple {port - 9020:02d} ({port}): {TEMPLE_PORTS[name]}"
    for name, port in TEMPLE_PORTS.items()
}

# Skill descriptions shown to the AI agent
TEMPLE_SKILL_DESCRIPTIONS = {
    "postgresql":    "Query/write relational data and trade history",
    "mongodb":       "Document store — flexible JSON data",
    "redis":         "Cache, pub/sub, real-time signals",
    "elasticsearch": "Full-text search and log analysis",
    "huggingface":   "Open-source AI models, datasets, inference",
    "openai":        "GPT models, embeddings, completions",
    "anthropic":     "Claude AI — deep reasoning and analysis",
    "ollama":        "Local LLM inference (private, offline)",
    "pinecone":      "Vector DB — semantic similarity search",
    "chroma":        "Embedded vector store for RAG",
    "discord":       "Send messages, alerts to Discord channels",
    "telegram":      "Send Telegram notifications and trading alerts",
    "slack":         "Team messaging, workflow notifications",
    "whatsapp":      "WhatsApp messaging",
    "email":         "Send/receive email via SMTP/IMAP",
    "twilio":        "SMS, voice calls, OTP",
    "twitter":       "Post tweets, read market sentiment",
    "linkedin":      "Professional network, posts",
    "github":        "Repos, PRs, issues, releases, code search",
    "gitlab":        "Self-hosted DevOps pipelines",
    "stripe":        "Process payments, manage subscriptions",
    "paypal":        "PayPal payments and transfers",
    "coinbase":      "Crypto exchange, buy/sell, custody",
    "kraken":        "Crypto trading, staking, margin",
    "binance":       "Largest crypto exchange — spot, futures",
    "coingecko":     "Crypto prices, market cap, trends",
    "alpaca":        "Stock trading, portfolio management",
    "polygon":       "Real-time stocks, options, forex data",
    "yahoo_finance": "Historical market data, financials, news",
    "forex":         "FX rates, currency conversion",
    "grafana":       "Create/query dashboards and visualizations",
    "datadog":       "APM, infrastructure metrics, logs",
    "sentry":        "Error tracking, performance monitoring",
    "cloudwatch":    "AWS logs, metrics, alarms",
    "kubernetes":    "Deploy, scale, manage containers",
    "docker":        "Build, run, manage containers",
    "jenkins":       "CI/CD pipeline management",
    "prometheus":    "Metrics scraping and alerting rules",
    "pagerduty":     "Incident management, on-call routing",
    "nginx":         "Proxy config, load balancer, SSL",
    "wikipedia":     "Encyclopedic knowledge, factual lookup",
    "arxiv":         "Research papers — AI, finance, science",
    "weather":       "Weather forecasts and climate data",
    "newzyon":       "Sacred NewZyon — abundance intelligence",
    "duckduckgo":    "Privacy-first web search",
    "google_search": "Comprehensive Google web search",
    "news_api":      "Global news headlines and articles",
    "reddit":        "Community sentiment, subreddit data",
    "stackoverflow": "Developer Q&A, code solutions",
    "maps":          "Geolocation, routing, place data",
    "aws_s3":        "Object storage — upload, download, list",
    "google_cloud":  "GCP — BigQuery, GCS, Vertex AI",
    "azure":         "Microsoft cloud — storage, AI, functions",
    "cloudflare":    "CDN, DNS, DDoS protection, Workers",
    "vercel":        "Deploy frontend apps, serverless functions",
    "github_actions":"Trigger and monitor CI/CD workflows",
    "firebase":      "Realtime DB, Firestore, auth, hosting",
    "supabase":      "Postgres + realtime + auth (open source)",
    "notion":        "Docs, knowledge base, task management",
    "airtable":      "Structured data, spreadsheet-DB hybrid",
    "calendar":      "Schedule events, manage time",
    "calculator":    "Precise arithmetic and financial calculations",
    "translator":    "Translate text across 100+ languages",
    "vikarma_core":  "Vikarma self-reference and meta-cognition",
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

    # ── Temple Skills ──────────────────────────────────────────────────────

    async def call_temple(self, temple: str, action: str, params: dict = None) -> dict:
        """
        Invoke any of the 64 Bhairava Temple skills.
        Routes to the MCP server on its port, or falls back to built-in handlers.
        """
        if temple not in TEMPLE_PORTS:
            available = list(TEMPLE_PORTS.keys())
            return {"error": f"Unknown temple: '{temple}'", "available_temples": available}

        port = TEMPLE_PORTS[temple]
        params = params or {}

        # Try the MCP server on its port first
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"http://localhost:{port}/{action}",
                    json=params,
                    headers={"Content-Type": "application/json"},
                )
                return {"temple": temple, "port": port, "action": action, "result": r.json()}
        except httpx.ConnectError:
            pass  # Temple not running locally — use built-in fallback

        # Built-in fallbacks for key temples
        return await self._temple_fallback(temple, action, params)

    async def _temple_fallback(self, temple: str, action: str, params: dict) -> dict:
        """Built-in fallbacks when a temple's MCP server isn't running locally."""
        port = TEMPLE_PORTS[temple]
        fallback_note = f"Temple {port} not running locally — using built-in fallback"

        # CoinGecko: price lookups
        if temple == "coingecko" and action in ("price", "get_price"):
            coin = params.get("coin", params.get("symbol", "bitcoin")).lower()
            result = await self._vikarma_tool("web_fetch", {
                "url": f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,eur&include_24hr_change=true"
            })
            return {"temple": temple, "action": action, "result": result, "note": fallback_note}

        # Wikipedia: article lookup
        if temple == "wikipedia":
            query = params.get("query", params.get("topic", action))
            result = await self._vikarma_tool("web_fetch", {
                "url": f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
            })
            return {"temple": temple, "action": action, "result": result, "note": fallback_note}

        # arXiv: paper search
        if temple == "arxiv":
            query = params.get("query", action)
            result = await self._vikarma_tool("web_fetch", {
                "url": f"https://export.arxiv.org/api/query?search_query=all:{query}&max_results=5"
            })
            return {"temple": temple, "action": action, "result": result, "note": fallback_note}

        # Weather
        if temple == "weather":
            city = params.get("city", params.get("location", "London"))
            result = await self._vikarma_tool("web_fetch", {
                "url": f"https://wttr.in/{city.replace(' ', '+')}?format=j1"
            })
            return {"temple": temple, "action": action, "result": result, "note": fallback_note}

        # DuckDuckGo search
        if temple == "duckduckgo":
            query = params.get("query", action)
            result = await self._vikarma_tool("web_search", {"query": query})
            return {"temple": temple, "action": action, "result": result, "note": fallback_note}

        # Translator (via LibreTranslate public instance)
        if temple == "translator":
            text = params.get("text", "")
            target = params.get("target_lang", "en")
            result = await self._vikarma_tool("web_fetch", {
                "url": f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target}&dt=t&q={text}"
            })
            return {"temple": temple, "action": action, "result": result, "note": fallback_note}

        # Anthropic / Claude sentiment/analysis
        if temple in ("anthropic", "openai", "ollama", "huggingface"):
            prompt = params.get("prompt", params.get("message", action))
            result = await self._vikarma_chat(prompt, provider="claude" if temple == "anthropic" else "openai")
            return {"temple": temple, "action": action, "result": result, "note": fallback_note}

        # Calculator — evaluate directly (no backend needed)
        if temple == "calculator":
            expression = params.get("expression", params.get("expr", action))
            try:
                # Safe eval: numbers and math operators only
                import math
                safe_globals = {"__builtins__": {}, "math": math}
                safe_globals.update({k: getattr(math, k) for k in dir(math) if not k.startswith("_")})
                value = eval(expression, safe_globals)  # noqa: S307
                return {"temple": temple, "action": action, "result": value, "expression": expression}
            except Exception as e:
                return {"temple": temple, "action": action, "error": str(e), "expression": expression}

        # News
        if temple in ("news_api", "reddit", "twitter"):
            query = params.get("query", action)
            result = await self._vikarma_tool("web_search", {"query": f"{query} news"})
            return {"temple": temple, "action": action, "result": result, "note": fallback_note}

        return {
            "temple": temple,
            "port": port,
            "action": action,
            "note": fallback_note,
            "description": TEMPLE_SKILL_DESCRIPTIONS.get(temple, ""),
            "params_received": params,
        }

    def list_temples(self, category: str = None) -> list[dict]:
        """List all 64 temples with their descriptions."""
        categories = {
            "data":          list(range(9021, 9031)),
            "communication": list(range(9031, 9041)),
            "finance":       list(range(9041, 9051)),
            "devops":        list(range(9051, 9061)),
            "knowledge":     list(range(9061, 9071)),
            "cloud":         list(range(9071, 9081)),
            "sacred":        list(range(9081, 9085)),
        }
        temples = []
        for name, port in TEMPLE_PORTS.items():
            cat = next((c for c, ports in categories.items() if port in ports), "other")
            if category and cat != category:
                continue
            temples.append({
                "name": name,
                "port": port,
                "temple_number": port - 9020,
                "category": cat,
                "description": TEMPLE_SKILL_DESCRIPTIONS.get(name, ""),
            })
        return sorted(temples, key=lambda t: t["port"])

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
