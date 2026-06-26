---
issue_id: issue-011
worker: codex
status: done
created: 2026-06-23
reviewed_by: []
---

## Summary

Normalized the agent-turn vocabulary so runner events, transcript persistence, the desktop bridge, and the frontend all read from one shared event taxonomy instead of duplicating `kind`-based classification logic.

## Changes

- Added `hephaestus/integration/turns.py` to define shared turn categories, transcript roles, labels, conversation visibility, and persistence behavior.
- Extended `AgentEvent` to carry normalized metadata automatically.
- Switched `AgentService.run()` persistence and trace routing to the carried metadata instead of ad hoc `kind` checks.
- Enriched desktop transcript rows and live bridge events with normalized fields for the frontend.
- Updated the React coordinator and raw run view to classify from carried categories.

## Files Changed

- `hephaestus/integration/turns.py`
- `hephaestus/integration/runners.py`
- `hephaestus/integration/service.py`
- `hephaestus/desktop.py`
- `frontend/src/components/Coordinator.jsx`
- `frontend/src/components/RunAgent.jsx`
- `tests/test_integration.py`
- `tests/test_desktop_agent.py`

## Verification

- Focused contract tests: `.\venv\Scripts\python.exe -m pytest tests\test_integration.py tests\test_desktop_agent.py --basetemp tmp_pytest\issue11-focused -o cache_dir=tmp_pytest\cache-issue11-focused`
- Result: `35 passed`.
- Full suite: `173 passed`.
- Frontend build: `cmd /c npm --prefix frontend run build`.

## Notes

- The desktop-only `done` signal remains a transport sentinel and was not folded into the shared turn taxonomy.
- No database migration was required; normalization was added as a code seam over existing persisted `role` and `kind` fields.
