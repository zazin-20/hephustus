---
task: T-doc-drift-linkfix
role: architect
status: dispatched
created: 2026-07-04
owner: orchestrator
---

# Task: Fix dead structural.md links + one stale index.md line

## Goal
Final tidy pass on the S-rule doc reconciliation. `structural.md` lives ONLY at
the repo root, but several docs link to it via wrong relative paths. Fix them,
plus the root `index.md` "built-in compliance rules" wording.

## Fixes (mechanical, verified locations)
- `agents/architect/architect.md:42,61` — `rules/structural.md` → `../../structural.md`
- `agents/qa/claude.md:38` — `../architect/rules/structural.md` → `../../structural.md`
- `index.md` (repo root) `:103` — `../spec/rules/structural.md` → `structural.md`,
  and reword "built-in compliance rules" → the governance model.
- `log.md:31` — LEAVE (inside a dated historical entry; accurate point-in-time).

## Constraints
- Docs only. No `.py`. Verify each fixed link resolves to an existing file.
- Append a dated entry to `agents/architect/log.md`.

## Dispatch
- Agent: general-purpose (fresh context), carrying `agents/architect/architect.md`.
