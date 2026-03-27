---
name: market-research
description: Crypto and financial market research using coingecko, news_api, reddit, and anthropic temples. Produces decision-oriented market analysis with source attribution.
origin: ECC-adapted-for-Vikarma
---

# Market Research — Vikarma Trading Intelligence

Research that supports trading decisions, not research theater.

## When to Activate

- User asks about a crypto asset, market trend, or trading opportunity
- Building TAM/SAM analysis for a token or DeFi protocol
- Comparing exchanges or protocols
- Pressure-testing a thesis before entering a trade
- Due diligence on a project or team

## Data Sources (Temples)

| Temple | Data |
|--------|------|
| `coingecko` | Price, market cap, volume, 24h change |
| `binance` | Order book, recent trades, spot price |
| `news_api` | Market news, project announcements |
| `reddit` | Community sentiment (r/crypto, r/CryptoCurrency) |
| `twitter` | Social sentiment, influencer signals |
| `yahoo_finance` | Macro market context, equities correlation |
| `anthropic` | AI synthesis and pattern recognition |
| `wikipedia` | Project background, technology |
| `arxiv` | Academic research on DeFi/blockchain |

## Research Modes

### Quick Price Check
```
<tool>temple</tool>
<params>{"temple": "coingecko", "action": "price", "params": {"coin": "bitcoin"}}</params>
```

### Full Market Analysis
1. Get current price + 24h metrics from `coingecko`
2. Get recent news from `news_api`
3. Get community sentiment from `reddit`
4. Synthesize with `anthropic` temple

### Competitive Analysis (Protocol vs Protocol)
Collect for each:
- TVL, volume, fees (coingecko)
- Recent news (news_api)
- Community health (reddit)
- Technical differentiation (wikipedia + arxiv)

### Macro Context
```
<tool>temple</tool>
<params>{"temple": "yahoo_finance", "action": "macro", "params": {"query": "crypto market correlation S&P500"}}></params>
```

## Trading Signal Workflow

Use `trading-signals` skill for the actual signal generation.
This skill focuses on the research layer underneath.

### Research → Signal Pipeline

1. **Market Data** → coingecko: price, volume, change
2. **Sentiment** → news_api + reddit: bullish/bearish signals
3. **Macro** → yahoo_finance: risk-on/risk-off environment
4. **AI Analysis** → anthropic: connect the dots
5. **Signal** → Buy / Hold / Sell + confidence

## Output Format

```
## Market Research: [SYMBOL/TOPIC]
Date: [timestamp]

### Price Data (coingecko)
- Price: $X.XX
- 24h Change: +/-X.X%
- Market Cap: $XB
- Volume: $XM

### News Sentiment (news_api)
- Tone: [Bullish / Bearish / Neutral]
- Key stories:
  - "[headline]" — [source]

### Community Sentiment (reddit)
- Tone: [Bullish / Bearish / Neutral]
- Notable discussion: [summary]

### AI Synthesis (anthropic)
[2-3 sentence synthesis connecting all data points]

### Decision
Signal: [BUY / SELL / HOLD]
Confidence: [0-100]
Rationale: [1-2 sentences]
Risk factors: [what could invalidate this]
```

## Standards

1. Timestamp all data — crypto moves fast
2. Note which data is real-time vs cached (30s cache in NexusBridge)
3. Always include a risk factor / downside case
4. Never recommend specific position sizes
5. Ahimsa — no manipulation tactics, no FOMO engineering
