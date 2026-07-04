---
issue_id: issue-025
worker: codex
status: done
created: 2026-07-04
reviewed_by: []
---

## Summary

Implemented the node-graph editor and live monitor surface end to end: authored workflows now round-trip as YAML/JSON, the desktop snapshot carries workflow canvas state plus live node/edge overlays, and the frontend has a new canvas tab with author/run modes, node drill-in, and toast-based human-attention notifications.

## Changes

- Extended workflow persistence with dict serializers plus listing support so the canvas can author, save, and reload workflows through the existing OKF `agents/workflows/` seam.
- Added live workflow-state emission in `WorkflowRuntime` and repurposed `dashboard.snapshot()` to expose workflow canvas data, per-node drill-in details, edge state overlays, and accumulated notifications from the in-memory desktop session.
- Added desktop bridge methods for workflow save/run, with desktop-app orchestration that streams workflow updates into the existing `evaluate_js` push channel.
- Added a new frontend canvas tab with:
  - author mode for placing nodes, wiring guarded edges, toggling HITL/AFK, and saving YAML/JSON,
  - run mode for launching a saved workflow, reading node/edge run-state overlays, and drilling into gates, artifacts, transcript, and trace,
  - toast reuse for workflow notifications (`HITL needs input`, `node done + green`),
  - mock-data fallback so browser preview works without `pywebview`.
- Added focused backend tests for workflow serialization/listing, runtime live updates, snapshot canvas overlays, and the new desktop bridge workflow methods.

## Files Changed

- `frontend/src/App.jsx`
- `frontend/src/api.js`
- `frontend/src/components/Toast.jsx`
- `frontend/src/components/WorkflowCanvas.jsx`
- `frontend/src/mock.js`
- `hephaestus/dashboard.py`
- `hephaestus/desktop.py`
- `hephaestus/workflow_runtime.py`
- `hephaestus/workflows.py`
- `tests/test_dashboard.py`
- `tests/test_desktop_agent.py`
- `tests/test_workflow_runtime.py`
- `tests/test_workflows.py`

## Verification

- Focused TDD pass:
  `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest tests/test_workflows.py tests/test_workflow_runtime.py tests/test_dashboard.py tests/test_desktop_agent.py`
  Result: `21 passed`
- Full backend suite:
  `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest`
  Result: `209 passed, 5 warnings`
- Frontend production build:
  `C:\Program Files\nodejs\npm.cmd --prefix frontend ci`
  `C:\Program Files\nodejs\npm.cmd --prefix frontend run build`
  Result: Vite production build succeeded

## Notes

- Live `gh issue view 25 --repo zazin-20/hephustus` could not complete from this environment because outbound GitHub access is blocked by the sandbox, so implementation followed the provided issue body plus the local design docs and main-branch seams.
