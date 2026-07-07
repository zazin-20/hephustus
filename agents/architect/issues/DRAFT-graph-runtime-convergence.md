# BACKLOG (needs design) — Converge single-node observation + spawn onto the graph runtime

> **Status: backlog / needs-design.** NOT ready to dispatch and NOT opened on
> GitHub. Requires an ADR-0003-alignment design pass (grill) before it becomes a
> buildable issue. Recorded so the #30 reorg is never mistaken for convergence
> on the node-graph runtime.

**Origin:** Architect handoff review of #30 (2026-07-07). #30 retired the
Coordinator *name* and split it into **Library** (authored state) + **Console**
(runtime observation) — correct god-component debt paydown along the
governance-engine §7.1 authored-vs-runtime seam. But #30 was scoped as pure
reorganization; it did **not** move anything toward the ADR-0003 spine. Two
forward-looking flags fell out of that review.

## Flag 1 — Console should dissolve into the graph canvas, not live as a peer tab

ADR-0003 §7.9: *"Primary monitor = the graph canvas itself, with an author ↔ run
mode toggle,"* and single-node conversation/trace is a **node drill-in on the
canvas**, not a top-level surface. Today `Console.jsx` is a co-equal tab, which
keeps the pre-graph "pick one agent and chat to it" model as a first-class
citizen. Under full ADR-0003, Console should become:
- a **canvas node drill-in** for placed nodes (select a placement → its
  conversation/trace/gates), and
- a **thin ad-hoc runner** for standalone (un-placed) node execution
  (governance-engine §7.1 allows a node to "run standalone *or* placed in a
  graph").

`Console` is therefore a transitional surface wearing a permanent-looking name.

## Flag 2 — The role-based spawn card contradicts the graph gatekeeper + role-removal

`Console.jsx` preserves `parseHandoffMarker → evaluateSpawn → SpawnCard`, and the
card is keyed on `prefill_role`. But:
- the **Node model already removed `role`** (#18 — "Role removed, tags added"),
  and the governance vision §7.1 states *"`role` is removed entirely,"* yet the
  handoff-marker/spawn flow still carries `role`; and
- ADR-0003 gates transitions via the **workflow runtime walking the graph**
  (entry/exit gates, ask/allow edges, HITL) — not a manually-confirmed,
  role-based spawn affordance.

So the spawn card is a pre-graph, role-based manual-spawn concept that ADR-0003 +
the governance model want **absorbed into the graph runtime**. (This predates #30
— the code was only *moved*, not introduced — but it is the one place the reorg
re-cements a slated-for-retirement concept.)

## When picked up
Needs a design/grill pass against ADR-0003 §7.9 + governance-engine §7.1 to
decide: how a canvas node-drill-in replaces the Console tab; what a standalone
ad-hoc runner looks like; and how the handoff-marker/spawn flow is either dropped
in favor of graph-edge gating or reduced to an ad-hoc-only affordance with `role`
removed. Likely one ADR + a small wave of issues. Dependency-adjacent to the
deferred dynamic-fan-out work (both are graph-runtime deepening).
