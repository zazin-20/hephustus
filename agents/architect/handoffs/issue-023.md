---
issue_id: issue-023
worker: codex
status: done
created: 2026-07-04
reviewed_by: []
---

## Summary

Implemented the gatekeeper workflow runtime that advances authored workflows node-by-node through `AgentService`, enforces entry and exit gates, and stops on HITL or ask-before-advance boundaries instead of leaking across nodes.

## Changes

- Extended the workflow model with per-edge `allow`/`ask` advance policy and per-placement `afk`/`hitl` interactivity while keeping the existing YAML/JSON round-trip behavior intact.
- Added `hephaestus.workflow_runtime.WorkflowRuntime`, which:
  - resolves and executes node runs one placement at a time,
  - creates persisted runs/contracts through the existing service seam,
  - blocks on missing required inputs,
  - repurposes `evaluate_spawn_gate` for exit-gate evaluation,
  - enforces output ArtifactSpec predicates and skill obligations,
  - pauses on HITL nodes and green `ask` edges.
- Added focused runtime tests covering:
  - a 2-node workflow advancing on a green gate,
  - blocking on a failing exit gate,
  - ask-before-advance pausing on a green gate,
  - HITL pause behavior.

## Files Changed

- `hephaestus/workflows.py`
- `hephaestus/workflow_runtime.py`
- `tests/test_workflow_runtime.py`

## Verification

- TDD tracer bullet: `tests/test_workflow_runtime.py` first failed on `ModuleNotFoundError: No module named 'hephaestus.workflow_runtime'` before the runtime was implemented.
- Focused workflow tests: `9 passed` via `C:/Users/kambala.jathin/Projects/hephustus/agents/.venv/Scripts/python.exe -m pytest tests/test_workflows.py tests/test_workflow_runtime.py -q`.
- Full suite: `201 passed, 5 warnings` via `C:/Users/kambala.jathin/Projects/hephustus/agents/.venv/Scripts/python.exe -m pytest`.
- Live GitHub issue fetch was attempted with `gh issue view 23 --repo zazin-20/hephustus` but blocked by sandboxed network access, so implementation followed the provided issue body.
