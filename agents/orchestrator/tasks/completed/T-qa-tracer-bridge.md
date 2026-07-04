---
task: T-qa-tracer-bridge
role: qa
status: completed
created: 2026-07-04
completed: 2026-07-04
owner: orchestrator
---

**Result:** 18 bridge/security integration tests in agents/qa/tests/integration/
(all green; root suite still 211). No bugs, no product code touched. Covers
TC-DESK-*, TC-SEC-001, TC-CODE-006. Follow-ups: (1) testpaths→Architect so QA
tests join default suite; (2) next slices = provider-mocked run lifecycle, then
Playwright e2e.


# Task: QA tracer slice — desktop Bridge / js_api integration coverage

## Goal
Begin closing gap #1 (UI/desktop, zero coverage). Land a RUNNABLE tracer slice
of real integration tests against the `desktop.py` Bridge (the UI↔core js_api
contract, ~25 methods) — a green harness + a handful of real cases, not all 107.

## Why (routing)
Verification / test authoring → QA (owns `tests/`). Gap surfaced by
`agents/qa/test-plan.md`. Bridge is Python-testable today (no browser), unlike
Playwright for this pywebview app — fastest ROI tracer.

## Scope
- Tracer only: harness + ~5-10 real cases against no-live-call Bridge methods
  (get_state/rescan, get_catalog, list_rules, list_repos/tree/read_file incl. a
  path-traversal security case, parse_handoff_marker, evaluate_spawn,
  save_workflow+list_workflows round-trip, node/thread/correction store).
- run_agent/send_message/run_workflow spawn live providers — DEFER or fake; no
  live LLM calls this pass.

## Known constraint (flag, don't fix)
`pyproject.toml testpaths=["tests"]` → tests under `agents/qa/tests/` are NOT
auto-discovered. Put tracer tests in `agents/qa/tests/integration/`, make them
runnable via an explicit pytest path, document the command. Whether to add the
QA tree to testpaths is an Architect/config call — flag it, don't edit pyproject.

## Guardrails
- No product code edits (`hephaestus/*.py`, `pyproject.toml`). Bug found → file
  under `agents/qa/bug-report/`, report, don't fix.
- venv python only: `agents/.venv/Scripts/python.exe -m pytest`.

## Dispatch
- Agent: general-purpose (fresh context), carrying `agents/qa/claude.md`.
