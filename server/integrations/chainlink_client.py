"""
Chainlink Oracle Client — Temple 65
Reads price feeds directly from on-chain Chainlink AggregatorV3 contracts.
Supports ETH/Polygon mainnet via public or Alchemy RPC.
🔱 Om Namah Shivaya
"""

import asyncio
import json
import logging
import os
import time
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# ── Chainlink AggregatorV3Interface ABI (minimal) ─────────────────────────────

AGGREGATOR_ABI = json.dumps([
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"internalType": "uint80",  "name": "roundId",         "type": "uint80"},
            {"internalType": "int256",  "name": "answer",          "type": "int256"},
            {"internalType": "uint256", "name": "startedAt",       "type": "uint256"},
            {"internalType": "uint256", "name": "updatedAt",       "type": "uint256"},
            {"internalType": "uint80",  "name": "answeredInRound", "type": "uint80"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "description",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
])

# ── Mainnet price feed addresses (Ethereum) ───────────────────────────────────

PRICE_FEEDS = {
    # Crypto
    "BTC/USD":   "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88b",
    "ETH/USD":   "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
    "LINK/USD":  "0x2c1d072e956AFFC0D435Cb7AC308d97936Ed4a3b",
    "SOL/USD":   "0x4ffC43a60e009B551865A93d232E33Fce9f01507",
    "MATIC/USD": "0x7bAC85A8a13A4BcD8abb3eB7d6b4d632c895B45B",
    "BNB/USD":   "0x14e613AC84a31f709eadbEf3bf98585aD3087600",
    "AVAX/USD":  "0xFF3EEb22B5E3dE6e705b44749C2559d704923FD7",
    "ADA/USD":   "0xAE48c91dF1fE419994FFDa27da09D5aC69c30f55",
    "DOT/USD":   "0x1C07AFb8E2B827c5A4739C6d59Ae3A5035f28734",
    "UNI/USD":   "0x553303d460EE0afB37EdFf9bE42922D8FF63220e",
    "AAVE/USD":  "0x547a514d5e3769680Ce22B2361c10Ea13619e8a9",
    "CRV/USD":   "0xCd627aA160A6fA45Eb793D19Ef54f5062F20f334",
    # Forex
    "EUR/USD":   "0xb49f677943BC038e9857d61E7d053CaA2C1734C1",
    "GBP/USD":   "0x5c0Ab2d9b5a7ed9f470386e82BB36A3613cDd4b5",
    "JPY/USD":   "0xBcE206caE7f0ec07b545EddE332A47C2F75bbeb3",
    # Commodities
    "XAU/USD":   "0x214eD9Da11D2fbe465a6fc601a91E62EbEc1a0D6",  # Gold
    "XAG/USD":   "0x379589227b15F1a12195D3f2d90bBc9F31f95235",  # Silver
}

# ── Public RPC endpoints (fallback when no Alchemy key) ───────────────────────

PUBLIC_RPC_ENDPOINTS = [
    "https://cloudflare-eth.com",
    "https://rpc.ankr.com/eth",
    "https://eth.public-rpc.com",
]


class ChainlinkClient:
    """
    Read Chainlink oracle price feeds on-chain.
    Uses Alchemy RPC if ALCHEMY_API_KEY is set, otherwise public RPCs.
    """

    def __init__(self):
        self._w3 = None
        self._rpc_url = self._get_rpc_url()

    def _get_rpc_url(self) -> str:
        api_key = os.getenv("ALCHEMY_API_KEY")
        if api_key:
            return f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
        return PUBLIC_RPC_ENDPOINTS[0]

    def _get_web3(self):
        if self._w3 is None:
            try:
                from web3 import Web3
                self._w3 = Web3(Web3.HTTPProvider(self._rpc_url))
            except ImportError:
                raise RuntimeError("web3 not installed — run: pip install web3")
        return self._w3

    # ── Price Feeds ────────────────────────────────────────────────────────

    async def get_price(self, pair: str) -> dict:
        """Get latest price from Chainlink oracle for a pair (e.g. 'ETH/USD')."""
        pair_upper = pair.upper()
        if "/" not in pair_upper:
            pair_upper = f"{pair_upper}/USD"

        address = PRICE_FEEDS.get(pair_upper)
        if not address:
            available = list(PRICE_FEEDS.keys())
            return {"error": f"No feed for '{pair_upper}'", "available": available}

        try:
            return await asyncio.to_thread(self._read_feed, address, pair_upper)
        except Exception as e:
            logger.warning(f"Chainlink on-chain read failed: {e}, trying HTTP fallback")
            return await self._http_fallback(pair_upper)

    def _read_feed(self, address: str, pair: str) -> dict:
        """Blocking web3 call — run in thread."""
        w3 = self._get_web3()
        import json as _json
        contract = w3.eth.contract(
            address=w3.to_checksum_address(address),
            abi=_json.loads(AGGREGATOR_ABI)
        )
        round_data = contract.functions.latestRoundData().call()
        decimals = contract.functions.decimals().call()

        _, answer, _, updated_at, _ = round_data
        price = answer / (10 ** decimals)
        age_seconds = int(time.time()) - updated_at

        return {
            "pair": pair,
            "price": price,
            "decimals": decimals,
            "updated_at": updated_at,
            "age_seconds": age_seconds,
            "feed_address": address,
            "source": "chainlink_onchain",
            "rpc": self._rpc_url.split("/v2/")[0],  # don't leak API key
        }

    async def _http_fallback(self, pair: str) -> dict:
        """Fallback: fetch price from CoinGecko if on-chain read fails."""
        coin_map = {
            "BTC/USD": "bitcoin", "ETH/USD": "ethereum",
            "LINK/USD": "chainlink", "SOL/USD": "solana",
            "MATIC/USD": "matic-network", "BNB/USD": "binancecoin",
        }
        coin_id = coin_map.get(pair)
        if not coin_id:
            return {"error": f"On-chain read failed and no fallback for {pair}"}

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"https://api.coingecko.com/api/v3/simple/price"
                    f"?ids={coin_id}&vs_currencies=usd"
                )
                data = r.json()
                price = data.get(coin_id, {}).get("usd", 0)
                return {
                    "pair": pair,
                    "price": price,
                    "source": "coingecko_fallback",
                    "note": "Chainlink on-chain read failed — using CoinGecko",
                }
        except Exception as e:
            return {"error": str(e), "pair": pair}

    # ── Feed Directory ─────────────────────────────────────────────────────

    def list_feeds(self) -> dict:
        """List all available Chainlink price feeds."""
        return {
            "feeds": list(PRICE_FEEDS.keys()),
            "count": len(PRICE_FEEDS),
            "categories": {
                "crypto": [k for k in PRICE_FEEDS if not k.startswith(("EUR", "GBP", "JPY", "XAU", "XAG"))],
                "forex":  [k for k in PRICE_FEEDS if k.startswith(("EUR", "GBP", "JPY"))],
                "commodities": [k for k in PRICE_FEEDS if k.startswith(("XAU", "XAG"))],
            },
            "network": "ethereum-mainnet",
            "rpc": "alchemy" if os.getenv("ALCHEMY_API_KEY") else "public",
        }

    async def get_multiple(self, pairs: list[str]) -> dict:
        """Get prices for multiple pairs concurrently."""
        tasks = [self.get_price(p) for p in pairs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            pair: (result if not isinstance(result, Exception) else {"error": str(result)})
            for pair, result in zip(pairs, results)
        }


# Module-level singleton
_chainlink_client: Optional[ChainlinkClient] = None


def get_chainlink_client() -> ChainlinkClient:
    global _chainlink_client
    if _chainlink_client is None:
        _chainlink_client = ChainlinkClient()
    return _chainlink_client
