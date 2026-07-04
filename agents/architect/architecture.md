# Hephaestus — Architecture Foundation

**Version:** 1.0
**Date:** 2026-06-21
**Status:** Decided — the architecture of record.

This document captures the foundational architecture for Hephaestus, derived
from a design dialogue. It is deliberately **scale-first**: every decision was made
against expected post-MVP requirements (multi-service workspaces, context curation,
provider governance, full audit/replay, the future code-graph overlay).

---

## 0. Identity of the system

> **Hephaestus is a control plane over interchangeable AI providers.**
> Providers (Claude, Codex, future engines) are commoditized execution engines that can
> write code and call tools. Hephaestus governs *every dimension* of how they run —
> **what** they consume (curated context), **where** they work (scope), **which** model,
> **how hard** they think (effort), **what** tools they may call — and then **verifies**
> they complied.
>
> **Context manager on the way in. Compliance checker on the way out.**

---

## 1. Decision log

| # | Fork | Decision |
|---|---|---|
| D1 | Where does runtime state live? | **SQLite operational store**, separate from the OKF tree. `agents/` stays *pure agent-authored knowledge*. |
| D2 | Store scope | **Per-workspace**, co-located at `<workspace>/.hephaestus/state.db`. One running Hephaestus = one open workspace (VSCode multi-root model). |
| D3 | Multi-service / multi-repo | A **workspace** = one OKF tree + N service repos. **Service is not a schema axis** — derived at query time from trace target paths. |
| D4 | Conversation unit | A **thread** = a curatable, persistent, transferable **context container** owned by a role-actor (`role : named-thread`; an issue is one common thread name). |
| D5 | Context ownership | **Client-owned context.** Hephaestus compiles each run's input from a curated view of the transcript. Provider session-resume demoted to a within-run optimization. |
| D6 | Provider abstraction | First-class **Execution Contract** + strict **Provider Adapters**. **Hard governance** at the boundary where the provider supports it; **compliance layer as backstop** where it doesn't. |
| D7 | Rule model | **One rule interface** over a unified **`EvaluationContext`** (OKF + trace + contract + actor + scope). All four layers (structural/exit/governance/behavioral) share it. |
| D8 | Run model & concurrency | A **run** is a first-class persisted entity (the central audit join). Concurrency: **parallel across actors, serial per actor**. |

---

## 2. The two stores (the load-bearing split)

| | **OKF tree** (`agents/`, markdown) | **Operational store** (`.hephaestus/state.db`) |
|---|---|---|
| Written by | **Agents**, freely | **Only Hephaestus**, via typed DAL |
| Trust | Untrusted — validated after the fact | Trusted by construction |
| Format guarantee | frontmatter → Pydantic → rules | typed single-writer; no LLM ever writes here |
| Contents | issues, handoffs, QA evidence, completion logs, directives, **identity cards** | profiles, threads, turns, runs, trace, violations, corrections |
| Lifecycle | versioned, reviewed, durable knowledge | operational telemetry; queryable; rotatable |

**Why agents can't write the wrong format into SQLite:** they never write to it at all.
The store is a *closed* store with a single typed writer (Hephaestus). The OKF tree is the
*open* store — and the compliance engine exists precisely because it is agent-writable.

**Provenance cross-check (a consequence, and a feature):**
- `authored_by: arch-001` in OKF frontmatter = what the agent *claims* it did (untrusted).
- A trace event in the store = what Hephaestus *observed* it do (trusted).
- A governance rule can verify the two agree. Impossible if both are flat files the agent can write.

The DB lives in `.hephaestus/`, outside any agent's working dir, so agent filesystem access
does not reach it.

---

## 3. Entity model

```
Workspace
  └── Actor              (a persistent role-agent: identity + governing config)
        └── Thread       (a curatable context container; optionally bound to an issue)
              └── Run    (one governed execution against the thread)
                    ├── Contract     (the governance applied)
                    ├── Turns        (transcript it produced)
                    ├── Trace events (file/tool actions it took)
                    └── Outcome      (compliance result + usage/cost)
```

- **Actor identity** (who) is *knowledge* → a lightweight card at `agents/identities/{agent_id}.json`,
  the provenance anchor referenced by `authored_by`.
- **Actor configuration** (how it runs: rules, model, effort, scope) is *operational* → `profiles` table.
- `agent_id` links the two.

---

## 4. Operational store schema (SQLite, WAL mode)

```sql
-- single-writer; WAL for parallel-actor reads/writes

profiles (
  agent_id     TEXT PRIMARY KEY,   -- role-prefixed, e.g. arch-001
  name         TEXT NOT NULL,
  role         TEXT NOT NULL,
  rules        JSON NOT NULL,      -- declared exit/governance rule names
  model        TEXT,              -- default model for this actor
  effort       TEXT,              -- default reasoning/effort level
  working_dir  TEXT,              -- NULL = whole workspace
  created_at   TEXT NOT NULL
)

threads (
  id           TEXT PRIMARY KEY,
  agent_id     TEXT NOT NULL REFERENCES profiles,
  name         TEXT NOT NULL,
  issue_id     TEXT,              -- optional binding once an issue exists
  created_at   TEXT NOT NULL,
  updated_at   TEXT NOT NULL
)

turns (                          -- the transcript (immutable audit)
  id           TEXT PRIMARY KEY,
  thread_id    TEXT NOT NULL REFERENCES threads,
  run_id       TEXT REFERENCES runs,
  seq          INTEGER NOT NULL,
  role         TEXT NOT NULL,     -- user | assistant | tool
  kind         TEXT,              -- text | tool | system | result
  text         TEXT NOT NULL,
  included     INTEGER NOT NULL DEFAULT 1,  -- the pruning toggle (soft, reversible)
  created_at   TEXT NOT NULL
)

runs (                           -- first-class audit unit
  id           TEXT PRIMARY KEY,
  thread_id    TEXT NOT NULL REFERENCES threads,
  agent_id     TEXT NOT NULL REFERENCES profiles,
  contract     JSON NOT NULL,     -- model, effort, scope, tools actually applied
  status       TEXT NOT NULL,     -- running | done | error | interrupted
  usage        JSON,              -- tokens, cost
  outcome      JSON,              -- compliance summary
  started_at   TEXT NOT NULL,
  ended_at     TEXT
)

trace_events (                   -- observed agent actions (enforcement-verification signal)
  id           TEXT PRIMARY KEY,
  run_id       TEXT NOT NULL REFERENCES runs,
  agent_id     TEXT NOT NULL,
  ts           TEXT NOT NULL,
  action       TEXT NOT NULL,     -- write_file | read_file | bash | ...
  target_path  TEXT,              -- service derivable by prefix-match vs code roots
  raw          JSON
)

violations (                     -- persisted compliance results, with attribution
  id           TEXT PRIMARY KEY,
  rule_id      TEXT NOT NULL,
  layer        TEXT NOT NULL,     -- structural | exit | governance | behavioral
  severity     TEXT NOT NULL,
  message      TEXT NOT NULL,
  artifact     TEXT,
  run_id       TEXT REFERENCES runs,      -- attribution
  agent_id     TEXT,                       -- attribution (join via trace)
  issue_id     TEXT,
  fix_hint     TEXT,
  created_at   TEXT NOT NULL,
  resolved_at  TEXT
)

corrections (                    -- human feedback queue (seed of the self-improving OKF loop)
  id           TEXT PRIMARY KEY,
  violation_id TEXT REFERENCES violations,
  agent_id     TEXT,
  issue_id     TEXT,
  note         TEXT NOT NULL,
  created_at   TEXT NOT NULL
)

meta ( key TEXT PRIMARY KEY, value TEXT )   -- schema_version, etc.
```

**Compiled context** is a query, not a stored blob: ordered `turns WHERE included=1` for a
thread, prepended with the role directive and injected OKF artifacts.

---

## 5. Module map

### New — operational store layer (single typed writer)
- `store/db.py` — connection, schema, migrations, WAL.
- `store/profiles.py` — profile CRUD. *(was the PRD's `profiles.py`)*
- `store/threads.py` — threads + turns; `compile_context(thread_id)`; `set_included(turn_id, bool)` (pruning). *(absorbs the PRD's `history.py`)*
- `store/runs.py` — run lifecycle (`create / complete / interrupt`) + audit queries.
- `store/trace.py` — trace append + queries. *(was the PRD's `tracer.py`)*
- `store/violations.py` — violation persistence + attribution joins.
- `store/corrections.py` — corrections queue. *(was the PRD's `corrections.py`)*

### New — governance / execution layer
- `execution/contract.py` — `ExecutionContract` (actor, context, scope, model, effort, tools).
- `execution/adapters/claude.py`, `execution/adapters/codex.py` — strict adapters that translate
  the contract to native flags and **hard-enforce** what the provider supports. *(refactor of `integration/runners.py`)*
- `execution/service.py` — orchestrates the run lifecycle; per-actor serialization queue. *(evolves `integration/service.py`)*

### Refactored — compliance layer (one engine, four layers)
- `core.py` — `Violation`, `Severity` *(unchanged)*.
- `eval_context.py` — `EvaluationContext { okf, trace, contract, actor, scope }`.
- `index.py` — still builds the OKF slice (today's `OKFContext`), now a member of `EvaluationContext`.
- `rules/base.py` — `HephaestusRule` widened: `check(ctx: EvaluationContext)`, declares `layer`, `trigger`, `scope`.
- ~~`rules/structural.py` — S-001..S-006 refactored to read `ctx.okf`.~~ **Superseded:** the hardcoded `S-001..S-006` structural library was removed 2026-06-23; governance moved to user-authored artifact-spec predicates run by the generic `rules/registry.py`. There is no `structural.py` today. See `docs/design/governance-engine.md`.
- `rules/exit.py` — exit rules as `HephaestusRule` subclasses (`layer="exit"`, `scope="issue"`).
- `rules/governance.py` — scope/contract/skill rules (`layer="governance"`, read `ctx.trace` + `ctx.contract`); the shipped set is `G-001`/`G-002`/`G-003`.
- `rules/registry.py` — run rules selected by layer/trigger/scope.

### Knowledge layer (mostly unchanged)
- `frontmatter.py`, `models.py` — unchanged.
- `identity.py` — writes/loads the `agents/identities/{agent_id}.json` provenance card.

### Unchanged in shape
- `handoff_parser.py`, `watch.py` (still `*.md`-only → only OKF knowledge triggers re-scan, which is correct), `codeview.py` (already multi-root), `dashboard.py`, `desktop.py` Bridge (methods now delegate to store modules).

---

## 6. Run lifecycle (the loop that ties it together)

1. **Trigger** — user sends a message in a thread, *or* the Orchestrator emits a handoff marker → user confirms the Spawn button.
2. **Build contract** — `ExecutionContract` from the actor's profile (model, effort, scope, tools) + the thread.
3. **Compile context** — `[role directive] + [injected OKF artifacts] + [included turns] + [new message]`. Client-owned (D5).
4. **Open run** — create `runs` row (`status=running`); append the user turn.
5. **Dispatch** — provider adapter runs with hard governance applied (tool allow-list, sandbox, cwd jail) (D6).
6. **Stream** — for each event: append a turn; append a `trace_event` for tool calls; push to UI (run-scoped).
7. **Close run** — mark `done`, record usage; append the session to the identity card.
8. **Evaluate** — build `EvaluationContext` (OKF + this run's trace + contract); run governance rules (on run completion) and exit rules (on handoff); persist `violations` with attribution (D7).
9. **Surface** — violations → push notifications; "Correct →" writes a `corrections` row (D8 backstop loop).

**Concurrency:** steps run in parallel across actors; per actor they serialize via a queue.
**Crash:** if the app dies mid-run, the provider state is lost but transcript + contract are
durable → run marked `interrupted`; the user re-runs against the preserved curated context.

---

## 7. What this supersedes (the earlier flat-file profile design)

- Flat files in `agents/` for history/trace/corrections/profiles → **operational store** (§2, §4).
- `history.py` / `tracer.py` / `corrections.py` as tree-writers → **store modules** (§5).
- Free-function exit rules diverging from `HephaestusRule` → **one unified rule interface** (D7).
- Ephemeral `run_id` → **first-class persisted `runs`** (D8).
- `working_dir` as a required profile field → **optional**, defaults to the workspace (D3).
- Implicit single root → **explicit Workspace** = OKF root + N code roots (D2/D3).
- Opaque Claude provider-resume as the context mechanism → **client-owned compiled context** (D5).

The earlier design's *user stories, UI surfaces (roster / conversation / spawn / toasts / correction box),
and out-of-scope list remain valid.* This document revises the *implementation foundation* beneath them.

---

## 8. What the foundation deliberately enables later (not built now)

- **Cross-actor context transfer** — lifting one actor's relevant turns into another's compiled context (natural once context is client-owned and structured).
- **Code-graph overlay** — the `trace_events` table is its data layer; nodes light up from observed actions.
- **Correction promotion** — `corrections` → directive/rule edits (the self-improving OKF loop, Phase 3).
- **Behavioral (LLM-judged) rules** — a fourth `layer` on the same rule interface.
- **A2A interoperability** — identity cards are already A2A-shaped.
- **Cost/effort analytics** — `runs.usage` + `runs.contract` make per-model/per-effort reporting a query.
```
