---
task: T-node-authoring
role: architect
status: completed
created: 2026-07-05
owner: orchestrator
---

**Result (spec slice):** Architect authored the spec at
`agents/architect/issues/DRAFT-node-authoring.md` and placed it in `issue-dag.md`
(INDEPENDENT / ready-now; builds on merged #18/#20/#23/#25). Discovery: the DAL
has **no `update_node`** — the edit path needs a new DAL fn, not just UI.
`context_policy`: plumb inert, hold the UI control (reserved label) until
compression lands. **Issue opened 2026-07-07 as
[#28](https://github.com/zazin-20/hephustus/issues/28); dispatched to one Codex
Worker** in worktree `.claude/worktrees/issue-028-node-authoring` on branch
`feat/028-node-authoring`. **DONE 2026-07-07** — Worker implemented (213 backend
tests, +2; vite build green), Architect handoff review APPROVED, merged to main
as `91a222e` (impl `4e76fc7`), pushed, issue #28 closed. QA dispatch was skipped
per explicit user direction to merge. Carry-forward (non-blocking): `update_node`
resets identity-card `sessions=[]` on edit — revisit when session recording is
wired to a runtime path.

# Task: Complete node authoring — make the full Node contract authorable from the UI

## Goal
Close the gap between the `Node` data model (which already carries the whole
guardrail/artifact contract) and what a user can actually author through the
desktop UI. Today a node created from the app is a stub: provider + model +
effort + tags + rules only. The artifact bindings and guardrails that *define*
a node in the product vision cannot be set from the UI at all.

## Why (routing)
Design/spec of a product surface → Architect (static route). Architect authors
the issue spec (GitHub issue = spec of record); Worker implements afterward.
Surfaced by the 2026-07-05 vision-vs-codebase verification.

## Ground truth (verified in code)
- **DAL already supports the full contract.** `store/nodes.py::create_node`
  accepts `inputs, outputs, skills, skill_obligations, allowed_paths,
  allowed_tools, context_policy` and the `nodes` table has the columns
  (`store/db.py`). The Node dataclass is complete.
- **The bridge is the choke point.** `desktop.py::Bridge.create_node` (~line
  130) exposes only `name, provider, tags, rules, model, effort, working_dir`.
  The other seven fields are dropped on the floor.
- **The frontend mirrors that cap.** `frontend/src/api.js::createNode`
  (~line 117) forwards the same 7 args. `WorkflowCanvas.jsx` only *places*
  pre-existing `available_nodes`; there is no node-authoring form.
- **These fields already drive real runtime behavior** if set:
  `inputs`→entry gate `WF-ENTRY-001`; `outputs`→`WF-OUT` artifact-spec exit
  rules; `skill_obligations`→`G-003` + `WF-SKILL` exit rule; `allowed_paths`→
  `G-001`; `allowed_tools`/`skills`→context + contract. So widening authoring
  lights up guardrails that are already built but currently unreachable.

## Scope for the Architect (spec, don't implement)
1. Author the issue spec (`## What to build` / `## Acceptance criteria` /
   `## Blocked by`) for: (a) widening `Bridge.create_node` + `api.js` to the
   full field set, and (b) a node-authoring UI (create/edit form) that sets
   inputs, outputs, skills, skill_obligations, allowed_paths, allowed_tools —
   plus a node *edit* path, not just create.
2. Decide the treatment of `context_policy`: it is authorable but has **no
   runtime consumer yet** (compression deferred — see T-prompt-compression).
   Recommend whether to expose it now (labelled inert) or hold it until the
   compression adapter lands. Architect's call; record the reasoning.
3. Sequence it in `issue-dag.md` (one dedicated owner; note it does NOT depend
   on dynamic fan-out or compression — it is independent and ready).

## Guardrails
- Architect produces the SPEC + DAG placement only. No product code
  (`hephaestus/*.py`, `frontend/**`) edits. No GitHub issue creation, no
  commits/merges without explicit user confirmation.
- Append a dated entry to `agents/architect/log.md` (per the per-role logging
  rule added 2026-07-05).

## Dispatch
- Agent: general-purpose (fresh context), carrying `agents/architect/architect.md`.
