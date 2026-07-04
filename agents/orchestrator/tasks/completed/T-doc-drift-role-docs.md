---
task: T-doc-drift-role-docs
role: architect
status: completed
created: 2026-07-04
completed: 2026-07-04
owner: orchestrator
---

**Result:** 9 role/coordinator docs reconciled; S-rule IDs historicized, live
paths (okf_layout.py) + reviewed_by-gate-as-convention kept. No .py touched.
Follow-ups: dead `rules/structural.md` relative links in architect.md/qa/claude.md/
index.md/log.md; root index.md still says "built-in compliance rules";
qa/test-plan.md S-rule refs. See T-doc-drift-linkfix (proposed).


# Task: Finish S-rule drift cleanup across role + coordinator docs

## Goal
Follow-up to T-doc-drift-governance. The S-001..S-006 rules were removed from
code, but role docs and some spec docs still cite them as live/code-enforced.
Reconcile the remaining references so no doc claims a removed rule ID is
currently enforced — while preserving behavior that IS still real.

## Why (routing)
Architecture/spec + role-doc reconciliation → Architect (static route).
Surfaced by T-doc-drift-governance report.

## In scope (files flagged)
- `agents/architect/architect.md`, `agents/architect/index.md`
- `agents/worker/` role docs, `agents/qa/` role docs
- `architecture-coordinator.md`, `prd-coordinator.md`
- system-level `log.md`

## Critical nuance
Some references point at behavior that is STILL real (e.g. `okf_layout.py`
still consumes `evidence/{issue_id}.md`; the QA "reviewed_by: architect" gate may
be a live process convention even if no S-rule enforces it in code). Verify each
S-rule reference against code before rewriting — distinguish removed *rule IDs*
from still-live *behavior/paths*.

## Constraints
- Docs only. No `.py` changes. Canonical source: `docs/design/governance-engine.md`.
- Append a dated entry to `agents/architect/log.md`.

## Dispatch
- Agent: general-purpose (fresh context), carrying `agents/architect/architect.md`.
