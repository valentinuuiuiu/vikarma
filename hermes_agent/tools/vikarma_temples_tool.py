"""
Vikarma Bhairava Temples Tool — Hermes Agent Plugin
67 sacred temple skills available as a native Hermes tool.
🔱 Om Namah Shivaya — For All Humanity
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Path bootstrap — vikarma server/ is one level up from hermes_agent/ ───────
_HERE = Path(__file__).resolve().parent          # vikarma/hermes_agent/tools/
_VIKARMA_ROOT = _HERE.parent.parent              # vikarma/
if str(_VIKARMA_ROOT) not in sys.path:
    sys.path.insert(0, str(_VIKARMA_ROOT))

try:
    from server.nexus_bridge import NexusBridge
    _nexus = NexusBridge()
    _AVAILABLE = True
except ImportError as e:
    logger.warning("Vikarma temples not available: %s", e)
    _AVAILABLE = False
    _nexus = None

from tools.registry import registry

TEMPLE_SCHEMA = {
    "name": "vikarma_temple",
    "description": (
        "Invoke one of Vikarma's 67 Bhairava Temple skills. "
        "DATA: postgresql, redis, huggingface, anthropic, ollama | "
        "COMMS: discord, telegram, slack, github, twitter | "
        "FINANCE: coingecko, kraken, binance, stripe | "
        "KNOWLEDGE: wikipedia, arxiv, weather, duckduckgo | "
        "BLOCKCHAIN: chainlink (price oracles), alchemy (wallet/NFT/gas) | "
        "AVATAR: gemini_avatar (vision+thinking+streaming) | "
        "SACRED: calculator, translator"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "temple": {"type": "string", "description": "Temple name e.g. coingecko"},
            "action": {"type": "string", "description": "Action e.g. price, query, vision"},
            "params": {"type": "object", "description": "Action parameters", "default": {}},
        },
        "required": ["temple", "action"],
    },
}

LIST_TEMPLES_SCHEMA = {
    "name": "list_vikarma_temples",
    "description": "List all 67 Vikarma Bhairava Temples, optionally filtered by category.",
    "parameters": {
        "type": "object",
        "properties": {
            "category": {"type": "string", "description": "Filter: data|comms|finance|devops|knowledge|cloud|sacred|blockchain|avatar"},
        },
    },
}

def _check_vikarma():
    if not _AVAILABLE:
        return False, "Vikarma server package not found."
    return True, None

def vikarma_temple_tool(temple: str, action: str, params: dict = None) -> dict:
    if not _AVAILABLE:
        return {"error": "Vikarma temples not available"}
    params = params or {}
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _nexus.call_temple(temple, action, params))
                return future.result(timeout=60)
        return loop.run_until_complete(_nexus.call_temple(temple, action, params))
    except Exception as e:
        return {"error": str(e), "temple": temple, "action": action}

def list_vikarma_temples_tool(category: str = None) -> dict:
    if not _AVAILABLE:
        return {"error": "Vikarma temples not available"}
    temples = _nexus.list_temples(category=category)
    return {"temples": temples, "total": len(temples),
            "categories": list({t.get("category", "unknown") for t in temples})}

registry.register(
    name="vikarma_temple", toolset="vikarma", schema=TEMPLE_SCHEMA,
    handler=lambda args, **kw: vikarma_temple_tool(
        temple=args.get("temple", ""), action=args.get("action", ""), params=args.get("params", {})),
    check_fn=_check_vikarma, is_async=False,
    description="Invoke a Vikarma Bhairava Temple skill (67 external services/APIs)", emoji="🔱",
)

registry.register(
    name="list_vikarma_temples", toolset="vikarma", schema=LIST_TEMPLES_SCHEMA,
    handler=lambda args, **kw: list_vikarma_temples_tool(category=args.get("category")),
    check_fn=_check_vikarma, is_async=False,
    description="List all 67 Vikarma Bhairava Temples", emoji="🛕",
)
