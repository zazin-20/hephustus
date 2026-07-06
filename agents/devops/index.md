---
title: DevOps
role: devops
updated: 2026-07-05
owner: architect
---

# DevOps

Navigation page and directive for the DevOps role. (`index.md` is this role's
directive target — `ROLE_DIRECTIVE[devops]`.)

Owns **infrastructure and deployment** docs and process.

## Responsibilities

1. **Packaging** — the desktop app ships via PyWebView; document the build.
2. **Build gates** — Python suite (shared venv, see below) and frontend build
   (`npm --prefix frontend run build`) must be green before release.
3. **Environment** — document runtime prerequisites (the shared venv at
   `agents/.venv` — never bare `py`/`python`, which can resolve to a Windows
   Store alias stub that hangs under a sandboxed shell — Node/npm, Codex CLI,
   GitHub CLI) and any deployment steps.
4. **Log your work** — when you finish a unit of work, append a dated entry to
   your own role log at `log.md` (create it if absent): what changed, why, and
   any decisions or follow-ups. Every spawned agent logs its own slice
   post-work; keep it current so the system history is reconstructable from the
   logs, not just git.

## Python environment

All agents run Python via one shared venv at `agents/.venv`
(`C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe`),
holding only third-party dependencies — never an editable install of
`hephaestus` itself. Because `pyproject.toml` sets `pythonpath = ["."]`,
running `<venv-python> -m pytest` from any worktree's own root always imports
*that worktree's* local `hephaestus/` package, so the one shared venv is safe
to reuse across parallel isolated worktrees. Rebuild it with:

```
<system-python> -m venv agents/.venv
agents/.venv/Scripts/python.exe -m pip install -U pip
agents/.venv/Scripts/python.exe -m pip install "pydantic>=2" "pyyaml>=6" "pytest>=8" "watchdog>=4" "pywebview>=5" "tomlkit>=0.12" "claude-agent-sdk>=0.1"
```

## Contents

| Path | Holds |
|---|---|
| `index.md` | This directive |
| _infra/deployment docs_ | Added here as they are written |

## You do NOT

- Own product scope, specs, implementation, or QA.

See [../index.md](../index.md) for the full pipeline.
