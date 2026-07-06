---
task: T-dynamic-fanout
role: architect
status: deferred
created: 2026-07-05
owner: orchestrator
---

# Task: Dynamic fan-out — runtime-variable node instances (DEFERRED)

## Status
**Deferred by the user 2026-07-05.** Recorded so it is not lost; do NOT dispatch
until re-prioritized.

## Goal (when picked up)
Support workflows where one node emits *N* artifacts and fans out to *N* runtime
node instances — the vision's `business req → pm → prd → architect → ard →
issue-generator → n*(issues) → n*(worker)` shape.

## Ground truth (verified)
`workflows.py` placements + edges are **static / pre-declared**;
`workflow_runtime.py` iterates a fixed placement queue. `_output_bindings`
handles multiple *declared* outputs but not a runtime-variable count. There is
no mechanism to spawn a variable number of placements from a node's actual
output. This is the largest structural gap vs the product vision and will need
its own design pass (likely a grill session before spec).

## Dispatch
- Deferred. No agent assigned.
