---
title: Hephaestus — System Architecture
version: 0.2.1
status: active
created: 2026-06-21
updated: 2026-06-21
owner: architect
layer: spec
---

# Hephaestus System Architecture

## 1. Problem Statement

A multi-repo, multi-tool AI development system (Claude Code + Codex) operates
from a shared OKF knowledge base in `agents/`. As agents make changes rapidly,
three failure modes emerge:

1. **Knowledge drift** — OKF files go out of sync with actual agent behavior
   (e.g. `issues/index.md` lists open items that the completion log says are closed)
2. **Directive violations** — agents skip required pipeline steps (e.g. Worker
   closes an issue without leaving an Architect handoff)
3. **No feedback loop** — when a human spots a directive gap mid-operation,
   there is no structured path to update the OKF system

Hephaestus solves all three.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     HEPHAESTUS                          │
│                  (Python Coordinator)                   │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  OKF Editor │  │  Compliance  │  │  Code Viewer  │  │
│  │             │  │  Monitor     │  │  (read-only)  │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│         │                │                              │
│         └────────────────┘                              │
│                  │                                      │
│         ┌────────▼────────┐                             │
│         │ Pipeline        │                             │
│         │ Dashboard       │                             │
│         └─────────────────┘                             │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Integration Layer                   │   │
│  │  Claude Agent SDK (Python)  │  Codex MCP/stdio   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
              │                        │
              ▼                        ▼
        Claude Code               Codex CLI
   (Orchestrator, Architect,    (Worker only,
    PM, QA, Designer, DevOps)    via codex-cc)
```

Hephaestus is **not** the orchestrator. It is the **ground truth manager**
that all agents consume from. The Orchestrator agent retains responsibility
for spawning and routing.

**Deployment form:** Hephaestus ships as a cross-platform **desktop application**
(Windows + macOS), not a web service. The Python core runs in-process behind a
native OS webview (see §8); there is no server to host and no auth layer in the
single-user MVP. The architecture is deliberately built so a hosted/multi-user
variant remains possible later (see §6.1 and OQ-3).

---

## 3. Core Surfaces

### 3.1 OKF Editor

Manages the `agents/` tree directly.

**Capabilities:**
- Browse the full `agents/` directory tree
- Create new OKF files with correct frontmatter for each role type
- Edit existing directive files (role instructions, playbooks, index files)
- Frontmatter-aware: validates required fields per document type
- Detects and flags stale documents (updated_at drift vs the completion log)

**OKF Document Types:**

| Type | Required Frontmatter | Location Pattern |
|---|---|---|
| Role Directive | title, role, version, status | `agents/{role}/claude.md` |
| Issue Spec | id, status, role, sprint, created | `agents/architect/issues/{id}.md` |
| Handoff | issue_id, worker, status, created, reviewed_by | `agents/architect/handoffs/{issue_id}.md` |
| QA Evidence | issue_id, result, created | `agents/qa/evidence/{issue_id}.md` |
| Completion Record | issue_id, sprint, date, sprint_closed | `agents/log/{issue_id}.md` |
| Index (human rollup) | title, updated | `agents/{dir}/index.md` |
| Prose log (human rollup) | title, updated | `agents/log.md` |

> **Machine-checked vs human rollup.** Every artifact the rule engine reads
> (issue specs, handoffs, QA evidence, completion records) is a **structured
> per-issue frontmatter document**, so it can be schema-validated (Tier 1) and
> checked deterministically without an LLM. `index.md` and the prose `agents/log.md`
> are **human rollups** — for people to read, not parsed by rules.

### 3.2 Pipeline Dashboard

Visual state of every work item derived from reading the filesystem — no
separate database. Single source of truth remains the `agents/` tree.

**Pipeline State Machine per Issue:**

```
OPEN → IN_PROGRESS → HANDOFF_PENDING → QA_PENDING → DONE
```

State is inferred from file presence and frontmatter:

| State | Condition |
|---|---|
| OPEN | Exists in `issues/` with `status: open` |
| IN_PROGRESS | `status: in-progress` in issue spec |
| HANDOFF_PENDING | Issue closed but no matching handoff file |
| QA_PENDING | Handoff exists, no QA evidence entry |
| DONE | QA evidence exists AND log entry present |

**Dashboard View:**
```
issue-001  Auth module refactor     [PM ✓][Arch ✓][Worker ✓][QA ⏳][Log ○]
issue-002  SQL agent migration      [PM ✓][Arch ✓][Worker ○][QA ○][Log ○]
issue-003  API rate limiting        [PM ✓][Arch ⚠][Worker ○][QA ○][Log ○]
                                           ↑ violation flagged
```

### 3.3 Compliance Monitor

The active rules engine. Runs checks against the `agents/` tree on demand
or on file change events. Flags violations and routes them to the Correction Box.

See `spec/rules/structural.md` for the full rule library.

**Two Compliance Loops:**

**Loop 1 — Passive Monitoring (continuous)**
```
Hephaestus watches agents/ tree for changes
    → runs structural rules against changed files
    → flags violations with severity + fix hint
    → surfaces in dashboard
```

**Loop 2 — Correction Box (human-driven)**
```
Human spots directive gap mid-operation
    → drops note in Correction Box
    → Hephaestus queues it for review
    → Human promotes to:
        (a) OKF directive update (edit role's claude.md)
        (b) New structural rule
        (c) New behavioral rule (future)
    → Updated directive / rule goes live
```

### 3.4 Code Viewer

Read-only browse of the multi-repo codebase. Purpose is cross-reference:
view code state alongside OKF state without switching windows.

**MVP capabilities:**
- Directory tree browse across configured repos
- File content view with syntax highlighting
- No edit capability in MVP

---

## 4. Compliance Rule Architecture

Rules are the core primitive of the compliance engine. All rules — built-in
or custom — implement the same interface.

```python
class HephaestusRule:
    id: str                              # e.g. "structural.worker-needs-spec"
    name: str                            # human-readable
    layer: Literal["structural",         # filesystem checkable
                   "behavioral"]         # LLM-judged (future)
    severity: Literal["error",           # blocks progression
                      "warning",         # flags for review
                      "info"]            # informational
    roles_involved: list[str]            # ["worker", "architect"]
    auto_fixable: bool                   # can Hephaestus propose a fix?
    fix_hint: str                        # what to tell the human

    def check(self, context: OKFContext) -> ViolationResult:
        ...
```

**Rule Layers:**

| Layer | Checks | Implementation | MVP? |
|---|---|---|---|
| Structural | File presence, frontmatter, cross-refs | Python + filesystem | ✅ |
| Behavioral | Content quality, playbook adherence | LLM prompt | Future |
| Custom | User-defined | Python fn / YAML | Future |

**Built-in Structural Rules (MVP):**

See `spec/rules/structural.md` for full definitions.

| Rule ID | Description |
|---|---|
| `S-001` | Worker must have Architect issue spec before starting |
| `S-002` | Worker must leave handoff artifact after completing |
| `S-003` | QA must produce evidence before issue logged as done |
| `S-004` | Log entry must exist for every completed issue spec |
| `S-005` | Handoff must have Architect review before QA starts |
| `S-006` | Sprint state must be consistent (issues/index vs completion log) |

---

## 5. Integration Layer

### 5.1 Claude Agent SDK

Used for all Claude Code sessions (Orchestrator, Architect, PM, QA, Designer, DevOps).

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt=directive_prompt,
    options=ClaudeAgentOptions(
        setting_sources=["project"],     # loads .claude/ config
        append_system_prompt=okf_context # injects role's claude.md
    )
):
    yield message
```

**Context strategy:** OKF directive files are injected at session start via
`append_system_prompt`. Because context compaction can silently drop context,
critical architectural invariants from `agents/architect/architect.md` are
re-injected at the start of every turn for long-running sessions.

**Session management:** Sessions are tagged by role and issue ID for
resumability. Hephaestus maintains a session registry:

```python
sessions = {
    "architect:issue-003": "session-uuid-...",
    "qa:issue-001": "session-uuid-...",
}
```

### 5.2 Codex Integration

Codex CLI exposes a JSON-RPC 2.0 app-server over stdio. Hephaestus talks
to it via subprocess for Worker sessions.

```python
# Spawn Codex as MCP server
process = subprocess.Popen(
    ["codex", "mcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
)

# Send task with issue spec context
message = {
    "jsonrpc": "2.0",
    "method": "codex",
    "params": {
        "prompt": worker_prompt,
        "context_files": ["agents/worker/claude.md",
                          f"agents/architect/issues/{issue_id}.md",
                          "agents/worker/tdd.md"]
    }
}
```

**Why subprocess for Codex (not SDK):**
Codex does not have a Python SDK equivalent to the Claude Agent SDK. The
MCP server / app-server model is the correct programmatic interface.

### 5.3 Tool Routing

Routing is role-based, not task-based. The mapping is static and defined here:

| Role | Tool | Reason |
|---|---|---|
| Orchestrator | Claude Code (Agent SDK) | Multi-step planning, subagent spawning |
| Product Manager | Claude Code (Agent SDK) | Document-heavy, iterative |
| Architect | Claude Code (Agent SDK) | Complex reasoning, cross-repo awareness |
| Worker | Codex (subprocess/MCP) | Implementation, TDD, one spec at a time |
| QA | Claude Code (Agent SDK) | Test writing, evidence collection |
| Designer | Claude Code (Agent SDK) | Token/spec generation |
| DevOps | Claude Code (Agent SDK) | Infrastructure planning |

---

### 5.4 Concurrency & Process Model

Hephaestus mixes three concurrency styles that do **not** compose for free: the
Agent SDK is **async**, `watchdog` delivers **threaded** callbacks, and the Codex
stdio client is a **subprocess**. They are unified under a single asyncio core loop.
This must be decided on day one — retrofitting concurrency is expensive.

```
Thread 1 (main)     pywebview GUI loop ─────────────────┐
                                                        │  JS ↔ Python bridge
Thread 2 (core)     asyncio event loop                  │  (js_api + evaluate_js)
                      ├─ OKF index                       │
                      ├─ rule engine                     │
                      ├─ Claude Agent SDK queries        │
                      └─ Codex subprocess (asyncio)      │
Thread 3 (watcher)  watchdog observer ─ normalized event ┘
                                          │
                            loop.call_soon_threadsafe → asyncio.Queue → debounce
```

- **JS → Python:** `js_api` methods (invoked on the pywebview thread) dispatch into
  the core loop via `run_coroutine_threadsafe` and return results to the UI.
- **Python → JS (push):** live dashboard and violation updates are pushed with
  `window.evaluate_js(...)` from the core loop.
- **Watchdog → core:** the observer thread normalizes each FS event (path + inferred
  doc type) and hands it to the core loop via `call_soon_threadsafe`; the loop
  **debounces** (~200ms) to coalesce editor saves and multi-file agent writes before
  processing.
- **Codex:** spawned with `asyncio.create_subprocess_exec`; JSON-RPC requests are
  correlated by id with timeouts and restart-on-crash. Check whether the `codex-cc`
  skill already wraps this before hand-rolling the stdio client.

---

## 6. Data Model

### 6.1 Source of Truth vs. Derived Index

The `agents/` OKF tree is the **single source of truth**. Hephaestus runs no
database. But re-parsing the whole tree on every dashboard render or rule run does
not scale, so Hephaestus maintains an **in-memory OKF index** — a *derived read
cache*, never authoritative.

- Built once on startup (full scan), then **mutated incrementally** from watchdog
  events (see §5.4).
- Keyed for the queries rules and the dashboard need: issues by id / status /
  sprint, handoffs by issue_id, log entries by issue_id / sprint, QA evidence by
  issue_id.
- **The rule engine reads the index, not the disk.** `OKFContext` is a view over the
  index. This is the key scale property: the backing store can later become a SQLite
  cache (or a server-side store for a hosted variant) **without changing the rule
  interface**.

### 6.2 Write Posture — Read-Reconcile + Validate

Hephaestus is **not** the sole writer to `agents/`. Agents (Claude Code, Codex)
write to the tree directly; Hephaestus observes those writes and **validates that
they are correct**. It does not gate or lock writes in the MVP. This resolves OQ-3
in favour of the lower-risk posture.

The only files Hephaestus itself writes are:
- the **Correction Box** (`agents/hephaestus/corrections.md`), and
- OKF edits a **human** makes through the OKF Editor surface.

Because Hephaestus does not block writes, its guarantee is **detect-and-flag**, not
prevent — violations surface immediately in the dashboard with severity.

### 6.3 Validation Pipeline (two tiers)

Every watchdog event drives validation on the changed file(s):

| Tier | Scope | Runs | Question answered |
|---|---|---|---|
| **Tier 1 — Schema** | single file | every write | Does it parse? Does its frontmatter have the required fields and valid enum values for its doc type? (Pydantic) |
| **Tier 2 — Compliance** | cross-file | scoped to rules touching the changed file | Do the S-001…S-006 relationships still hold? |

Tier 1 is the core "are agents writing correctly" guard. The same validation logic
is designed to be reusable by a future **pre-write validation API** that an agent
could call before committing a change (Phase 2+) — so validation works both
reactively (watchdog) and proactively (agent-initiated), which matters for scale.

### 6.4 Correction Box

**Correction Box** is the only runtime state that lives outside `agents/`:

```python
# In-memory queue, flushed to agents/hephaestus/corrections.md on save
corrections: list[Correction] = []

class Correction:
    id: str
    timestamp: str
    description: str                         # human's note
    observed_in: str                         # file or pipeline stage
    status: Literal["pending",
                    "promoted_to_directive",
                    "promoted_to_rule",
                    "dismissed"]
    promoted_to: str | None                  # rule ID or file path
```

---

## 7. Build Phases

### Phase 1 — MVP (current scope)
- OKF Editor (read/write `agents/` tree, frontmatter-aware)
- Pipeline Dashboard (filesystem-derived state, no database)
- 6 structural rules (S-001 through S-006)
- Violation display with fix hints
- Correction Box (capture + queue)
- Code Viewer (read-only, multi-repo)
- Claude Agent SDK integration
- Codex MCP/subprocess integration

### Phase 2
- Correction Box → promote to directive (OKF update)
- Correction Box → promote to rule (structural rule builder)
- Session manager UI (active sessions, logs, cost tracking)
- File-change-triggered rule runs (watch mode)

### Phase 3
- Custom rule layer (Python function or YAML)
- Rule test harness (validate rules against fixture OKF trees)

### Phase 4
- Behavioral rules (LLM-judged content compliance)
- Directive diff viewer (what changed between versions)
- OKF template library per role

---

## 8. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language / Backend | Python 3.11+ | Claude Agent SDK is Python-native; rule engine + frontmatter parsing live here |
| Desktop shell | **PyWebView** (native OS webview) | Cross-platform (WebView2 on Windows, WKWebView on macOS); lightweight — no bundled Chromium; runs the Python core in-process |
| UI | React + Tailwind | Built to static assets, loaded into the webview; product-grade polish, reused across all four surfaces |
| Agent SDK | `claude-agent-sdk` | Official Claude Code programmatic interface (async) |
| Codex interface | `asyncio` subprocess + JSON-RPC 2.0 | Codex app-server over stdio; check `codex-cc` wrapper before hand-rolling the client |
| Data modeling / validation | **Pydantic v2** | Backbone of all OKF doc types (IssueSpec, Handoff, …) and per-doc-type frontmatter validation (Tier 1) |
| Frontmatter parsing | `python-frontmatter` | Splits YAML frontmatter from markdown body; parsed dict validated by Pydantic |
| OKF index | In-memory (derived cache) | Built on startup, updated incrementally from watchdog events; rules read the index, not disk (§6.1) |
| File watching | `watchdog` | Detects agent writes to the `agents/` tree; feeds the validation pipeline |
| Concurrency | `asyncio` core loop | Unifies async SDK, threaded watchdog (marshaled in), Codex subprocess (§5.4) |
| Config (read) | `tomllib` (stdlib) | Zero-dependency reads of `hephaestus.toml` |
| Config (write) | `tomlkit` | Round-trips UI-driven rule toggles while preserving human comments/formatting |
| Code Viewer highlighting | Shiki or Prism (React) | Lightweight read-only syntax highlighting; avoid Monaco (heavy) |
| Packaging | PyInstaller | Single-file desktop bundles for Windows + macOS |
| Testing | `pytest` + fixture OKF trees | Filesystem-as-truth makes rules trivially testable against `tmp_path` |

**Desktop shell decision.** The app must run on **Windows and macOS**, look like a
real product, and stay lightweight, with a Python core (the Agent SDK forces
Python). **PyWebView** wins this balance: it drives the **native OS webview**
(WebView2 / WKWebView) so there is **no bundled Chromium**, the Python core runs
**in-process** (no sidecar, no IPC), and the **React + Tailwind** UI carries product
polish across both platforms. Trade-off: weaker out-of-the-box
installer/auto-update/code-signing tooling than Tauri, and minor per-OS webview
rendering differences (OQ-5, OQ-6). **Migration path:** if distribution becomes the
priority, the shell can move to **Tauri** while keeping the same React UI and Python
core — so this is a reversible decision.

---

## 9. Open Questions

| # | Question | Impact |
|---|---|---|
| OQ-1 | Should Correction Box items be persisted to `agents/hephaestus/` immediately or only on user action? | Data loss risk |
| OQ-2 | Context compaction re-injection strategy: per-turn or threshold-triggered? | Agent behavior stability |
| OQ-3 | ~~Sole writer vs read-reconcile only?~~ **RESOLVED:** read-reconcile + validate (§6.2). | Conflict risk with agents writing directly |
| OQ-4 | ~~Path config vs git auto-discovery for the Code Viewer?~~ **RESOLVED:** explicit path config for MVP (§3.4); reads constrained to configured roots. | Setup friction |
| OQ-5 | Native webview rendering differs across WebView2 (Win) and WKWebView (macOS) — how much per-OS UI QA is needed? | Product polish on both platforms |
| OQ-6 | Code-signing / notarization (macOS) + auto-update: solve under PyWebView + PyInstaller, or defer to a Tauri shell migration? | Distribution as a real product |
