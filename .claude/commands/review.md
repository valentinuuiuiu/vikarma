---
description: Run code review on staged/recent changes using the code-reviewer agent.
---

Run a code review on the current changes using the `code-reviewer` agent pattern:

```bash
git diff --staged
git diff HEAD~1 --name-only
```

Apply the Vikarma code review checklist from `agents/code-reviewer.md`:
- CRITICAL: secrets, non-async I/O, shell injection, path traversal, unsafe eval
- HIGH: missing error dicts, missing type hints, unclosed resources, missing tests
- MEDIUM: functions >50 lines, print() instead of logger, magic strings
- LOW: naming, docstrings, TODOs

Output the Review Summary table and a clear verdict:
- APPROVE (no critical/high)
- WARNING (high issues — merge with caution)
- BLOCK (critical issues — fix required)
