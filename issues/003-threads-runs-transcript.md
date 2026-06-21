# 003 — Threads + Runs + transcript

**Type:** AFK (live verify optional) · **Status:** ready-for-agent

## What to build

The core conversation + execution loop, persisted.

- Sending a message to an actor creates (or continues) a **thread** and opens a
  first-class **run** (`status` running → done/error/interrupted; `usage` captured).
- The run streams via the existing provider adapter, persisting `user` / `assistant` /
  `tool` **turns** and the **run** record.
- The conversation panel replays a thread's transcript on open.
- **Concurrency:** runs serialize **per actor** (queue); **different actors run in
  parallel**. Streaming to the UI is run-scoped.

Reference: `architecture-coordinator.md` §3, §6 (run lifecycle), D8.

## Acceptance criteria

- [ ] Sending a message creates a `runs` row and persists turns; run transitions running → done.
- [ ] Reopening a thread replays its transcript in order.
- [ ] Two different actors run concurrently; the same actor's runs serialize.
- [ ] App killed mid-run → run marked `interrupted` on next open; transcript-so-far preserved.
- [ ] Echo-runner tests assert run lifecycle, turn persistence, and per-actor serialization.

## Blocked by

- 002 — Agent profiles → roster
