# Hephaestus

OKF system manager and agent compliance layer. See [`architecture.md`](architecture.md)
for the full design and [`structural.md`](structural.md) for the rule library.

This README covers the **code** (Phase 1 core). The `*.md` design docs are the OKF spec.

## Phase 1 core (built)

Bottom-up, dependency-ordered:

```
hephaestus/
├── core.py          Severity, Violation, ViolationResult (dependency-free primitives)
├── frontmatter.py   YAML frontmatter <-> (dict, body)
├── models.py        Pydantic OKF doc types — the Tier-1 schema layer
├── index.py         build_context() -> OKFContext (derived read cache over agents/)
├── rules/
│   ├── base.py      HephaestusRule interface
│   ├── structural.py S-001 .. S-006
│   └── registry.py  run_rules() / run_all()
├── monitor.py       ComplianceMonitor: rescan + violation diff (added/resolved)
├── watch.py         watchdog + asyncio debounce pipeline; py -m hephaestus.watch
├── dashboard.py     snapshot(): pipeline rows + violations for the UI (§3.2)
├── codeview.py      read-only multi-repo file browse, root-constrained (§3.4)
├── desktop.py       PyWebView shell + js_api bridge; py -m hephaestus.desktop
└── integration/     agent layer (§5): routing, context, Claude/Codex runners
frontend/            Vite + React + Tailwind UI (Dashboard + Compliance Monitor)
sample/agents/       a small example OKF tree to run the app against
tests/
├── conftest.py      clean_tree / violations_tree fixtures (built in tmp_path)
└── test_*.py        frontmatter, models, rules
```

## Running

```sh
py -m pytest                       # 27 tests

# desktop app — build the frontend once, then launch the native window
npm --prefix frontend install
npm --prefix frontend run build
py -m hephaestus.desktop sample    # opens over the sample OKF tree

# headless live monitor (prints deltas; no UI)
py -m hephaestus.watch sample
```

`pydantic>=2` and `pyyaml` are the core runtime deps; the desktop app adds
`watchdog` + `pywebview`. Install all extras with `pip install -e .[app,dev]`.
The frontend (Vite + React + Tailwind) lives in `frontend/` and builds to
`frontend/dist/`, which the window loads over `file://`.

Edit a file under `sample/agents/` while the app is open — the dashboard and
compliance monitor update live. The **Code** tab browses the configured repos (by
default the workspace OKF root plus any top-level service repos with a `.git/`)
read-only, with syntax highlighting.
The **Agent** tab runs a role-routed Claude/Codex session (§5) — pick a role + issue,
set a working dir, and watch output stream in. Run `npm --prefix frontend run dev` to
preview the UI in a browser (it falls back to mock data when the Python bridge isn't
present).

### Agent integration (§5)

```sh
# dry-run: show routing + which OKF files get injected (no live call)
py -m hephaestus.integration architect "Review the handoff" --issue issue-003 --root sample --echo
py -m hephaestus.integration worker    "Implement the issue" --issue issue-003 --root sample --echo
```

Drop `--echo` for live calls. Routing is static and role-based (§5.3):
**Worker → Codex** (`codex exec`), everything else **→ Claude** (`claude-agent-sdk`).
Claude roles need `pip install -e .[agents]` and a logged-in `claude` CLI; the
Worker role needs the `codex` CLI (`codex login`). Sessions are tagged by
`role:issue` and resumed automatically across calls.

## OKF on-disk layout (convention)

Rules read structured **per-issue frontmatter documents**. The prose `index.md` /
log files are human rollups.

```
agents/
├── architect/
│   ├── issues/
│   │   ├── index.md          # frontmatter: title, updated, open_issues[]
│   │   └── <issue-id>.md     # IssueSpec: id, status, role, sprint, created
│   └── handoffs/
│       └── <issue-id>.md     # Handoff: issue_id, worker, status, created, reviewed_by
├── qa/
│   └── evidence/
│       └── <issue-id>.md     # QAEvidence: issue_id, result, created
└── log/
    └── <issue-id>.md         # LogEntry: issue_id, sprint, date, sprint_closed, ...
```

> **Note — spec refinement:** the original spec described QA evidence and the
> completion log as single prose files (`agents/qa/readme.md`, `agents/log.md`).
> Those are not reliably machine-checkable, so the rule engine consumes per-issue
> structured records instead, with the prose files kept as human rollups. This is
> now reflected in `architecture.md` §3.1, `structural.md`, and `index.md`.

## Status

| Layer | State |
|---|---|
| Frontmatter parser | ✅ |
| Pydantic OKF models (Tier-1 schema) | ✅ |
| OKF index / `OKFContext` | ✅ |
| Structural rules S-001..S-006 | ✅ |
| watchdog validation pipeline (§5.4, §6.3) | ✅ |
| Pipeline dashboard derivation (§3.2) | ✅ |
| Desktop shell (PyWebView + React + Tailwind) | ✅ (MVP) |
| Claude Agent SDK / Codex integration (§5) | ✅ (MVP) |
| Code Viewer — read-only, multi-repo (§3.4) | ✅ (MVP) |
| Run Agent panel — desktop UI over §5 | ✅ (MVP) |
