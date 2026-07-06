# ADR-0003: The Node Graph Is an Executable Gatekeeper Runtime

**Status:** Accepted
**Date:** 2026-07-05
**Owner:** architect
**Supersedes:** ADR-0001 (node graph as a planning/authoring surface only)

## Context

ADR-0001 (2026-06-23) decided the node-based workflow creator would be **"a
planning and authoring surface, NOT a new runtime engine,"** and explicitly
listed **"Make the graph the runtime engine"** under *Alternatives Considered →
Rejected*, on the reasoning that Hephaestus is a control plane and compliance
layer while "the Orchestrator and providers remain the execution path." ADR-0001
was never advanced past **Status: Proposed**.

Since then the code moved deliberately *toward the product vision of an
executable graph* and *past* ADR-0001's recorded stance. As of the 2026-07-05
verification, the graph is not a preview — it is the thing that runs:

- **`hephaestus/workflow_runtime.py` (`WorkflowRuntime.run`) is a gatekeeper
  execution engine.** It topologically walks the graph from its start
  placements (`_start_placements`), and for each placement it: resolves the
  node's execution contract, streams the provider run through `AgentService`,
  evaluates **entry gates** (`WF-ENTRY-001`, declared `inputs` must exist),
  evaluates **exit gates** (`WF-OUT-*` artifact-spec rules from `outputs`, and
  `WF-SKILL-*` obligation rules from `skill_obligations`) via
  `evaluate_spawn_gate`, honors **HITL/AFK** interactivity and **ask/allow**
  edge advance, supports blocked-node **override**, and emits live per-node /
  per-edge state and notifications through the `on_update` callback.
- **The surrounding wiring is built.** The desktop bridge exposes
  `run_workflow` (`desktop.py`), the canvas renders live run state
  (`WorkflowCanvas.jsx`), and the runtime returns a first-class
  `WorkflowRunResult` with per-step status (`RUNNING` / `WAITING_HUMAN` /
  `BLOCKED` / `AWAITING_CONFIRM` / `DONE`).
- **The shipped node vocabulary diverged from ADR-0001's typed set.** ADR-0001
  named seven node *types* (`Start / Agent / Condition / Handoff / QA / Notify /
  End`). The shipped model (`hephaestus/workflows.py`) has no typed-node enum at
  all. Instead it is a **uniform `Node`** (provider + contract + guardrail
  fields) **placed** via `Placement` and connected by `Edge`s, with behavior
  expressed structurally rather than by node type (see Vocabulary below).

The decision record must catch up to the code. This ADR does not rewrite
ADR-0001 (its original stance and rejection are real history and are preserved);
it **supersedes** it and records why the stance reversed.

## Decision

**Adopt the executable node graph as a first-class gatekeeper runtime.** The
node graph is both the authoring surface *and* the execution model. Running a
workflow means walking its graph node-by-node under Hephaestus's gates; the
graph is not merely compiled into a separate execution path and it is not a
preview-only artifact.

This is a deliberate reversal of ADR-0001's "planning surface, not a runtime
engine" and of its rejection of "make the graph the runtime engine." The
reversal is *consistent with*, not a violation of, Hephaestus's compliance-first
posture, because the graph runtime **is** the compliance layer: every node
transition is gated (entry inputs, exit artifact/skill obligations, spawn
gating, HITL, ask/allow confirmation, and human override). Hephaestus does not
cede execution to an external orchestrator; it *is* the gatekeeping orchestrator
of the authored graph, while providers remain the leaf execution path for a
single node's run.

### Vocabulary reconciliation (ADR-0001 typed nodes → shipped structural model)

The seven typed nodes are **not** implemented as node types. Their intent is
realized structurally over a uniform `Node` + graph topology:

| ADR-0001 typed node | How it is realized in the shipped model |
| --- | --- |
| `Start` | A `Placement` with no incoming `Edge` (`_start_placements`), enqueued first. |
| `End` | A `Placement` with no outgoing `Edge`; run reaches `DONE` when the queue drains. |
| `Agent` | The uniform `Node` itself (provider + model/effort + contract) — every placement runs a provider node. |
| `Condition` | An `Edge` carrying a `Guard(condition, label)`; guarded edges are also the loop-permitting case in cycle checks. |
| `Handoff` | An `Edge` between placements, plus the `HandoffMarker` / spawn-gate `SpawnCard` emitted at each transition. |
| `QA` | A `Node` whose exit gate is an artifact-spec / skill obligation (`WF-OUT-*` / `WF-SKILL-*`) — QA is a gate, not a node type. |
| `Notify` | Runtime-emitted `notifications` (`hitl_needed`, `node_done_green`, …) on the `on_update` stream, not an authored node. |

Two dimensions ADR-0001 did not name, and which the runtime adds, are authored
per placement/edge rather than as node types:

- **Interactivity** — `NodeInteractivity.AFK | HITL` on a `Placement`
  (HITL pauses the run for human input).
- **Advance mode** — `AdvanceMode.ALLOW | ASK` on an `Edge` (ASK pauses at
  `AWAITING_CONFIRM` for explicit user confirmation before advancing).

Cycles remain **rejected unless guarded**: `_reject_unguarded_cycles` allows a
back-edge only if it carries a `Guard`, which is the "future ADR explicitly adds
loop semantics" escape hatch ADR-0001 anticipated — now realized via guarded
edges.

### What carries forward unchanged from ADR-0001

- Workflow definitions are **durable authored knowledge**, stored as
  YAML/JSON graph documents under the OKF `workflows/` tree
  (`save_workflow` / `OKFLayout.workflow_path`) — not ephemeral UI state and not
  telemetry in SQLite. (ADR-0001 alternatives #4 and the OKF-storage stance
  still hold.)
- The graph is **validated before execution** (`_validate_workflow`: unique
  placement ids, edge endpoints resolve, no unguarded cycles).
- Prose-only and DSL-only authoring remain rejected for the same reasons
  ADR-0001 gave; the node graph is the authoring surface.

## Consequences

### Positive

- The decision record now matches the shipped system: reviewers and future
  agents reading ADR-0001 are no longer told the graph is preview-only when it
  is the runtime.
- Guardrails that are *already built* (entry/exit gates, obligations, HITL,
  ask/allow, override) are recorded as first-class, intended behavior rather
  than an undocumented drift.
- The uniform-`Node` + structural-behavior model is simpler to extend than a
  closed typed-node enum: new behavior is a new edge/placement attribute or a
  new gate rule, not a new node class.

### Negative / risk

- The graph runtime is now load-bearing execution, so its gates are on the
  critical path — a bug in `WorkflowRuntime` blocks real runs, not just a
  preview. This raises the test bar for changes to `workflow_runtime.py`.
- The authored `Node` contract is richer than any UI currently exposes (only
  7 of ~14 fields are authorable from the desktop bridge today). Superseding
  ADR-0001 makes that gap a recorded, addressable item rather than a silent one
  (see *Relates to*).

### Neutral

- No product code changes are made by this ADR; it reconciles the record to
  code that already shipped (#20 workflow model, #23 gatekeeper runtime,
  #25 node-graph editor — all merged to `main`).
- ADR-0001 is retained verbatim as honest history with a superseded banner; its
  original rejection reasoning is the "before" half of this record.

## Alternatives Considered

1. **Revise ADR-0001 in place (flip its Status to Accepted, rewrite its
   Decision).** Rejected — ADRs are append-only records; rewriting an
   already-published decision erases the honest history that the stance was
   genuinely reversed. A superseding ADR preserves both the original rejection
   and the reversal, matching ADR-0002's "Supersedes / relates to" precedent.
2. **Leave ADR-0001 as "Proposed" and add only a note.** Rejected — it would
   leave the canonical record actively contradicting the code (graph "NOT a
   runtime engine" while `workflow_runtime.py` runs it), which is the exact
   drift this reconciliation exists to close.
3. **Restore ADR-0001's stance in code (make the graph preview-only again).**
   Rejected — the executable gatekeeper runtime *is* the product vision and is
   already merged and wired; reverting it would discard shipped, tested value to
   satisfy a stale record. The record should follow the code here, not vice
   versa.

## Supersedes / relates to

- **Supersedes ADR-0001** (`0001-node-based-workflow-creator.md`): reverses its
  "planning surface, not a runtime engine" decision and its rejection of an
  executable graph; reconciles its typed-node vocabulary to the shipped
  structural model.
- Records the intended design behind issues **#20** (workflow model + storage),
  **#23** (gatekeeper runtime — node-by-node advance, entry/exit gates,
  HITL/AFK), and **#25** (node-graph editor), all merged to `main`.
- Relates to the open **node-authoring** work (widen `Bridge.create_node` +
  `api.js` and add a create/edit UI to the full `Node` contract): this ADR
  establishes *why* those unreachable guardrail fields matter — they are the
  gates the runtime already enforces.
