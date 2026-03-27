---
name: tdd-workflow
description: Use when writing new agent tools, memory operations, or server features. Enforces Python TDD with pytest — write tests first, then implementation. 80%+ coverage required.
origin: ECC-adapted-for-Vikarma
---

# TDD Workflow — Vikarma Python Edition

Write tests before code. Always. No exceptions.

## When to Activate

- Adding a new tool to `VikarmaToolGateway`
- Adding a new temple fallback to `NexusBridge`
- Adding memory operations to `KANMemory`
- Fixing bugs in the agent loop
- Adding new API endpoints to `server/main.py`

## Workflow

### Step 1: Write the User Story
```
As Tvaṣṭā, I want to [action],
so that [benefit for the user / system].

Example:
As Tvaṣṭā, I want to call the `translator` temple with a phrase and target language,
so that I can respond to users in their native language.
```

### Step 2: Write Failing Tests First

```python
# server/tests/test_tool_gateway.py

@pytest.mark.asyncio
async def test_translator_temple_returns_translation(gw):
    result = await gw.execute("temple", {
        "temple": "translator",
        "action": "translate",
        "params": {"text": "hello", "target_lang": "es"}
    })
    assert "error" not in result
    assert result["temple"] == "translator"

@pytest.mark.asyncio
async def test_translator_temple_handles_missing_text(gw):
    result = await gw.execute("temple", {
        "temple": "translator",
        "action": "translate",
        "params": {}
    })
    # Should return something, not crash
    assert isinstance(result, dict)
```

### Step 3: Run Tests — They Should Fail
```bash
python -m pytest server/tests/ -v -k "translator"
# FAILED — expected, we haven't implemented yet
```

### Step 4: Implement Minimal Code
Write the smallest change that makes tests pass. No extras.

### Step 5: Run Tests — They Should Pass
```bash
python -m pytest server/tests/ -v -k "translator"
# PASSED
```

### Step 6: Refactor
Improve without breaking tests:
- Remove duplication
- Better naming
- Add type hints
- Improve error messages

### Step 7: Check Coverage
```bash
python -m pytest server/tests/ --cov=server --cov-report=term-missing
# Target: 80%+ coverage
```

## Test Patterns for Vikarma

### Async Tool Test Pattern
```python
@pytest.fixture
def gw(tmp_path):
    return VikarmaToolGateway(workspace=str(tmp_path))

@pytest.mark.asyncio
async def test_my_tool(gw):
    result = await gw.execute("my_tool", {"param": "value"})
    assert result["success"] is True
```

### Agent Tool Call Test Pattern
```python
@pytest.mark.asyncio
async def test_agent_uses_temple(mem):
    temple_call = '<tool>temple</tool><params>{"temple": "calculator", "action": "2+2", "params": {"expression": "2+2"}}</params>'
    final = "The answer is 4."

    agent = VikarmaAgent(AsyncMock(), VikarmaToolGateway(), mem)
    agent._call_ai = AsyncMock(side_effect=[temple_call, final])

    result = await agent.run("What is 2+2?")
    assert result == final
```

### Memory Test Pattern
```python
def test_fact_survives_reload(tmp_path):
    mem = KANMemory(storage_dir=str(tmp_path))
    mem.remember_fact("language", "Python")

    mem2 = KANMemory(storage_dir=str(tmp_path))
    results = mem2.recall_fact("language")
    assert any(f["value"] == "Python" for f in results)
```

### Temple Fallback Test Pattern
```python
@pytest.mark.asyncio
async def test_temple_fallback_no_crash():
    bridge = NexusBridge()
    result = await bridge.call_temple("calculator", "1+1", {"expression": "1+1"})
    assert "error" not in result
    assert result["result"] == 2
```

## Coverage Requirements

```bash
# Run with coverage
python -m pytest server/tests/ \
  --cov=server \
  --cov-report=term-missing \
  --cov-fail-under=80
```

Minimum 80% coverage on:
- `server/agents/autonomous_agent.py`
- `server/agents/kan_memory.py`
- `server/tools/gateway.py`
- `server/nexus_bridge.py`

## Mocking External APIs

### Mock Temple HTTP calls
```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_coingecko_temple(gw):
    mock_response = {"bitcoin": {"usd": 50000, "usd_24h_change": 2.5}}
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value.json = AsyncMock(return_value=mock_response)
        result = await gw.execute("temple", {
            "temple": "coingecko",
            "action": "price",
            "params": {"coin": "bitcoin"}
        })
    assert result["temple"] == "coingecko"
```

### Mock AI provider
```python
agent._call_ai = AsyncMock(return_value="Final answer without tool tags")
result = await agent.run("task")
assert result == "Final answer without tool tags"
```

## Success Criteria

- All tests pass (`pytest server/tests/ -v`)
- Coverage ≥ 80% (`--cov-fail-under=80`)
- No skipped tests
- New feature has at least: 1 happy path, 1 error path, 1 edge case
- Tests run in < 5 seconds total (mock external APIs)
