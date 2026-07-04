---
task: T-doc-drift-governance
role: architect
status: completed
created: 2026-07-04
completed: 2026-07-04
owner: orchestrator
---

**Result:** README.md, structural.md, architecture.md, architect/log.md
reconciled to the governance-engine model. S-rules kept only as dated History.
No .py touched. Suite: 211 passed. Follow-ups spun out (role-doc S-rule refs,
issue-lifecycle model drift, duplicate governance-engine-revised.md).


# Task: Reconcile S-rule doc drift with the governance-engine reality

## Goal
Docs still describe the removed hardcoded S-001..S-006 structural rules and a
stale "27 tests" count. Reconcile README.md / structural.md / architecture.md to
the current model: no built-in ruleset; governance = user-authored specs +
G-001/G-002/G-003 (`rules/governance.py`), runner in `rules/registry.py`.

## Why (routing)
Architecture/spec-doc reconciliation → Architect (static route). Surfaced by the
QA full-surface survey (`agents/qa/test-plan.md`).

## Confirmed drift (verified against code)
- README `rules/structural.py S-001 .. S-006` → no such file; it's
  `governance.py` (G-rules) + `registry.py` (no default set).
- README "27 tests" → suite is now 211.
- README Status table "Structural rules S-001..S-006 ✅" → stale.
- structural.md / architecture.md still present S-rules as the rule library.

## Constraints
- Docs only. Do not change product code or rule behavior.
- Canonical source of truth: `docs/design/governance-engine.md`.

## Dispatch
- Agent: general-purpose (fresh context), carrying `agents/architect/architect.md`.
