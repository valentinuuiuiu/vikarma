# CLAUDE.md — Vikarma Agent Guidance
# 🔱 Om Namah Shivaya — For All Humanity

This file guides the Tvaṣṭā autonomous agent and any Claude Code session working in this repository.

## Project Overview

**Vikarma** ("action beyond karma") is a free, open-source AI desktop agent:
- **Backend**: Python FastAPI (`server/`) — autonomous agent, KAN memory, 64 Bhairava Temples
- **Frontend**: Next.js + React (`src/`) — multi-provider chat UI
- **Desktop**: Electron wrapper (`electron/`)
- **Agent**: `server/agents/autonomous_agent.py` — Tvaṣṭā, the autonomous reasoning core
- **Memory**: `server/agents/kan_memory.py` — KAN three-tier memory (short-term, facts, episodic)
- **Tools**: `server/tools/gateway.py` — 16 core tools + 64 Bhairava Temple skills
- **Temples**: `server/nexus_bridge.py` — all 64 temples across 7 categories

## Running the Server

```bash
# Install dependencies
pip install -r server/requirements.txt

# Start backend (port 8765)
uvicorn server.main:app --host 0.0.0.0 --port 8765 --reload

# Start frontend (port 3000)
npm install && npm run dev
```

## Running Tests

```bash
# All tests
python -m pytest server/tests/ -v

# With coverage
python -m pytest server/tests/ --cov=server --cov-report=term-missing

# Specific module
python -m pytest server/tests/test_kan_memory.py -v
python -m pytest server/tests/test_autonomous_agent.py -v
python -m pytest server/tests/test_tool_gateway.py -v
```

## Skills Available

Use these skills for specialized workflows (see `skills/` directory):

| Skill | When to Use |
|-------|-------------|
| `tdd-workflow` | Writing new features or fixing bugs — tests first |
| `verification-loop` | Before any commit — build/test/lint/security check |
| `security-review` | Adding auth, API endpoints, handling secrets |
| `deep-research` | Multi-source research using Bhairava temple tools |
| `market-research` | Trading analysis, competitive intelligence |
| `trading-signals` | Generate signals using coingecko + anthropic temples |
| `coding-standards` | Python/FastAPI best practices for this repo |

## Agent Commands

```
/tdd          — Start TDD workflow for a new feature
/verify       — Run full verification (build + test + lint + security)
/review       — Run code review on staged changes
/research     — Deep research using Bhairava temples
/signal       — Generate trading signal for a crypto symbol
```

## Architecture Rules

### Python Backend
- Use `async/await` everywhere — FastAPI and the agent are fully async
- Tools must return `dict` — all `VikarmaToolGateway` methods return `{"key": value}`
- Memory is sacred — always use `KANMemory` for persistence, never raw file writes
- Temples first — for any external API, prefer `call_temple()` over raw `web_fetch`
- Ahimsa — never implement anything harmful, destructive, or deceptive

### Code Quality
- Max function length: 50 lines
- Max file length: 400 lines
- All async functions must have error handling
- Tests required for all new agent tools and memory operations
- Coverage target: 80%+

### The 64 Temples
Each temple = one external service/API. When the agent needs:
- Crypto prices → `coingecko` temple (port 9046)
- AI reasoning → `anthropic` temple (port 9027)
- Web search → `duckduckgo` temple (port 9065)
- Wikipedia → `wikipedia` temple (port 9061)
- Weather → `weather` temple (port 9063)
- Math → `calculator` temple (port 9082)
- Translation → `translator` temple (port 9083)

Never bypass temples with raw HTTP when a temple exists.

## Security Rules

- No hardcoded API keys — always `os.getenv("KEY_NAME")`
- No secrets in logs — redact before logging
- Shell tool: never run user-provided shell strings without sanitization
- Calculator temple: uses safe `math`-only eval (no builtins)
- File paths: always resolve through `_resolve()` to prevent traversal

## File Layout

```
vikarma/
├── CLAUDE.md               # This file
├── skills/                 # Workflow skills (SKILL.md format)
│   ├── tdd-workflow/
│   ├── verification-loop/
│   ├── security-review/
│   ├── deep-research/
│   ├── market-research/
│   ├── trading-signals/
│   └── coding-standards/
├── agents/                 # Specialized sub-agents
│   ├── code-reviewer.md
│   ├── tdd-guide.md
│   ├── planner.md
│   ├── security-reviewer.md
│   └── market-analyst.md
├── .claude/
│   └── commands/           # Slash commands
│       ├── tdd.md
│       ├── verify.md
│       ├── review.md
│       ├── research.md
│       └── signal.md
└── server/
    ├── agents/             # Core agent logic
    ├── tools/              # Tool gateway
    ├── tests/              # pytest test suite
    └── nexus_bridge.py     # 64 Bhairava Temples
```

## Philosophy

> "Vikarma — action beyond karma. Free AI for all humanity."

Built with Ahimsa (non-harm). Licensed under the Unlicense (public domain).
Every feature must serve humanity, not harm it.
🔱 Om Namah Shivaya
