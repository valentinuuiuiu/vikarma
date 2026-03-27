"""
Alchemy Blockchain API Client — Temple 66
Full-featured client for Alchemy's enhanced blockchain APIs.
Supports: ETH, Polygon, Arbitrum, Optimism, Base, Solana.
Set ALCHEMY_API_KEY env var before using.
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

# ── Network configurations ─────────────────────────────────────────────────────

ALCHEMY_NETWORKS = {
    "ethereum":  "eth-mainnet",
    "eth":       "eth-mainnet",
    "mainnet":   "eth-mainnet",
    "polygon":   "polygon-mainnet",
    "matic":     "polygon-mainnet",
    "arbitrum":  "arb-mainnet",
    "arb":       "arb-mainnet",
    "optimism":  "opt-mainnet",
    "op":        "opt-mainnet",
    "base":      "base-mainnet",
    "solana":    "solana-mainnet",
    "sol":       "solana-mainnet",
    "sepolia":   "eth-sepolia",     # testnet
    "amoy":      "polygon-amoy",    # polygon testnet
}

ALCHEMY_BASE_URL = "https://{network}.g.alchemy.com/v2/{api_key}"
ALCHEMY_PRICES_URL = "https://api.g.alchemy.com/prices/v1/{api_key}"


class AlchemyClient:
    """
    Alchemy blockchain data client.
    Wraps JSON-RPC and Alchemy-enhanced REST APIs.

    Usage:
        client = AlchemyClient(api_key=os.getenv("ALCHEMY_API_KEY"))
        balance = await client.get_balance("0xAbCd...", network="ethereum")
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ALCHEMY_API_KEY", "")
        if not self.api_key:
            logger.warning("ALCHEMY_API_KEY not set — Alchemy temple will be limited")

    def _rpc_url(self, network: str = "ethereum") -> str:
        net_id = ALCHEMY_NETWORKS.get(network.lower(), network)
        return ALCHEMY_BASE_URL.format(network=net_id, api_key=self.api_key)

    async def _rpc(self, method: str, params: list, network: str = "ethereum") -> dict:
        """Execute a JSON-RPC call."""
        if not self.api_key:
            return {"error": "ALCHEMY_API_KEY not set — provide your key via /signal or set env var"}

        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(self._rpc_url(network), json=payload)
                data = r.json()
                if "error" in data:
                    return {"error": data["error"].get("message", str(data["error"]))}
                return {"result": data.get("result"), "method": method, "network": network}
        except Exception as e:
            return {"error": str(e), "method": method}

    async def _alchemy_get(self, path: str, params: dict = None) -> dict:
        """Call Alchemy REST API."""
        if not self.api_key:
            return {"error": "ALCHEMY_API_KEY not set"}
        url = f"{ALCHEMY_PRICES_URL.format(api_key=self.api_key)}/{path}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(url, params=params or {})
                return r.json()
        except Exception as e:
            return {"error": str(e)}

    # ── Balance & Account ──────────────────────────────────────────────────

    async def get_balance(self, address: str, network: str = "ethereum") -> dict:
        """Get native token balance (ETH/MATIC/etc.) for an address."""
        result = await self._rpc("eth_getBalance", [address, "latest"], network)
        if "error" in result:
            return result
        wei = int(result["result"], 16)
        eth = wei / 1e18
        return {
            "address": address,
            "network": network,
            "balance_wei": wei,
            "balance_eth": round(eth, 6),
            "symbol": "ETH" if network in ("ethereum", "eth", "mainnet") else "native",
        }

    async def get_token_balances(self, address: str, network: str = "ethereum") -> dict:
        """Get all ERC-20 token balances for an address."""
        result = await self._rpc(
            "alchemy_getTokenBalances",
            [address, "erc20"],
            network,
        )
        if "error" in result:
            return result
        tokens = result.get("result", {}).get("tokenBalances", [])
        # Filter out zero balances
        non_zero = [t for t in tokens if t.get("tokenBalance", "0x0") != "0x0"]
        return {
            "address": address,
            "network": network,
            "token_count": len(non_zero),
            "tokens": non_zero[:50],  # cap at 50
        }

    async def get_nfts(self, address: str, network: str = "ethereum") -> dict:
        """Get NFTs owned by an address."""
        result = await self._rpc(
            "alchemy_getNFTsForOwner",
            [address, {"withMetadata": False}],
            network,
        )
        if "error" in result:
            return result
        nfts = result.get("result", {})
        return {
            "address": address,
            "network": network,
            "total_count": nfts.get("totalCount", 0),
            "nfts": nfts.get("ownedNfts", [])[:20],  # cap at 20
        }

    # ── Transactions ───────────────────────────────────────────────────────

    async def get_asset_transfers(
        self,
        address: str,
        direction: str = "from",
        network: str = "ethereum",
        max_count: int = 10,
    ) -> dict:
        """Get transfer history (sent or received) for an address."""
        params = {
            "fromBlock": "0x0",
            "toBlock":   "latest",
            "withMetadata": False,
            "excludeZeroValue": True,
            "maxCount": hex(max_count),
            "category": ["external", "erc20", "erc721", "erc1155"],
        }
        if direction == "from":
            params["fromAddress"] = address
        else:
            params["toAddress"] = address

        result = await self._rpc("alchemy_getAssetTransfers", [params], network)
        if "error" in result:
            return result
        transfers = result.get("result", {}).get("transfers", [])
        return {
            "address": address,
            "direction": direction,
            "network": network,
            "count": len(transfers),
            "transfers": transfers,
        }

    async def get_transaction(self, tx_hash: str, network: str = "ethereum") -> dict:
        """Get transaction details by hash."""
        result = await self._rpc("eth_getTransactionByHash", [tx_hash], network)
        if "error" in result:
            return result
        tx = result.get("result")
        if not tx:
            return {"error": f"Transaction not found: {tx_hash}"}
        return {"transaction": tx, "network": network, "hash": tx_hash}

    async def get_transaction_receipt(self, tx_hash: str, network: str = "ethereum") -> dict:
        """Get transaction receipt (includes status, gas used, logs)."""
        result = await self._rpc("eth_getTransactionReceipt", [tx_hash], network)
        if "error" in result:
            return result
        receipt = result.get("result")
        if not receipt:
            return {"error": f"Receipt not found (tx may be pending): {tx_hash}"}
        status = "success" if receipt.get("status") == "0x1" else "failed"
        return {
            "hash": tx_hash,
            "status": status,
            "network": network,
            "gas_used": int(receipt.get("gasUsed", "0x0"), 16),
            "block_number": int(receipt.get("blockNumber", "0x0"), 16),
            "receipt": receipt,
        }

    # ── Block & Network ────────────────────────────────────────────────────

    async def get_block_number(self, network: str = "ethereum") -> dict:
        """Get current block number."""
        result = await self._rpc("eth_blockNumber", [], network)
        if "error" in result:
            return result
        block = int(result["result"], 16)
        return {"network": network, "block_number": block}

    async def get_gas_price(self, network: str = "ethereum") -> dict:
        """Get current gas price in Gwei."""
        result = await self._rpc("eth_gasPrice", [], network)
        if "error" in result:
            return result
        wei = int(result["result"], 16)
        gwei = wei / 1e9
        return {"network": network, "gas_price_wei": wei, "gas_price_gwei": round(gwei, 2)}

    async def get_fee_history(self, network: str = "ethereum") -> dict:
        """Get recent fee history for gas estimation."""
        result = await self._rpc(
            "eth_feeHistory",
            [10, "latest", [25, 50, 75]],
            network,
        )
        if "error" in result:
            return result
        return {"network": network, "fee_history": result.get("result")}

    # ── Token Prices (Alchemy Prices API) ─────────────────────────────────

    async def get_token_price(self, symbols: list[str]) -> dict:
        """Get token prices via Alchemy Prices API."""
        params = {"symbols": ",".join(symbols)}
        result = await self._alchemy_get("tokens/by-symbol", params)
        if "error" in result:
            return result
        return {"prices": result, "symbols": symbols, "source": "alchemy_prices"}

    async def get_token_price_by_address(
        self, address: str, network: str = "ethereum"
    ) -> dict:
        """Get token price by contract address."""
        net_id = ALCHEMY_NETWORKS.get(network.lower(), network)
        result = await self._alchemy_get(
            f"tokens/by-address",
            {"addresses[0][network]": net_id, "addresses[0][address]": address},
        )
        if "error" in result:
            return result
        return {"price_data": result, "address": address, "network": network}

    # ── Smart Contract ─────────────────────────────────────────────────────

    async def call_contract(
        self,
        contract_address: str,
        data: str,
        network: str = "ethereum",
    ) -> dict:
        """Make a read-only contract call (eth_call)."""
        result = await self._rpc(
            "eth_call",
            [{"to": contract_address, "data": data}, "latest"],
            network,
        )
        if "error" in result:
            return result
        return {
            "contract": contract_address,
            "result": result.get("result"),
            "network": network,
        }

    async def get_code(self, address: str, network: str = "ethereum") -> dict:
        """Get bytecode at an address (non-empty = smart contract)."""
        result = await self._rpc("eth_getCode", [address, "latest"], network)
        if "error" in result:
            return result
        code = result.get("result", "0x")
        return {
            "address": address,
            "network": network,
            "is_contract": code != "0x" and len(code) > 2,
            "bytecode_length": (len(code) - 2) // 2,
        }

    # ── Simulation ─────────────────────────────────────────────────────────

    async def simulate_transaction(
        self,
        from_address: str,
        to_address: str,
        data: str = "0x",
        value: int = 0,
        network: str = "ethereum",
    ) -> dict:
        """Simulate a transaction without broadcasting."""
        result = await self._rpc(
            "alchemy_simulateExecution",
            [{
                "from": from_address,
                "to": to_address,
                "data": data,
                "value": hex(value),
            }],
            network,
        )
        if "error" in result:
            return result
        return {"simulation": result.get("result"), "network": network}

    # ── Convenience ────────────────────────────────────────────────────────

    async def wallet_summary(self, address: str, network: str = "ethereum") -> dict:
        """Get a full wallet summary: balance + tokens + recent transfers."""
        balance, tokens, transfers = await asyncio.gather(
            self.get_balance(address, network),
            self.get_token_balances(address, network),
            self.get_asset_transfers(address, "to", network, max_count=5),
            return_exceptions=True,
        )
        return {
            "address": address,
            "network": network,
            "native_balance": balance if not isinstance(balance, Exception) else {"error": str(balance)},
            "tokens": tokens if not isinstance(tokens, Exception) else {"error": str(tokens)},
            "recent_incoming": transfers if not isinstance(transfers, Exception) else {"error": str(transfers)},
            "timestamp": time.time(),
        }

    def supported_networks(self) -> dict:
        return {"networks": list(ALCHEMY_NETWORKS.keys()), "count": len(ALCHEMY_NETWORKS)}


# Module-level singleton
_alchemy_client: Optional[AlchemyClient] = None


def get_alchemy_client() -> AlchemyClient:
    global _alchemy_client
    if _alchemy_client is None:
        _alchemy_client = AlchemyClient()
    return _alchemy_client
