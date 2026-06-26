---
issue_id: issue-012
worker: codex
status: done
created: 2026-06-23
reviewed_by: []
---

## Summary

Moved run construction out of the desktop shell and into `AgentService`, so role-based and profile-based runs are assembled through one backend-owned entry point.

## Changes

- Added service-owned helpers for building tasks and prepared runs:
  - `task_for_role`
  - `task_for_profile`
  - `begin_role_run`
  - `begin_profile_run`
- Updated the desktop shell to forward run construction to `AgentService` instead of assembling `AgentTask` directly.
- Added coverage for the service entry points and the desktop forwarding path.

## Files Changed

- `hephaestus/integration/service.py`
- `hephaestus/desktop.py`
- `tests/test_integration.py`
- `tests/test_desktop_agent.py`

## Verification

- Covered by the full suite after the issue wave: `173 passed` via `.\venv\Scripts\python.exe -m pytest --basetemp tmp_pytest\full-after-issue11 -o cache_dir=tmp_pytest\cache-full-after-issue11`.

## Notes

- This issue was the critical-path refactor that unblocked issue `#13`.
