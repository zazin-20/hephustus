# 001 — Workspace + operational store bootstrap

**Type:** AFK · **Status:** ready-for-agent

## What to build

Introduce a first-class **Workspace** (one OKF root + N service code roots) and a
**per-workspace SQLite operational store** created at `<workspace>/.hephaestus/state.db`
when a workspace is opened.

- Create the full schema on first open (`profiles`, `threads`, `turns`, `runs`,
  `trace_events`, `violations`, `corrections`, `meta`) in **WAL mode**.
- Migrations keyed off `meta.schema_version`; re-opening an existing workspace must be
  idempotent (no wipe), running migrations only when the stored version is behind.
- Service roots discovered by scanning top-level folders that contain a `.git`,
  excluding `agents/`, `archive/`, `node_modules/`. The Code Viewer uses these
  workspace-derived roots instead of the current hardcoded `[project, okf_root]`.

Schema reference: `architecture-coordinator.md` §4.

## Acceptance criteria

- [ ] Opening a workspace creates `.hephaestus/state.db` with all tables and `meta.schema_version` set.
- [ ] Re-opening an existing workspace does not recreate or wipe data; migrations run only when behind.
- [ ] WAL mode is enabled (safe concurrent read/write).
- [ ] Service roots are auto-discovered; `agents/`, `archive/`, `node_modules/` excluded; the Code tab lists them.
- [ ] `.hephaestus/` is gitignored.
- [ ] Tests cover schema creation, idempotent re-open, and a migration version bump.

## Blocked by

- None — can start immediately.
