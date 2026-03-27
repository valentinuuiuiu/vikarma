---
name: trading-signals
description: Generate trading signals for crypto assets by combining coingecko price data, news sentiment, and Claude AI analysis via Bhairava temples. Use when the user asks for a trading recommendation or signal.
origin: Vikarma-native
---

# Trading Signals — Rehoboam via Bhairava Temples

Generate actionable trading signals by orchestrating multiple data temples.

## When to Activate

- User asks "should I buy [token]?"
- User asks "what's the signal for BTC/ETH/SOL?"
- Automated signal generation in the Rehoboam trading loop
- User wants a market opinion on a specific asset

## Signal Generation Workflow

### Step 1: Get Price Data
```
<tool>temple</tool>
<params>{"temple": "coingecko", "action": "price", "params": {"coin": "bitcoin"}}</params>
```

Extract:
- `price_usd` — current price
- `usd_24h_change` — 24h % change
- `usd_24h_vol` — trading volume signal

### Step 2: Get News Sentiment
```
<tool>temple</tool>
<params>{"temple": "news_api", "action": "search", "params": {"query": "bitcoin market 2025"}}></params>
```

Or use web_search as fallback:
```
<tool>web_search</tool>
<params>{"query": "bitcoin news today sentiment 2025"}</params>
```

### Step 3: AI Synthesis
```
<tool>temple</tool>
<params>{
  "temple": "anthropic",
  "action": "analyze",
  "params": {
    "prompt": "Price: $X, 24h change: +X%, News: [summary]. Analyze: sentiment (bullish/bearish/neutral), confidence (0-100), key factors, signal (BUY/SELL/HOLD). Be concise."
  }
}</params>
```

### Step 4: Generate Final Signal

Signal logic (combine price + sentiment):
```
change > +5% AND bullish sentiment  → BUY  (confidence ~75)
change < -5% AND bearish sentiment  → SELL (confidence ~70)
otherwise                           → HOLD (confidence ~60)
```

Adjust confidence based on:
- Volume confirmation (+10 if volume spike)
- News strength (+10 if multiple bullish sources)
- Macro environment (+/-10 based on risk-on/off)

## Output Format

```
TRADING SIGNAL — [SYMBOL]
========================
Price:      $X,XXX.XX
24h Change: +/-X.X%

Signal:     [BUY / SELL / HOLD]
Confidence: [0-100]%

AI Analysis:
[2-3 sentence synthesis from anthropic temple]

Temples Used: coingecko, news_api, anthropic
Timestamp: [ISO timestamp]
Cache: [30s — data may be up to 30s old]

Risk Warning:
This is AI analysis, not financial advice.
Always do your own research. Trade responsibly.
🔱 Ahimsa — never risk what you cannot afford to lose.
```

## Integration with NexusBridge

The `NexusBridge.generate_trading_signal()` method implements this workflow in code:

```python
signal = await bridge.generate_trading_signal("bitcoin")
# Returns: signal, confidence, price, change, ai_analysis
```

Use the programmatic API for automated Rehoboam trading loops.
Use this skill for interactive user requests via the agent chat.

## Supported Assets

Any asset available on CoinGecko. Use the CoinGecko ID:
- Bitcoin → `bitcoin`
- Ethereum → `ethereum`
- Solana → `solana`
- BNB → `binancecoin`
- Cardano → `cardano`

## Ethics

- Never promise profits or guarantee returns
- Always include risk warning
- Ahimsa — no panic-selling content, no FOMO manipulation
- This is a research/analysis tool, not a licensed financial advisor
