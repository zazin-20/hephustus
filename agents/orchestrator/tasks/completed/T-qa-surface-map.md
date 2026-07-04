---
task: T-qa-surface-map
role: qa
status: completed
created: 2026-07-04
completed: 2026-07-04
owner: orchestrator
---

**Result:** `agents/qa/test-plan.md` — 20 flows, ~22 components, 107 test cases
(`TC-<AREA>-<NNN>`). Suite green (211 unit tests). QA-owned test homes empty →
integration/e2e/security/UI are all real gaps.


# Task: Map testable surface + author test-case catalog

## Goal
Before any new feature work, produce a complete map of the interaction flows and
components that currently need testing, and create the best-suited doc to hold
the generated test cases.

## Why (routing)
Verification work → QA (static route, `hephaestus/integration/routing.py`).
This is an Orchestrator-authorized **full-surface survey**, not per-issue
verification — it intentionally runs outside the normal S-005 handoff gate.

## Deliverables
1. A map of every interaction flow and component under test (what exists today).
2. A test-case catalog doc — QA chooses the best-suited format — populated with
   concrete test cases, stored in the QA tree.

## Dispatch
- Agent: general-purpose (fresh context, full tools).
- Carries QA directive (`agents/qa/claude.md`).
