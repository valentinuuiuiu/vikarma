---
name: deep-research
description: Multi-source research using Bhairava Temple tools. Searches the web, Wikipedia, arXiv, and news sources. Synthesizes findings into cited reports. Use when the user needs thorough, evidence-based research on any topic.
origin: ECC-adapted-for-Vikarma
---

# Deep Research — Using Bhairava Temples

Produce thorough, cited research by orchestrating multiple Bhairava Temple knowledge sources.

## When to Activate

- User says "research", "investigate", "deep dive", "what's the current state of"
- Competitive analysis or technology evaluation
- Market sizing or trend analysis
- Any question needing synthesis from multiple sources

## Temple Sources Available

| Temple | Best For |
|--------|----------|
| `wikipedia` | Factual background, definitions, history |
| `arxiv` | Academic papers, cutting-edge AI/finance research |
| `duckduckgo` | Privacy-first web search, broad coverage |
| `news_api` | Recent news, current events, market developments |
| `reddit` | Community sentiment, practitioner opinions |
| `stackoverflow` | Technical questions, code patterns |
| `coingecko` | Crypto market data, token information |
| `anthropic` | AI synthesis — summarize and connect findings |

## Research Workflow

### Step 1: Decompose the Question

Break into 3-5 sub-questions. Example:
- Topic: "Impact of LLM agents on financial trading"
  1. What are the current LLM-based trading systems?
  2. What academic research exists on AI trading performance?
  3. What are practitioners saying (Reddit, news)?
  4. What are the risks and limitations?
  5. Who are the key players and projects?

### Step 2: Execute Multi-Source Search

For each sub-question, use 2-3 temples:

```
<tool>temple</tool>
<params>{"temple": "duckduckgo", "action": "search", "params": {"query": "LLM agents financial trading 2025"}}</params>

<tool>temple</tool>
<params>{"temple": "arxiv", "action": "query", "params": {"query": "large language model algorithmic trading"}}</params>

<tool>temple</tool>
<params>{"temple": "wikipedia", "action": "algorithmic trading"}}</params>

<tool>temple</tool>
<params>{"temple": "news_api", "action": "headlines", "params": {"query": "AI trading bots 2025"}}></params>
```

### Step 3: Synthesize with Anthropic Temple

After gathering raw results, ask Claude to synthesize:

```
<tool>temple</tool>
<params>{
  "temple": "anthropic",
  "action": "synthesize",
  "params": {
    "prompt": "Here are findings from multiple sources about [topic]:\n\n[paste results]\n\nSynthesize into: key findings, evidence quality, gaps, and recommendation."
  }
}</params>
```

### Step 4: Store Key Facts in Memory

```
<tool>remember</tool>
<params>{"key": "research_[topic]_date", "value": "2026-03-27"}</params>

<tool>remember</tool>
<params>{"key": "research_[topic]_finding_1", "value": "[key finding]"}</params>
```

## Output Format

```
## Research: [Topic]
Date: [date]
Sources: [list of temples used]

### Key Findings
1. [Finding with source citation]
2. [Finding with source citation]
3. ...

### Evidence Quality
- Strong: [claims with multiple sources]
- Weak: [single source or old data]
- Missing: [what we couldn't find]

### Contrarian View
[Evidence that challenges the main narrative]

### Recommendation / Decision
[Actionable conclusion — not just a summary]

### Sources
- [URL or temple/query used for each claim]
```

## Research Quality Standards

1. Every important claim needs a source (which temple, which query)
2. Prefer recent data — flag anything older than 1 year
3. Include contrarian evidence
4. Separate fact, inference, and recommendation
5. End with a decision, not just a summary
