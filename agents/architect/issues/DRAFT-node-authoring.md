# DRAFT — Node authoring: make the full Node contract authorable + editable from the UI

> **OPENED as [#28](https://github.com/zazin-20/hephustus/issues/28)
> (2026-07-07).** The `## What to build` / `## Acceptance criteria` /
> `## Blocked by` sections below were used as the issue body verbatim. This file
> remains the local spec-of-record elaboration; the GitHub issue is now the
> definition of done for the Worker.

**Owner:** one dedicated Worker (see `issue-dag.md`)
**Routing:** Architect authored the spec; Worker implements; QA verifies.
**Relates to:** ADR-0003 (the graph is an executable gatekeeper runtime — the
fields this issue exposes are the gates that runtime already enforces).

## What to build

Close the gap between the `Node` data model — which already carries the full
guardrail/artifact contract — and what a user can author through the desktop UI.
Today a node created from the app is a stub: only `name, provider, tags, rules,
model, effort, working_dir` are settable. The seven fields that actually define
a node's guardrails and artifact bindings are dropped at the bridge and have no
UI at all. There is also no way to **edit** an existing node.

Ground truth (verified in code, 2026-07-05):

- **DAL already supports the full contract.** `hephaestus/store/nodes.py::create_node`
  accepts `inputs, outputs, skills, skill_obligations, allowed_paths,
  allowed_tools, context_policy`; the `nodes` table has all columns
  (`store/db.py`); the `Node` dataclass is complete.
- **No update path exists in the DAL.** `store/nodes.py` has `create_node`,
  `get_node`, `list_nodes`, `delete_node` — but **no `update_node`**. The edit
  path therefore requires a new DAL function, not just UI work.
- **The bridge is the choke point.** `desktop.py::Bridge.create_node` (~line 130)
  exposes only the 7 stub fields and its return payload is partial
  (`node_id, name, provider, tags, status` — it drops the rest, so a UI form
  cannot hydrate from the create response).
- **The frontend mirrors the cap.** `frontend/src/api.js::createNode` (~line 117)
  forwards the same 7 args. `WorkflowCanvas.jsx` only *places* pre-existing
  `available_nodes`; there is no node-authoring form.
- **These fields already drive runtime behavior** when set (see ADR-0003):
  `inputs`→entry gate `WF-ENTRY-001`; `outputs`→`WF-OUT-*` artifact-spec exit
  rules; `skill_obligations`→`WF-SKILL-*` exit rule + `G-003`; `allowed_paths`→
  `G-001`; `allowed_tools`/`skills`→node contract + context. Widening authoring
  lights up guardrails that are already built but currently unreachable.

Scope, in three layers:

1. **DAL — add `update_node`.** Add `update_node(db_path, node_id, *, ...)` to
   `store/nodes.py` that updates the mutable node fields (all except
   `node_id`/`created_at`) and returns the updated `Node`. Keep the identity
   card in sync the way `create_node`/`delete_node` do (rewrite the card when
   name/tags change). Do not change `node_id` or `created_at`.

2. **Bridge + api.js — widen to the full field set.**
   - `Bridge.create_node`: accept `inputs, outputs, skills, skill_obligations,
     allowed_paths, allowed_tools, context_policy` (keyword args, each defaulting
     to `None`/`[]` so existing callers are unaffected) and pass them through to
     `create_node_record`. Return the **full** node payload (all contract fields)
     so a UI edit form can hydrate from it.
   - Add `Bridge.update_node(node_id, …)` mapping to the new DAL `update_node`.
   - `api.js`: widen `createNode(...)` to forward the full field set and add
     `updateNode(nodeId, …)`. Keep the `window.pywebview?.api?.…` guard pattern
     used by the other wrappers.

3. **UI — a create/edit node form.** Add a node-authoring form (reachable from
   the node catalog / canvas node list) that creates a new node and edits an
   existing one through the same form, pre-filled from the node on edit. Fields:
   - existing: `name, provider, tags, rules, model, effort, working_dir`;
   - new list-typed fields with add/remove row editors: `inputs, outputs,
     skills, skill_obligations, allowed_paths, allowed_tools`;
   - `context_policy` — see decision below (rendered inert).
   On save, call `createNode`/`updateNode`; refresh the node list so the new/edited
   node is immediately available to place on the canvas.

### Decision — `context_policy` treatment: **hold the active control; plumb the field inert**

`context_policy` is persisted by the DAL and table but has **no runtime
consumer** — compression is deferred behind the Headroom adapter seam
(see `T-prompt-compression` / the governance-engine context notes). Recommendation:

- **Plumb it through** the bridge + `api.js` pass-through (so the data plane is
  symmetric with the DAL and no later migration is needed to start carrying it).
- **Do NOT surface an editable control** for it in the authoring form yet.
  Render it **read-only / disabled** with an explicit label:
  *"Reserved — no runtime effect until context compression lands
  (see T-prompt-compression)."*

Reasoning: the field's **value vocabulary is undefined** until the compression
adapter defines what a policy means. Letting users author free-form values now
would create silent data debt (values the eventual consumer can't interpret) and
imply a capability that does not exist. Holding the *control* while plumbing the
*field* keeps the pipeline honest and migration-free: when the compression
adapter lands, it defines the value schema and flips the same control live in a
follow-up, with zero data-model change. This is a deliberately narrower stance
than "expose-as-inert editable," chosen specifically to avoid authoring
un-interpretable values ahead of the consumer.

## Acceptance criteria

- `store/nodes.py` gains `update_node(...)` that updates all mutable `Node`
  fields, preserves `node_id`/`created_at`, returns the updated `Node`, and keeps
  the identity card consistent. Covered by a unit test.
- `Bridge.create_node` accepts and forwards all seven previously-dropped fields
  and returns the full node contract payload (not the 5-field stub).
- `Bridge.update_node` exists and round-trips an edit (create → update → read
  back shows the changed fields).
- `api.js` `createNode` forwards the full field set and `updateNode` exists,
  both behind the standard bridge-presence guard.
- A node create/edit form in the UI can set `inputs, outputs, skills,
  skill_obligations, allowed_paths, allowed_tools` (add/remove list editors) plus
  the existing fields, creates a new node, and edits an existing node pre-filled
  from its current values; the node list refreshes after save.
- `context_policy` is plumbed through create/update but its UI control is
  disabled/read-only with the "reserved, no runtime effect" label — no editable
  free-form value is accepted from the form.
- Existing callers of `create_node` / `createNode` (which pass only the 7 stub
  fields) keep working unchanged — the new params default to empty and are
  optional.
- A node authored with `inputs`/`outputs`/`skill_obligations` set is observably
  gated at runtime (entry `WF-ENTRY-001` / exit `WF-OUT-*` / `WF-SKILL-*`),
  demonstrating the previously-unreachable guardrails are now reachable from the
  UI. (Can be shown via an integration test or a QA trace, not necessarily a new
  runtime feature.)
- No existing test is weakened or deleted; the full suite stays green. Product
  code is untouched outside `store/nodes.py`, `desktop.py`, `frontend/src/api.js`,
  and the frontend node-form component(s).

## Blocked by

- **Nothing.** This work is **independent and ready now**. It does **not** depend
  on dynamic fan-out and does **not** depend on the deferred context-compression
  (Headroom) adapter — `context_policy` is deliberately held inert precisely so
  this issue needs neither. The DAL, table, runtime gates, and canvas placement
  it builds on are all already merged to `main` (#18, #20, #23, #25).
