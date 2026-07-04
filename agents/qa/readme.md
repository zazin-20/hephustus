---
title: QA — Process
role: qa
updated: 2026-07-03
owner: architect
---

# QA — Process

How verification runs in this workspace.

## Flow

1. Handoff reviewed by Architect (`reviewed_by: architect`).
2. QA verifies against the issue spec's acceptance criteria.
3. QA writes `evidence/{issue_id}.md` (`result: pass|fail`).
4. On pass, the issue can be logged at `../log/{issue_id}.md`.

## Test homes

| Kind | Location |
|---|---|
| Security | `tests/security/` |
| Integration | `tests/integration/` |
| End-to-end | `tests/e2e/` |
| Browser | `playwright/` |
| Manual snapshots | `manual_test_snapshots/` |
| Bugs | `bug-report/` |

Python suite runs with the shared venv — never bare `py`/`python` (can hang on a
Windows Store alias stub under a sandboxed shell):
`C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest`
(fallback: add `--basetemp=.pytest_tmp`).
