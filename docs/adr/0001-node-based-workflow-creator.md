# ADR-0001: Node-Based Workflow Creator for Coordinator Pipelines

**Status:** Superseded by [ADR-0003](0003-node-graph-is-an-executable-gatekeeper-runtime.md) (2026-07-05)
**Date:** 2026-06-23
**Owner:** architect

> **Superseded — read ADR-0003 for the accepted decision.** This ADR's core
> decision (the node graph is *"a planning and authoring surface, NOT a new
> runtime engine"*, and *"make the graph the runtime engine"* is rejected) was
> **reversed** by the code that subsequently shipped. `hephaestus/workflow_runtime.py`
> is an executable gatekeeper engine that runs the graph node-by-node under
> Hephaestus's gates, and the typed node set below (`Start/Agent/Condition/…`)
> was replaced by a uniform `Node` + `Placement` + `Edge` + `Guard` model with
> AFK/HITL interactivity and ask/allow advance. The text below is retained
> verbatim as honest history of the original stance and why it was rejected;
> ADR-0003 records the reversal, the reasoning, and the vocabulary reconciliation.

## Context

Hephaestus already models the pipeline as a sequence of role-driven stages:
Orchestrator, Product Manager, Architect, Worker, QA, and completion logging.
The current architecture also makes two things explicit:

- Hephaestus is a control plane and compliance layer, not the orchestrator.
- Runtime state belongs in the operational store, while durable knowledge lives
  in the OKF tree.

There is already a lightweight representation of work ordering in
`agents/issue-dag.md`, and the Coordinator architecture points toward a future
code-graph overlay. What is missing is a first-class way to author, review, and
revise workflow structure without burying it in prose or hard-coding it into the
execution layer.

The question is whether that workflow authoring surface should be:

- a node-based editor,
- a text-only DSL,
- or a hidden implementation detail behind the existing coordinator UI.

## Decision

Build a **node-based workflow creator** as a **planning and authoring surface**,
not as a new runtime engine.

The editor will let a user compose a workflow as a directed graph of typed
nodes and edges. The graph will then compile into the existing Hephaestus
execution model:

- role-based agent selection
- issue/thread context
- gated handoffs
- spawn confirmation
- compliance evaluation
- trace logging

Workflow definitions will be stored as durable OKF knowledge, not as ephemeral
UI state. Runtime execution state continues to live in the operational store.

The workflow creator will support a small, explicit node set at first:

- `Start`
- `Agent`
- `Condition`
- `Handoff`
- `QA`
- `Notify`
- `End`

Edges describe the allowed transitions. Cycles are rejected unless a future ADR
explicitly adds loop semantics.

## Consequences

### Positive

- The workflow becomes visible and reviewable instead of being hidden in prose
  or spread across code.
- The Coordinator UI can reuse the graph as a planning aid and as an execution
  preview.
- The same artifact can support future trace overlays and audit/replay views.
- The model matches the project language: issue DAGs, handoffs, and stage
  transitions.
- The graph can be validated before execution, which fits the existing
  compliance-first posture.

### Negative

- The editor introduces a second layer of complexity above the existing
  coordinator model.
- The graph schema must be versioned and migrated carefully.
- Validation logic is required to prevent invalid graphs, missing exits, and
  broken handoff targets.
- Users may expect the graph to be executable in arbitrary ways; the
  implementation must stay narrower than that expectation.

### Neutral / operational

- Workflow definitions need a stable storage location. The preferred shape is an
  OKF document under `agents/workflows/` or an equivalent documented tree path.
- Execution will still use the existing Orchestrator-confirmed spawn flow. The
  creator does not bypass user confirmation.
- The graph editor can start as a planning tool and later become a source for
  generated issue plans or handoff templates.

## Alternatives Considered

### 1. Keep workflows as prose only

Rejected because prose does not give enough structure for validation, diffing,
or future graph overlays. It also makes reuse across sessions harder.

### 2. Use a hidden JSON or YAML DSL only

Rejected because the primary user need is to think in nodes and edges, not in
serialization syntax. A DSL may still exist behind the scenes, but it should not
be the only authoring surface.

### 3. Make the graph the runtime engine

Rejected because it would conflict with the current architecture. Hephaestus is
the control plane and compliance layer; the Orchestrator and providers remain
the execution path.

### 4. Store the workflow only in SQLite

Rejected because workflow definitions are durable project knowledge, not
transient telemetry. The OKF tree is the right home for authored structure.

## Notes

This ADR intentionally aligns with the existing `agents/issue-dag.md` artifact.
If that file becomes the canonical workflow input, this ADR should be updated to
reference it directly and describe the migration path from the current prose
sequence to the node graph.
