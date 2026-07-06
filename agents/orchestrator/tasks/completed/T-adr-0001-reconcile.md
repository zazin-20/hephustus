---
task: T-adr-0001-reconcile
role: architect
status: completed
created: 2026-07-05
completed: 2026-07-05
owner: orchestrator
---

**Result:** Reconciled via **supersede, not rewrite** (keeps append-only ADR
history, matches ADR-0002 precedent). New `docs/adr/0003-node-graph-is-an-
executable-gatekeeper-runtime.md` (Accepted) records the reversal + reasoning
(the runtime IS the compliance layer, so consistent with the compliance-first
posture) + a vocabulary table mapping ADR-0001's 7 typed nodes onto the shipped
`Node`+`Placement`+`Edge`+`Guard` model with AFK/HITL + ask/allow. ADR-0001 kept
verbatim under a superseded banner. Docs only; uncommitted. Architect log updated.

# Task: Reconcile ADR-0001 to the shipped gatekeeper runtime

## Goal
ADR-0001 (`docs/adr/0001-node-based-workflow-creator.md`) is stale and now
contradicts the code. Bring the recorded decision into line with what actually
shipped.

## Why (routing)
ADRs are architecture records → Architect owns end-to-end (docs only, no
routing to Worker). Surfaced by the 2026-07-05 verification.

## The contradiction (verified)
- ADR-0001 decides the node graph is **"a planning and authoring surface, NOT
  a new runtime engine"** and explicitly lists **"Make the graph the runtime
  engine"** under *Alternatives Considered → Rejected*.
- But `hephaestus/workflow_runtime.py` **is** a gatekeeper execution engine: it
  runs the graph node-by-node, resolves each placement's contract, streams the
  provider run, evaluates entry/exit gates (`WF-ENTRY`/`WF-OUT`/`WF-SKILL`),
  honors HITL/AFK + ask/allow advance, and emits live node/edge state.
- ADR is still marked **Status: Proposed** though the runtime, the canvas, and
  the desktop bridge (`run_workflow`) are all built and wired.

The code has intentionally moved *toward the product vision* (an executable
graph) and *past* ADR-0001's recorded stance. The decision record must catch up.

## Scope for the Architect
- Reconcile the record to reality: either supersede ADR-0001 with a new ADR
  that accepts the executable gatekeeper runtime, or revise ADR-0001 in place
  (Status → Accepted/Superseded) with a corrected Decision + Consequences that
  describe the runtime as it exists. Architect's call on which form.
- Keep the honest history (what was originally rejected and why it changed) —
  do not silently rewrite the past; record the evolution.
- Cross-check the node set: ADR lists `Start/Agent/Condition/Handoff/QA/Notify/
  End`; the shipped model is `Placement`+`Edge`+`Guard` with AFK/HITL +
  ask/allow. Reconcile the vocabulary or note the divergence.

## Guardrails
- Docs only. No `.py`/frontend edits. No commits without user confirmation.
- Append a dated entry to `agents/architect/log.md`.

## Dispatch
- Agent: general-purpose (fresh context), carrying `agents/architect/architect.md`.
