# 005 — Trace capture + audit view

**Type:** AFK · **Status:** ready-for-agent

## What to build

Record what each agent actually did — the observed action trail.

- Parse tool events from the agent stream into **`trace_events`** (`action`,
  `target_path`, `ts`, `run_id`, `agent_id`).
- A per-run / per-agent **timeline (audit) view**.
- Service is **derived at display time** by prefix-matching `target_path` against the
  workspace code roots — not a stored column.

This table is also the data layer for the future code-graph overlay and the
enforcement-verification signal for governance rules.

Reference: `architecture-coordinator.md` §4 (`trace_events`), §8.

## Acceptance criteria

- [ ] Tool events (write_file / read_file / bash / …) recorded as `trace_events` tied to run + agent.
- [ ] Non-tool events are not recorded as trace.
- [ ] Audit view lists a run's actions in order; filterable by agent and by issue.
- [ ] `target_path` stored; service derived at display time.
- [ ] Tests: tool events captured, non-tool ignored, target extraction for write/read/bash.

## Blocked by

- 003 — Threads + Runs + transcript
