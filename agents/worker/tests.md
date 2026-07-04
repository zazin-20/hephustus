---
title: Worker Test Conventions
role: worker
updated: 2026-07-03
owner: architect
---

# Worker — Test Conventions

Conventions for tests a Worker writes. QA owns higher-level suites under
`../qa/tests/`; this file covers unit/focused tests that ship with implementation.

## Conventions

- One focused test file per unit of behavior; name it for the behavior, not the
  internal.
- Assert on public behavior and observable output, not private attributes.
- Filesystem fixtures use `tmp_path`; DB fixtures use
  `tmp_path / ".hephaestus" / "state.db"`.
- Keep the full suite green: `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest`
  (the shared venv — never bare `py`/`python`, see [tdd.md](tdd.md)).
- Frontend: run `npm --prefix frontend run build` when frontend files change.

## Do not

- Do not delete or weaken existing tests to make a change pass.
- Do not stage `.hephaestus/`, `.pytest_tmp/`, `tmp_pytest/`, or `*.pyc`.
