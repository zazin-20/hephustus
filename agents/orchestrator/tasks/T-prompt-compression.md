---
task: T-prompt-compression
role: architect
status: deferred
created: 2026-07-05
owner: orchestrator
---

# Task: Prompt/context compression adapter (DEFERRED)

## Status
**Deferred by the user 2026-07-05.** Recorded so it is not lost; do NOT dispatch
until re-prioritized. Note the dependency below for T-node-authoring.

## Goal (when picked up)
Make the node's `context_policy` field actually do something: a per-node
context-management adapter that compresses/manages the assembled prompt behind a
seam (Headroom was the previously chosen external tool for this).

## Ground truth (verified)
`context_policy` is stored on the `Node` (dataclass + `nodes` table) but
**consumed nowhere** — `integration/context.py::build_session_context` just
concatenates files raw. The field is inert. The seam (a per-node policy) exists;
the adapter does not.

## Cross-task note
T-node-authoring must decide whether to expose `context_policy` in the authoring
UI now (as an inert, labelled field) or hold it until this adapter lands.

## Dispatch
- Deferred. No agent assigned.
