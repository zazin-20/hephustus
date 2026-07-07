---
task: T-coordinator-rehome
role: worker
status: completed
created: 2026-07-07
owner: orchestrator
---

# Task: Retire the Coordinator view — rehome into Library + Console

**Issue:** [#30](https://github.com/zazin-20/hephustus/issues/30). Spec of record:
`agents/architect/issues/DRAFT-coordinator-rehome.md`.

**Why:** "Coordinator" is the superseded pre-graph concept (ADR-0001 → ADR-0003;
absent from governance-engine.md). But it uniquely hosts artifact authoring
(#29's `ArtifactForm`), node delete, and the single-node console + spawn card —
so removal = rehome, not delete. User chose **Library as the default** tab.

**Dispatch:** one `codex:codex-rescue` Worker in worktree
`.claude/worktrees/issue-030-coordinator-rehome` (branch `feat/030-coordinator-rehome`,
off main `46af333`).

**Scope (frontend-only, no backend/bridge/DAL):** split `Coordinator.jsx` →
`Library.jsx` (node + artifact catalogs, full CRUD, reusing NodeForm/ArtifactForm)
+ `Console.jsx` (threaded conversation, trace, spawn card, composer); rewire
`App.jsx` nav to `Library · Console · Canvas · Code · Agent` (default library);
delete `Coordinator.jsx`. Canvas unchanged.

**v1 acceptance:** nothing lost — every Coordinator capability reachable in the
new tabs; build green; product code only under `frontend/src/**`.

**Pre-work landed:** NodeForm human rule-label fix committed to main (`349733c`).

**Guardrails:** no close/merge/push without user confirm. Status stays open until
built + verified + Architect-reviewed.

**DONE 2026-07-07** — Worker split cleanly (Library 702 + Console 628, Coordinator
deleted); Orchestrator verified (build green, 53 modules; no lost refs; api.js/
NodeForm edits cosmetic-only) and committed `9575b14`. Architect handoff review
**APPROVED** (`0d5887f`) — met the reorg charter, nothing dropped — but flagged
that it is NOT ADR-0003 convergence: Console should become a canvas node
drill-in, and the role-based spawn card contradicts the graph gatekeeper +
role-removal. Both captured in `architect/issues/DRAFT-graph-runtime-convergence.md`
(backlog / needs-design). Merged, pushed, #30 closed.
