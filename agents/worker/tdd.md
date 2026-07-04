---
title: Worker TDD Playbook
role: worker
updated: 2026-07-03
owner: architect
---

# Worker — TDD Playbook

The test-first loop every Worker follows. This file is consumed by
`hephaestus/okf_layout.worker_tdd_path()` and is the reference for the
behavioral "TDD playbook followed" check — keep it authoritative.

## Loop

1. Write or extend the focused test file first.
2. Run the focused target and confirm it **fails** before implementing.
3. Implement the smallest change that turns the test green.
4. Run the focused suite again.
5. Finish with the full suite: `<venv-python> -m pytest`.

## Rules

6. Test through public behavior, not private internals.
7. Use `tmp_path` for filesystem fixtures.
8. Use `tmp_path / ".hephaestus" / "state.db"` for DB fixtures.
9. Do not delete or weaken existing tests.

## Commands

- Python: the shared venv at `agents/.venv` — **never** bare `py` or `python`
  (both can resolve to a Windows Store alias stub that hangs under a sandboxed
  shell). Always use the absolute interpreter path:
  `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe`
- Tests: `<venv-python> -m pytest` (fallback `<venv-python> -m pytest --basetemp=.pytest_tmp`)
- The venv holds only third-party dependencies (pydantic, pyyaml, pytest, …) —
  never `hephaestus` itself (no editable install). `pyproject.toml` sets
  `pythonpath = ["."]`, so running from a worktree's own root always imports
  *that worktree's* local `hephaestus/` package, even though the venv is shared
  across every worktree. This is what makes one venv safe to reuse in parallel
  isolated worktrees.
