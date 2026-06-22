# Hephaestus - Codex Worker Brief

Fill in `ISSUE_NUMBER`, `ISSUE_TITLE`, `BRANCH_NAME`, and `WHAT_TO_BUILD`
before handing this to a worker.

## Identity

- Repo: `C:\Users\kambala.jathin\Projects\hephustus`
- GitHub: `zazin-20/hephustus`
- Python cmd: `py`
- Test cmd: `py -m pytest`
- Basetemp fallback: `py -m pytest --basetemp=.pytest_tmp`
- Codex CLI: `C:\Users\kambala.jathin\AppData\Roaming\npm\codex.cmd`
- GitHub CLI: `C:\Program Files\GitHub CLI\gh.exe`

## Before You Start

Fetch the full issue body before writing code:

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" issue view ISSUE_NUMBER --repo zazin-20/hephustus
```

Treat the GitHub acceptance criteria as the definition of done.

## Architecture Rules

- The operational store at `.hephaestus/state.db` is written only through typed
  DAL modules in `hephaestus/store/`.
- The OKF tree under `agents/` is the open store; agents write markdown there.
- `hephaestus.store.db.connect(path)` is the only supported DB entry point.
- Use `dumps_json` and `loads_json` from `hephaestus.store.db` for JSON columns.
- Do not delete or weaken existing tests.

## TDD Rules

1. Write or extend the focused test file first.
2. Run the focused test target and confirm it fails before implementation.
3. Implement the smallest change that turns the test green.
4. Run the relevant focused suite again.
5. Finish with `py -m pytest`.
6. Test through public behavior, not private internals.
7. Use `tmp_path` for filesystem fixtures.
8. Use `tmp_path / ".hephaestus" / "state.db"` for DB fixtures.

## Git Workflow

```powershell
git checkout -b BRANCH_NAME
# implement
git add <specific files only>
git commit -m "feat: ISSUE_TITLE (issue #ISSUE_NUMBER)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012sdAQ15eRfQ8mQwZ3s46yJ"
```

Branch naming convention:

- `feat/00N-short-slug`

Example:

- `feat/003-threads-runs`

## GitHub Closeout

Run this only after tests are green and the frontend build succeeds when the UI
changed:

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" issue close ISSUE_NUMBER `
  --repo zazin-20/hephustus `
  --comment "Implemented: <one-line summary>. <N> tests passing. Merged BRANCH_NAME to main."
```

## Frontend Rules

- Preserve the existing dark Tailwind v4 UI language in `frontend/src/`.
- Do not remove existing tabs unless the issue explicitly requires it.
- In browser-preview mode without `window.pywebview`, fall back to mock data.
- Run `npm --prefix frontend run build` as the final step when frontend files changed.
- If gzip bundle size grows by more than 50 kB, explain why.

## Definition Of Done

- [ ] `py -m pytest` is green
- [ ] `npm --prefix frontend run build` is green when frontend changed
- [ ] All acceptance criteria from the GitHub issue are met
- [ ] Only intended files changed
- [ ] No `.hephaestus/`, `.pytest_tmp/`, `tmp_pytest/`, or `*.pyc` files are staged
- [ ] Commit includes the co-author trailer
- [ ] GitHub issue is closed with a summary comment

## What To Build

- Issue `#ISSUE_NUMBER`: `ISSUE_TITLE`
- Branch: `BRANCH_NAME`
- Scope: `WHAT_TO_BUILD`
