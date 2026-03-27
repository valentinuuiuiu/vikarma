---
name: verification-loop
description: Run before every commit. Full quality gate: tests, lint, type check, security scan, diff review. Produces a READY/NOT READY verdict.
origin: ECC-adapted-for-Vikarma
---

# Verification Loop — Vikarma

Run this before every commit or PR. No exceptions.

## When to Activate

- Before `git commit`
- Before creating a PR
- After completing a feature
- After any refactor of agent/memory/tools

## Verification Phases

### Phase 1: Tests
```bash
python -m pytest server/tests/ -v --tb=short
```
If ANY test fails — STOP. Fix before continuing.

Report:
- Tests passed: X / total
- Tests failed: list them

### Phase 2: Coverage
```bash
python -m pytest server/tests/ --cov=server --cov-report=term-missing -q
```
Target: 80%+. Below 70% = NOT READY.

### Phase 3: Type Hints Check
```bash
# Check for missing type hints in new code
grep -n "^def \|^async def " server/agents/*.py server/tools/*.py | grep -v "->.*:" | head -20
```
Flag functions missing return type annotations.

### Phase 4: Security Scan
```bash
# Check for hardcoded secrets
grep -rn "api_key\s*=\s*['\"]" server/ --include="*.py" | grep -v "os.getenv\|environ\|test\|example"

# Check for unsafe eval (not our safe calculator)
grep -rn "\beval(" server/ --include="*.py" | grep -v "nexus_bridge\|# noqa"

# Check for shell injection risk
grep -rn "shell=True\|os.system\|subprocess.call" server/ --include="*.py"
```

### Phase 5: Import Health
```bash
python -c "
import server.main
from server.agents.autonomous_agent import VikarmaAgent
from server.agents.kan_memory import KANMemory
from server.tools.gateway import VikarmaToolGateway
from server.nexus_bridge import NexusBridge, TEMPLE_PORTS
print(f'All imports OK — {len(TEMPLE_PORTS)} temples loaded')
"
```

### Phase 6: Diff Review
```bash
git diff --stat
git diff HEAD --name-only
```
Review each changed file for:
- Unintended changes
- Missing error handling
- TODO/FIXME without context

## Output Format

```
VIKARMA VERIFICATION REPORT
============================

Tests:     [PASS/FAIL]  (X/Y passed)
Coverage:  [PASS/FAIL]  (X% — target 80%)
Security:  [PASS/FAIL]  (X issues found)
Imports:   [PASS/FAIL]  (X temples loaded)
Diff:      [X files changed]

Verdict:   [READY / NOT READY] to commit

Blockers:
1. ...
2. ...
```

## Quick Run (Copy-Paste)

```bash
python -m pytest server/tests/ -q && \
python -m pytest server/tests/ --cov=server -q && \
python -c "from server.nexus_bridge import TEMPLE_PORTS; print(f'{len(TEMPLE_PORTS)} temples OK')" && \
echo "READY"
```
