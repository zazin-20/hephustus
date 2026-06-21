# Hephaestus — Coordinator Build Issues

Tracer-bullet issues for the Coordinator phase. Each is a thin vertical slice that
cuts end-to-end (schema → store → service → bridge → UI) and is demoable on its own.

Source of truth for the design: [`../architecture-coordinator.md`](../architecture-coordinator.md)
and [`../prd-coordinator.md`](../prd-coordinator.md).

> Note: these are **build tickets for Hephaestus itself** — distinct from
> `agents/architect/issues/`, which is the OKF *domain* tree that role-agents consume.

## Slices

| # | Title | Type | Blocked by |
|---|---|---|---|
| 001 | Workspace + operational store bootstrap | AFK | — |
| 002 | Agent profiles → roster | AFK | 001 |
| 003 | Threads + Runs + transcript | AFK | 002 |
| 004 | Client-owned compiled context + pruning | AFK | 003 |
| 005 | Trace capture + audit view | AFK | 003 |
| 006 | EvaluationContext + unified rule engine | AFK | 005 |
| 007 | Execution Contract + hard governance + governance rules | AFK (live verify) | 006 |
| 008 | Orchestrator handoff → gated Spawn | AFK | 006 |
| 009 | Compliance notifications + Correction Box | AFK | 007 |

Dependency DAG: `001 → 002 → 003 → 004` · `003 → 005 → 006` · `006 → 007 → 009` · `006 → 008`
