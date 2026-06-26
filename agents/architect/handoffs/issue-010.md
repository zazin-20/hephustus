---
issue_id: issue-010
worker: codex
status: done
created: 2026-06-23
reviewed_by: []
---

## Summary

Introduced a shared OKF layout seam so the repository shape for `agents/` and related artifacts is defined in one place instead of being re-derived across modules.

## Changes

- Added `hephaestus/okf_layout.py` as the single layout source.
- Routed workspace, indexing, watcher, identity, integration-context, and profile code through the shared layout helpers.
- Added focused coverage for layout paths and the affected consumers.

## Files Changed

- `hephaestus/okf_layout.py`
- `hephaestus/workspace.py`
- `hephaestus/index.py`
- `hephaestus/watch.py`
- `hephaestus/integration/context.py`
- `hephaestus/identity.py`
- `hephaestus/store/profiles.py`
- `tests/test_workspace.py`
- `tests/test_watch.py`
- `tests/test_identity.py`
- `tests/test_profiles.py`
- `tests/test_okf_layout_paths.py`

## Verification

- Focused wave verification previously passed for the issue-specific path set: `43 passed`.
- Full suite after the complete wave: `173 passed` via `.\venv\Scripts\python.exe -m pytest --basetemp tmp_pytest\full-after-issue11 -o cache_dir=tmp_pytest\cache-full-after-issue11`.

## Notes

- This issue was landed as an independent locality refactor and merged back into the main working tree before the later integration issues were completed.
