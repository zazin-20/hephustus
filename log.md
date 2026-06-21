---
title: Hephaestus System Log
updated: 2026-06-21
---

# Hephaestus System Log

Records system-level changes to the Hephaestus design and OKF structure.

---

## 2026-06-21 — Initial System Design

**Type:** Architecture
**Author:** Human + Claude (design session)

Created the initial Hephaestus system design through a structured design
discussion. Key decisions made:

- Hephaestus is an OKF manager + compliance layer, NOT an orchestrator
- Routing is role-based (static mapping), not task-based or dynamic
- Claude Agent SDK (Python) for all Claude Code roles
- Codex via subprocess/MCP server for Worker role only
- No database — filesystem is the source of truth
- 6 structural rules form the MVP compliance loop
- Correction Box is the feedback mechanism for evolving directives

**Files created:**
- `agents/index.md` — OKF entry point
- `spec/architecture.md` — full system design
- `spec/rules/structural.md` — 6 built-in structural rules

**Open questions logged in architecture.md:** OQ-1 through OQ-4

**Next step:** Build Phase 1 (MVP surfaces + rule engine)

---

## 2026-06-21 — Tech Stack Analysis & Decisions (v0.2.0)

**Type:** Architecture
**Author:** Human + Claude (tech-stack review)

Reviewed the proposed stack against the four MVP surfaces and filled the gaps.
Key decisions:

- **Desktop, not web.** Ships as a cross-platform desktop app (Windows + macOS)
  via **PyWebView** (native OS webview, no bundled Chromium) with the Python core
  in-process and a **React + Tailwind** UI. Tauri kept as a documented, reversible
  migration path if distribution becomes the priority.
- **Write posture = read-reconcile + validate** (resolves OQ-3). Agents keep
  writing to `agents/` directly; Hephaestus validates on change and flags, but does
  not gate writes. Two-tier validation: Pydantic schema (per file) + compliance
  rules (cross-file).
- **Filesystem stays the source of truth**, fronted by an **in-memory OKF index**
  (derived cache, watchdog-updated). Rules read the index, not disk — so the backing
  store can scale later without changing the rule interface.
- **Concurrency model fixed:** a single asyncio core loop unifying the async Agent
  SDK, threaded watchdog (marshaled in via `call_soon_threadsafe`), and the Codex
  asyncio subprocess.
- **Stack gaps filled:** Pydantic (data model + validation), python-frontmatter,
  tomllib (read) + tomlkit (write), Shiki/Prism (Code Viewer), PyInstaller
  (packaging), pytest + fixture OKF trees (rule tests).

**Files changed:**
- `spec/architecture.md` — §2, §5.4 (new), §6 (rewritten), §8 (rewritten), §9 → v0.2.0

**New open questions:** OQ-5 (per-OS webview QA), OQ-6 (signing/auto-update vs Tauri)

**Next step:** Build Phase 1 (MVP surfaces + rule engine)

---

## 2026-06-21 — Phase 1 Core Scaffolded (rule engine + models)

**Type:** Implementation
**Author:** Human + Claude

Built the bottom-up core: frontmatter parser → Pydantic OKF models → OKF index
(`OKFContext`) → structural rule engine (S-001..S-006). All read from the derived
index, never the disk, per §6.1.

- **Stack:** Python 3.12, `pydantic` 2.11, `pyyaml`; `pytest` for tests.
- **Tests:** 14 passing (`py -m pytest`) — frontmatter, model validation, and
  rules against `clean_tree` / `violations_tree` fixtures built in `tmp_path`.
  Each of S-001..S-006 has a fixture that triggers it; Tier-1 schema errors
  surface as `schema` violations.
- **Files:** `pyproject.toml`, `hephaestus/` package, `tests/`, `README.md`,
  `.gitignore`.

**Spec refinement (needs reconciliation):** QA evidence and the completion log are
now **per-issue frontmatter documents** (`agents/qa/evidence/<id>.md`,
`agents/log/<id>.md`) rather than the single prose files the spec described, so the
rules are machine-checkable. Prose `index.md` / `log.md` remain human rollups.
Documented in README; `architecture.md` §3.1 and `structural.md` to be updated if
approved.

**Environment note:** this machine's default `%TEMP%` rejects pytest's basetemp;
`pyproject.toml` pins `--basetemp=.pytest_tmp` as a workaround.

**Next step:** watchdog-driven validation pipeline (§5.4, §6.3), then the
PyWebView + React shell.

---

## 2026-06-21 — Spec Reconciled to Per-Issue OKF Layout

**Type:** Architecture
**Author:** Human + Claude

Reconciled the design docs to the per-issue document layout the Phase 1 rule
engine actually consumes, so the docs and code agree.

**Why:** structural rules must be checkable from frontmatter alone (no LLM). QA
evidence and the completion log were specified as single prose files
(`agents/qa/readme.md`, `agents/log.md`), which would force fragile regex-scraping
of human markdown and leave no Tier-1 schema to validate. Per-issue frontmatter
docs give each record a typed, schema-validatable contract.

**Changes:**
- `architecture.md` §3.1 — doc-types table now lists **QA Evidence**
  (`agents/qa/evidence/{issue_id}.md`) and **Completion Record**
  (`agents/log/{issue_id}.md`); added a machine-checked-vs-human-rollup note.
  Drift wording (§2, §3.1) and the S-006 summary updated. → v0.2.1
- `structural.md` — OKFContext source comments, plus S-003 / S-004 / S-006 messages,
  artifacts, and fix hints repointed to the per-issue paths. → v0.2.0
- `index.md` — traceability table: QA evidence → `agents/qa/evidence/`,
  completion log → `agents/log/` (with `agents/log.md` as human rollup). → v0.2.0
- `README.md` — refinement note marked reconciled.

**Outcome:** prose `index.md` / `agents/log.md` remain human rollups; all
rule-checked artifacts are structured per-issue frontmatter documents.

**Next step:** watchdog-driven validation pipeline (§5.4, §6.3).

---

## 2026-06-21 — Watchdog Validation Pipeline (§5.4 / §6.3)

**Type:** Implementation
**Author:** Human + Claude

Built the live compliance pipeline on top of the rule engine, in two decoupled
layers so the core is testable without watchdog or asyncio.

- **`monitor.py` — `ComplianceMonitor`**: stateful rescan + diff. `refresh()`
  rebuilds the index, runs `run_all` (Tier-1 schema + Tier-2 rules), and returns a
  `ViolationDelta(added, resolved, current)`. Watcher-agnostic — drives both the
  passive monitor loop and any manual "re-check".
- **`watch.py`**: the §5.4 concurrency model —
  `OKFEventHandler` (filters to `*.md`) → `AsyncDebouncer` (coalesces bursts,
  marshals onto the asyncio loop via `call_soon_threadsafe`) →
  `OKFWatcher` (watchdog Observer) → `on_change(delta)`. Includes a CLI:
  `py -m hephaestus.watch <root>`.
- **`watchdog`** is an optional extra; the module imports fine without it and only
  `OKFWatcher.start()` requires it.

**Decision — full rescan, not incremental:** each debounced batch rebuilds the
whole index rather than mutating it in place. At MVP scale this is negligible;
incremental updates (§6.1) remain a deferred optimization that won't change the
`ComplianceMonitor` interface.

**Tests:** 23 passing (was 14). Added monitor diff tests (detect → resolve →
re-add) and watch tests (debounce coalescing, `*.md` filtering, and a real
filesystem end-to-end via watchdog).

**Next step:** the PyWebView + React desktop shell — surfacing the dashboard +
compliance monitor over this pipeline.

---

## 2026-06-21 — Desktop Shell (PyWebView + React + Tailwind)

**Type:** Implementation
**Author:** Human + Claude

Built the MVP desktop shell over the validation pipeline.

- **`dashboard.py` — `snapshot()`**: pure derivation of the §3.2 pipeline state per
  issue (OPEN/IN_PROGRESS/HANDOFF_PENDING/QA_PENDING/DONE) plus stage flags
  (spec/handoff/review/qa/log) and per-issue violation attribution. Returns one
  JSON-serializable payload — the single thing the bridge serves and pushes.
- **`desktop.py`**: PyWebView window (1280×820) loading the built frontend over
  `file://`. `Bridge` exposes `get_state()` / `rescan()` as `js_api`; the asyncio
  core loop + `OKFWatcher` run on a daemon thread and push fresh snapshots to the
  UI via `window.evaluate_js(window.__hephaestus_push__(...))` — the §5.4 model.
- **`frontend/`**: Vite 6 + React 18 + Tailwind v4. Two surfaces — Pipeline
  Dashboard and Compliance Monitor — plus summary stat cards, a Live/Preview
  indicator, and a Rescan button. Dark, product-grade styling. Browser preview
  falls back to mock data when no bridge is present.
- **`sample/agents/`**: example OKF tree (3 issues; one S-002 error on issue-003)
  so `py -m hephaestus.desktop sample` shows a populated, interesting view and live
  updates can be demoed by editing files.

**Verified:** 27 tests pass (added dashboard tests); `npm run build` succeeds
(dist 0.41 kB html + 20 kB css + 153 kB js); `hephaestus.desktop` imports with
pywebview present and frontend built; sample snapshot = 3 issues / 1 violation as
designed. The GUI window itself must be launched on the user's desktop session
(can't be opened headlessly from the agent).

**Tech stack note:** React pinned to 18.3 (not 19) for plugin stability; Tailwind
v4 via `@tailwindcss/vite` (no separate config file).

**Next step:** Claude Agent SDK + Codex integration (§5.1, §5.2), or the OKF Editor
surface (write-path with Tier-1 validation on save).

---

## 2026-06-21 — Agent Integration Layer (§5)

**Type:** Implementation
**Author:** Human + Claude

Built the `hephaestus/integration/` package: role-based static routing to Claude
and Codex backends, with pure/testable parts split from thin I/O adapters.

- **`routing.py`**: `Role` / `Tool` enums + static `ROLE_TOOL` map (§5.3,
  Worker → Codex, all others → Claude) + `ROLE_DIRECTIVE` locations.
- **`context.py`**: `build_session_context()` — pure assembly of the OKF docs to
  inject (role directive + issue spec for worker/qa/architect + worker `tdd.md`),
  concatenated into a system prompt; reports missing files rather than failing.
- **`runners.py`**: `ClaudeRunner` (claude-agent-sdk), `CodexRunner`
  (`codex exec`, streaming JSONL), `EchoRunner` (offline). `build_codex_argv` is
  pure and unit-tested; `_codex_command()` resolves the Windows shim (`cmd /c codex`).
- **`service.py`**: `AgentService` routes + `SessionRegistry` tags sessions by
  `role:issue` and **auto-resumes** (captures `session_id` from Claude result
  events, replays on the next call). CLI: `py -m hephaestus.integration`.

**Decisions / spec refinements (verified against installed tools):**
- **Codex backend = `codex exec`**, not the MCP/JSON-RPC stdio server the spec
  described. `codex exec` (codex-cli 0.130.0) is the supported non-interactive
  subprocess interface; context is piped via stdin as a `<stdin>` block.
- **Claude system-prompt field changed**: the SDK no longer has
  `append_system_prompt`; OKF context is now injected via `system_prompt` using the
  `{type: preset, preset: claude_code, append: ...}` form. A regression test
  asserts the context actually reaches `ClaudeAgentOptions` (the old field would
  have silently dropped it).

**Tests:** 35 passing (was 27). Routing, context assembly (incl. missing-file
reporting), `build_codex_argv`, echo-routed end-to-end, registry keys, the
context-injection regression test, and session resume.

**Not yet done (needs the user / live calls):** no live Claude/Codex call has been
run — those are outward-facing and cost tokens. CLI `--echo` dry-run verified for
both paths. Desktop UI does not yet expose a "run agent" panel.

**Next step:** OKF Editor surface (write-path + Tier-1 validation on save), or wire
a "run agent" panel into the desktop UI over this service.

---

## 2026-06-21 — Live Verification: Claude + Codex

**Type:** Verification
**Author:** Human + Claude

Ran both backends live (user-authorized; tiny prompts).

- **Claude (architect path):** returned the exact token `HEPHAESTUS_CLAUDE_OK`
  through `ClaudeRunner` end-to-end. ✅
- **Codex (worker path):** returned `HEPHAESTUS_CODEX_OK` (~31 output tokens). ✅

**Diagnosis — codex "hang":** a raw `codex exec <prompt>` invocation blocks because,
when stdin is a pipe, codex reads it as an appended `<stdin>` block and waits for
EOF ("Reading additional input from stdin…"). `CodexRunner` already closes stdin
(`proc.stdin.close()`), so runs *through the integration* complete; only the raw
diagnostic command hung. This confirms the runner's stdin handling is required and
correct.

**Parser fix:** captured the real codex-cli 0.130.0 JSONL schema —
`{"type":"item.completed","item":{"type":"agent_message","text":...}}`. The agent
text lives at `item.text`, which the generic parser missed. `_codex_event` now
extracts it (agent_message → `text`, turn.completed → `result`), locked in by a
unit test against the observed schema.

**Tests:** 36 passing (added the codex schema test).

**Next step:** unchanged — OKF Editor write-path, or a desktop "run agent" panel.

---

## 2026-06-21 — Code Viewer (§3.4)

**Type:** Implementation
**Author:** Human + Claude

Added the read-only multi-repo Code Viewer — the last Phase 1 MVP surface that
reads from disk.

- **`codeview.py` — `CodeViewer`**: `list_repos()` / `tree()` (lazy, one level) /
  `read_file()`. Reads are **constrained to configured roots** (path-traversal
  rejected), ignore noise dirs (`.git`, `node_modules`, …), cap at 1 MB, and skip
  binaries (null-byte sniff). Returns JSON-serializable data + a language hint.
- **Bridge**: exposed `list_repos` / `tree` / `read_file` on `window.pywebview.api`;
  desktop defaults the viewer roots to `[project, OKF root]`.
- **Frontend**: new **Code** tab (header nav) with a repo selector, lazy-expanding
  directory tree, and a file viewer using **highlight.js** (lazily registered
  languages; github-dark theme). Browser preview uses mock data.

**Decision (resolves OQ-4):** explicit path config for the MVP, not git
auto-discovery — simpler and deterministic. Security: reads are root-jailed.

**Note:** chose `highlight.js` as the lightweight highlighter (§8 listed
Shiki/Prism; all qualify as "lightweight, not Monaco") — simplest React
integration, works offline. Bundle grew to ~221 kB (71 kB gzip).

**Verified:** 40 tests pass (+4 codeview, incl. traversal-blocked + binary
detection); frontend builds clean; bridge serves the tree and detects languages.

**Phase 1 MVP status:** read surfaces complete (Dashboard, Compliance Monitor,
Code Viewer) + Claude/Codex integration. Remaining MVP gaps: **OKF Editor**
(write-path) and **Correction Box** (capture).

**Next step:** OKF Editor write-path (Tier-1 validation on save), or a desktop
"run agent" panel over the integration service.

---

## 2026-06-21 — Run Agent Panel (desktop UI over §5)

**Type:** Implementation
**Author:** Human + Claude

Wired the agent integration into the desktop UI so role-routed Claude/Codex
sessions can be launched from the workbench (the dogfooding lever for building
hephaestus-workbench *with* Hephaestus).

- **Bridge / streaming**: `Bridge.run_agent()` -> `DesktopApp.start_agent()` builds
  an `AgentTask`, resolves tool+context synchronously (returns run metadata), and
  schedules `_stream_agent` on the core loop via `run_coroutine_threadsafe`. Each
  `AgentEvent` is pushed to the UI through `window.__hephaestus_agent__(...)` —
  the same push pattern as compliance deltas (js_api can't stream). Sessions
  auto-resume via the existing registry.
- **Frontend**: new **Agent** tab — role selector (auto-routes), optional
  issue + working dir, prompt; live event log color-coded by kind; shows the
  resolved tool + injected context. Browser preview degrades gracefully.

**De-risking (no tokens spent):** verified `asyncio.create_subprocess_exec` works
on a background-thread Proactor loop (mirrors how `CodexRunner` runs under the
desktop), so the Worker/Codex path is sound off the main thread. Claude + Codex
were already verified live earlier.

**Tests:** 41 passing (+1). New test drives `start_agent` on a real background loop
with echo runners and asserts events (incl. terminal `done`) reach a fake window.

**Phase 1 MVP status:** all read surfaces + agent execution done. Remaining MVP
gaps: **OKF Editor** (write-path) and **Correction Box** (capture).

**Next step:** OKF Editor write-path, then Correction Box — completing Phase 1.
