---
description: Generate a trading signal for a crypto asset using coingecko + news + AI analysis via Bhairava temples.
---

Generate a trading signal for: $ARGUMENTS

Follow the `trading-signals` skill workflow using the `market-analyst` agent:

1. Fetch price data from `coingecko` temple: price, 24h change, volume
2. Get news context from `news_api` or `web_search`
3. Check sentiment from `reddit` temple
4. Synthesize with `anthropic` temple
5. Apply signal logic:
   - >+5% + bullish → BUY (~75% confidence)
   - <-5% + bearish → SELL (~70% confidence)
   - mixed → HOLD (~60% confidence)

Output the full signal report per `skills/trading-signals/SKILL.md`.
Always include: price, 24h change, signal, confidence, evidence, risk factors.
Always end with: "This is analysis, not financial advice. 🔱 Ahimsa."
