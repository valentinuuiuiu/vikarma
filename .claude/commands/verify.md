---
description: Run full verification gate before committing. Tests + coverage + security scan + import health check.
---

Run the Vikarma verification loop:

```bash
# Phase 1: Tests
python -m pytest server/tests/ -v --tb=short

# Phase 2: Coverage
python -m pytest server/tests/ --cov=server --cov-report=term-missing -q

# Phase 3: Security scan
grep -rn "api_key\s*=\s*['\"]" server/ --include="*.py" | grep -v "os.getenv\|environ\|test"

# Phase 4: Import health
python -c "
from server.nexus_bridge import TEMPLE_PORTS
from server.tools.gateway import VikarmaToolGateway
from server.agents.autonomous_agent import VikarmaAgent
print(f'OK — {len(TEMPLE_PORTS)} temples, all imports healthy')
"
```

Then produce a VERIFICATION REPORT with verdict: READY or NOT READY.
Format per `skills/verification-loop/SKILL.md`.
