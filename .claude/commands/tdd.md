---
description: Start TDD workflow for a new Vikarma feature. Writes failing tests first, then guides implementation.
---

Activate the `tdd-workflow` skill for the following feature: $ARGUMENTS

Follow the TDD workflow exactly:
1. Understand the feature and identify the correct test file
2. Write failing tests first (happy path + error path + edge case)
3. Run tests to confirm they fail
4. Guide implementation to make tests pass
5. Run full test suite to confirm nothing broke
6. Check coverage meets 80% threshold

Use the `tdd-guide` agent pattern for this workflow.
