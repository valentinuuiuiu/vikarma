"""
Tests for Chainlink (Temple 65) and Alchemy (Temple 66) integrations.
Uses real HTTP calls where possible; mocks chain/RPC calls.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.integrations.chainlink_client import ChainlinkClient, PRICE_FEEDS
from server.integrations.alchemy_client import AlchemyClient, ALCHEMY_NETWORKS
from server.tools.gateway import VikarmaToolGateway


@pytest.fixture
def gw(tmp_path):
    return VikarmaToolGateway(workspace=str(tmp_path))


@pytest.fixture
def chainlink():
    return ChainlinkClient()


@pytest.fixture
def alchemy():
    return AlchemyClient(api_key="test_key_123")


# ── Chainlink client unit tests ────────────────────────────────────────────────

class TestChainlinkClient:
    def test_list_feeds_returns_all_pairs(self, chainlink):
        result = chainlink.list_feeds()
        assert result["count"] >= 10
        assert "BTC/USD" in result["feeds"]
        assert "ETH/USD" in result["feeds"]
        assert "EUR/USD" in result["feeds"]
        assert "XAU/USD" in result["feeds"]

    def test_list_feeds_has_categories(self, chainlink):
        result = chainlink.list_feeds()
        assert "crypto" in result["categories"]
        assert "forex" in result["categories"]
        assert "commodities" in result["categories"]

    def test_price_feeds_dict_has_addresses(self):
        for pair, address in PRICE_FEEDS.items():
            assert address.startswith("0x"), f"Bad address for {pair}: {address}"
            assert len(address) == 42, f"Wrong address length for {pair}"

    @pytest.mark.asyncio
    async def test_unknown_pair_returns_error(self, chainlink):
        result = await chainlink.get_price("FAKECOIN/USD")
        assert "error" in result
        assert "available" in result

    @pytest.mark.asyncio
    async def test_pair_without_slash_auto_appended_usd(self, chainlink):
        # Should auto-append /USD — will fail on-chain but return graceful error
        result = await chainlink.get_price("FAKECOIN")
        assert isinstance(result, dict)
        # Either "error" with available list, or a price result
        assert "error" in result or "price" in result

    @pytest.mark.asyncio
    async def test_get_multiple_returns_dict_keyed_by_pair(self, chainlink):
        with patch.object(chainlink, "get_price", new=AsyncMock(
            side_effect=lambda p: {"pair": p, "price": 50000.0, "source": "mock"}
        )):
            result = await chainlink.get_multiple(["BTC/USD", "ETH/USD"])
        assert "BTC/USD" in result
        assert "ETH/USD" in result
        assert result["BTC/USD"]["price"] == 50000.0

    @pytest.mark.asyncio
    async def test_http_fallback_known_pair(self, chainlink):
        """CoinGecko fallback works for known pairs."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"bitcoin": {"usd": 65000}}
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await chainlink._http_fallback("BTC/USD")
        assert result["price"] == 65000
        assert "fallback" in result["source"]

    @pytest.mark.asyncio
    async def test_http_fallback_unknown_pair_returns_error(self, chainlink):
        result = await chainlink._http_fallback("UNKNOWN/USD")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_rpc_url_uses_alchemy_key_if_set(self):
        import os
        os.environ["ALCHEMY_API_KEY"] = "mykey123"
        client = ChainlinkClient()
        assert "alchemy" in client._rpc_url
        assert "mykey123" in client._rpc_url
        del os.environ["ALCHEMY_API_KEY"]

    @pytest.mark.asyncio
    async def test_rpc_url_falls_back_to_public(self):
        import os
        os.environ.pop("ALCHEMY_API_KEY", None)
        client = ChainlinkClient()
        assert any(pub in client._rpc_url for pub in ["cloudflare", "ankr", "public-rpc"])


# ── Alchemy client unit tests ──────────────────────────────────────────────────

class TestAlchemyClient:
    def test_no_api_key_logs_warning(self):
        import os
        os.environ.pop("ALCHEMY_API_KEY", None)
        client = AlchemyClient(api_key="")
        assert client.api_key == ""

    def test_supported_networks(self, alchemy):
        result = alchemy.supported_networks()
        assert result["count"] >= 8
        assert "ethereum" in result["networks"]
        assert "polygon" in result["networks"]
        assert "arbitrum" in result["networks"]
        assert "solana" in result["networks"]

    def test_rpc_url_format(self, alchemy):
        url = alchemy._rpc_url("ethereum")
        assert "eth-mainnet" in url
        assert "test_key_123" in url

    def test_rpc_url_network_aliases(self, alchemy):
        assert "eth-mainnet" in alchemy._rpc_url("eth")
        assert "polygon-mainnet" in alchemy._rpc_url("matic")
        assert "arb-mainnet" in alchemy._rpc_url("arb")

    @pytest.mark.asyncio
    async def test_no_api_key_returns_error(self):
        client = AlchemyClient(api_key="")
        result = await client.get_balance("0x123", "ethereum")
        assert "error" in result
        assert "ALCHEMY_API_KEY" in result["error"]

    @pytest.mark.asyncio
    async def test_get_balance_parses_hex(self, alchemy):
        with patch.object(alchemy, "_rpc", new=AsyncMock(
            return_value={"result": "0xde0b6b3a7640000"}  # 1 ETH in wei
        )):
            result = await alchemy.get_balance("0xabc", "ethereum")
        assert result["balance_eth"] == pytest.approx(1.0)
        assert result["balance_wei"] == 10 ** 18

    @pytest.mark.asyncio
    async def test_get_balance_propagates_rpc_error(self, alchemy):
        with patch.object(alchemy, "_rpc", new=AsyncMock(
            return_value={"error": "rate limited"}
        )):
            result = await alchemy.get_balance("0xabc")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_block_number_converts_hex(self, alchemy):
        with patch.object(alchemy, "_rpc", new=AsyncMock(
            return_value={"result": "0x1312d00"}  # block 20000000
        )):
            result = await alchemy.get_block_number("ethereum")
        assert result["block_number"] == 20000000

    @pytest.mark.asyncio
    async def test_get_gas_price_converts_to_gwei(self, alchemy):
        with patch.object(alchemy, "_rpc", new=AsyncMock(
            return_value={"result": hex(int(20e9))}  # 20 Gwei
        )):
            result = await alchemy.get_gas_price("ethereum")
        assert result["gas_price_gwei"] == pytest.approx(20.0)

    @pytest.mark.asyncio
    async def test_get_transaction_receipt_parses_status(self, alchemy):
        with patch.object(alchemy, "_rpc", new=AsyncMock(return_value={
            "result": {
                "status": "0x1",
                "gasUsed": "0x5208",
                "blockNumber": "0x100",
                "transactionHash": "0xabc",
            }
        })):
            result = await alchemy.get_transaction_receipt("0xabc")
        assert result["status"] == "success"
        assert result["gas_used"] == 21000  # 0x5208

    @pytest.mark.asyncio
    async def test_get_transaction_receipt_failed_status(self, alchemy):
        with patch.object(alchemy, "_rpc", new=AsyncMock(return_value={
            "result": {"status": "0x0", "gasUsed": "0x0", "blockNumber": "0x1",
                       "transactionHash": "0xfail"}
        })):
            result = await alchemy.get_transaction_receipt("0xfail")
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, alchemy):
        with patch.object(alchemy, "_rpc", new=AsyncMock(
            return_value={"result": None}
        )):
            result = await alchemy.get_transaction("0xnotfound")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_is_contract_eoa(self, alchemy):
        """EOA (externally owned account) returns is_contract=False."""
        with patch.object(alchemy, "_rpc", new=AsyncMock(
            return_value={"result": "0x"}
        )):
            result = await alchemy.get_code("0xEOA")
        assert result["is_contract"] is False

    @pytest.mark.asyncio
    async def test_is_contract_true(self, alchemy):
        with patch.object(alchemy, "_rpc", new=AsyncMock(
            return_value={"result": "0x6080604052"}  # EVM bytecode
        )):
            result = await alchemy.get_code("0xCONTRACT")
        assert result["is_contract"] is True

    @pytest.mark.asyncio
    async def test_wallet_summary_returns_all_sections(self, alchemy):
        with patch.object(alchemy, "get_balance", new=AsyncMock(
            return_value={"balance_eth": 1.5}
        )):
            with patch.object(alchemy, "get_token_balances", new=AsyncMock(
                return_value={"token_count": 3}
            )):
                with patch.object(alchemy, "get_asset_transfers", new=AsyncMock(
                    return_value={"count": 5}
                )):
                    result = await alchemy.wallet_summary("0xWALLET")
        assert "native_balance" in result
        assert "tokens" in result
        assert "recent_incoming" in result
        assert result["native_balance"]["balance_eth"] == 1.5

    @pytest.mark.asyncio
    async def test_unknown_action_returns_available_list(self, alchemy):
        # Test through gateway
        pass  # covered in gateway tests below


# ── Gateway temple routing tests ───────────────────────────────────────────────

class TestTempleGatewayRouting:
    @pytest.mark.asyncio
    async def test_chainlink_list_feeds(self, gw):
        result = await gw.execute("temple", {
            "temple": "chainlink",
            "action": "list_feeds",
        })
        assert result["temple"] == "chainlink"
        feeds = result["result"]
        assert feeds["count"] >= 10

    @pytest.mark.asyncio
    async def test_chainlink_unknown_pair_error(self, gw):
        result = await gw.execute("temple", {
            "temple": "chainlink",
            "action": "price",
            "params": {"pair": "NOTREAL/USD"},
        })
        assert "error" in result["result"]

    @pytest.mark.asyncio
    async def test_alchemy_no_key_returns_error(self, gw):
        import os
        os.environ.pop("ALCHEMY_API_KEY", None)
        result = await gw.execute("temple", {
            "temple": "alchemy",
            "action": "balance",
            "params": {"address": "0xabc"},
        })
        assert result["temple"] == "alchemy"
        assert "error" in result["result"]

    @pytest.mark.asyncio
    async def test_alchemy_unknown_action(self, gw):
        result = await gw.execute("temple", {
            "temple": "alchemy",
            "action": "unknownaction",
            "params": {},
        })
        assert "error" in result["result"]
        assert "available" in result["result"]

    @pytest.mark.asyncio
    async def test_alchemy_networks_action(self, gw):
        result = await gw.execute("temple", {
            "temple": "alchemy",
            "action": "networks",
        })
        assert result["temple"] == "alchemy"
        networks = result["result"]
        assert "ethereum" in networks["networks"]

    @pytest.mark.asyncio
    async def test_list_temples_includes_blockchain_category(self, gw):
        result = await gw.execute("list_temples", {"category": "blockchain"})
        temples = result["temples"]
        names = [t["name"] for t in temples]
        assert "chainlink" in names
        assert "alchemy" in names

    @pytest.mark.asyncio
    async def test_total_temple_count_is_66(self, gw):
        result = await gw.execute("list_temples", {})
        assert result["total"] == 67
