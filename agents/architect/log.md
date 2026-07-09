---
title: Architect Log
updated: 2026-07-09
owner: architect
---

# Architect Log

Architect-local change history: design decisions, spec/handoff events, and rule
changes that are narrower than the system-level rollup in
[../log.md](../log.md).

---

## 2026-07-09 — PRD-01/02/03 decomposed into GitHub issues #31–#47

Ground-truthed the three approved PRDs (`prds/PRD-01…03`) against the current
codebase (Python core `hephaestus/` + `frontend/src/`) and cut them into 17
tracer-bullet vertical-slice issues on the tracker, in integration order, all
AFK + `ready-for-agent`. Key ground-truth findings that shaped the slicing:

- `WorkflowRuntime.run` already accepts `confirm_edges` / `override_placements`
  / `human_inputs`, but `Bridge.run_workflow` never passes them — a paused run
  is a UI dead end. That seam became the wave's tracer bullet (#31).
- Ask edges have no reject path at all; the queue dedup makes re-execution
  impossible — revision loops are a real runtime feature, not UI polish (#35).
- The literal-path fallback PRD-02 removes lives in TWO seams:
  `workflow_runtime._resolve_path` and `integration/context._resolve_declared_path` (#37).
- The PRD-03 learning backend is substantially built (corrections lifecycle,
  frozen-rule promotion with supersede/disable, scope addressing, constitution
  injection); the gap is bridge + UI (#43).
- Nodes have no version field; placements resolve `node_id` live, so silent
  drift is today's behavior (#45).

Wave layout: PRD-01 → #31 session controls, #32 inspector, #33 run-state
legend/filters, #34 snapshot-vs-draft, #35 rejection/revision, #36 Console
dissolution + spawn-card retirement. PRD-02 → #37 artifact-identity edges,
#38 flow visuals, #39 binding invalidation, #40 preflight, #41 context preview,
#42 presentation layer. PRD-03 → #43 learning surface, #44 typed Library,
#45 version pinning, #46 templates, #47 ad-hoc runner.

Reconciliation: `issues/DRAFT-graph-runtime-convergence.md` marked RESOLVED —
Flag 1 folded into #36 + #47, Flag 2 into #36. User-deferred items (dynamic
fan-out; prompt/context compression via `context_policy`) were NOT expanded:
#35/#38/#46 and #41 carry explicit non-goal boundaries instead. All UI-facing
issues cite `agents/design-system/component-library.html` +
`DESIGN_LANGUAGE_*.md` as the implementation guide. Created `issue-dag.md`
(was referenced by the directive but absent) with the wave's dependency graph;
open wave: #31, #32, #33, #37.

---

## 2026-07-08 - Graph runtime PRD set and gallery expansion

Synthesized the graph-runtime design grill into three integration-ordered PRDs
under `prds/`:

- `PRD-01-canvas-runtime-command-center.md`
- `PRD-02-artifact-flow-preflight-context.md`
- `PRD-03-learning-library-and-secondary-runtime.md`

The split matches the agreed rollout order:

1. Canvas-first runtime command center and node drill-in
2. Artifact flow clarity, preflight, and context visibility
3. Learning/corrections, typed library inventory, templates, and the secondary
   ad-hoc runtime path

Also expanded the design-system component gallery to capture the agreed vNext
runtime surfaces, markers, states, and explicit out-of-scope constraints so the
UI decisions are queryable before issue slicing.

No product code changed in this pass; this was a planning and design artifact
update only.

---

## 2026-07-07 — Coordinator retirement spec'd (rehome → Library + Console)

User decided to retire the **Coordinator** view. Grounded it: ADR-0001 (which
tied the graph to "Coordinator pipelines") is superseded by ADR-0003, and the
canonical `governance-engine.md` has no Coordinator concept — but the view
uniquely hosts artifact authoring (#29's `ArtifactForm`, mounted nowhere else),
node delete, and the single-node threaded console + spawn card. So removal =
**rehome, not delete**.

Resolved layout (user picked Library as default): new **Library** tab (node +
artifact catalogs, full CRUD, reusing `NodeForm`/`ArtifactForm`) + new **Console**
tab (threaded conversation, trace, spawn card, composer); delete `Coordinator.jsx`;
`App.jsx` default → `library`; `WorkflowCanvas` unchanged. Pure frontend reorg —
no backend/bridge/DAL touch. Spec → `issues/DRAFT-coordinator-rehome.md`;
DAG-placed. Also landed a small display fix: NodeForm rule pills now read
"Path scope/Model lock/Skill proof · G-00x" instead of a bare id.

---

## 2026-07-07 — Handoff review: #29 artifact authoring → APPROVE

Reviewed the Codex Worker's handoff for #29 (commit `d833d4a`, branch
`feat/029-artifact-authoring`) before QA/merge. Verdict **APPROVE — ready to
merge**; set `reviewed_by: architect` on `handoffs/029.md`.

Walked all seven acceptance criteria; every one passes. Load-bearing checks:
- **DAL is a thin index, file is source of truth** — `store/artifacts.py`
  composes the spec markdown and writes `agents/artifacts/<id>.md`; the DB row
  is `{artifact_id, name, path, tags, created_at}` only. Every write calls
  `load_artifact_spec()` (author-time parse guard), and `test_artifacts.py`
  asserts the composed `## Predicates` parse to the expected labels — a real,
  non-skipped assertion.
- **id-resolution seam is backward-compatible** — `context.py::_resolve_declared_path`
  and `workflow_runtime.py::_resolve_path` try artifact-id first, fall back to
  literal path on `KeyError`; `test_integration.py` proves #28 literal paths
  still resolve.
- **No gating change** — `WF-OUT-*` and context injection untouched; the diffs
  add id→path resolution only.
- **Key risk `Coordinator.jsx` (+364) is additive** — the #28 node roster
  (list/create/edit/delete, full node payload, threads/conversation/trace) is
  intact; artifacts are layered on via a `catalogMode` tab with parallel state.
  Nothing dropped.

Non-blocking: untracked `sample/agents/identities/` is out of scope (Worker
sandbox blocked removing it); minor `min_items` string-coercion hardening noted
as a fast-follow. Committed the handoff + this log entry only; did not touch
product code, merge, push, or close.

---

## 2026-07-07 — Artifact-authoring: grill + DRAFT spec (follow-on to #28)

Ran a grill (grill-me) on the PM's three open decisions for artifact-spec
authoring (`product-manager/todo/artifact-spec-authoring.md`). Resolved:
(1) **storage** = folder-of-markdown source of truth + thin `store/artifacts.py`
index (`artifact_id → path`), node binds by id, backward-compatible with #28
literal paths — NOT relational content (user wants md for agent-readability, git
diffs, future sphinx-style external checkers); (2) **v1 checks** = required
headings (`has_section`/`non_empty`) + `min_items`, defer `matches`/`has_field`;
(3) **live preview** deferred.

**Load-bearing finding:** the runtime already does both halves of the loop —
`integration/context.py` (~L187) injects the output spec into the *producing*
node's context, and `WF-OUT-*` already runs `check_artifact` on exit. So v1 is
authoring UI + thin index + an id-resolution seam — **no gatekeeper/context
change**. This shrank the scope materially.

**v1 acceptance:** *can the user author an artifact and connect it to a node.*
Spec authored → `issues/DRAFT-artifact-authoring.md`; DAG-placed (INDEPENDENT,
ready-now, builds on merged #28 + artifact-spec engine). Awaiting user approval
to open the GitHub issue → dispatch one Worker (mirrors the #28 flow). No product
code, no issue filed, no dispatch yet.

---

## 2026-07-03 — Workspace restructure

Architect artifacts consolidated under `agents/architect/`:

- `architecture.md`, `architecture-coordinator.md` moved in from repo root.
- `prd-coordinator.md` moved to `prds/`.
- `structural.md` moved to `rules/`.
- `issue-dag.md` moved in from `agents/`.
- Added `briefs/`, `discussion/`, `plans/`, `research/`, and
  `issues/completed/`, `handoffs/completed/`.

---

## 2026-07-03 — Wave 1 landed to main; DAG + S-001 wording updated

- Fast-forwarded local `main` to `integration/wave1-014-015-016-017-018`
  (`7d2b8d6`) — #14-18 (glossary, ArtifactSpec checker, marker parser, node
  model, provider registry), already verified 180 tests + frontend green in
  T-008. No re-merge needed; identical tree.
- Closed GitHub issues #14-18 with the merge commit referenced.
- `issue-dag.md` rewritten: #10-18 marked done; #19-25 (governance-engine-revised
  wave 2) added with real `## Blocked by` edges pulled live from GitHub. Open
  wave now is `#19` + `#20` (parallel); `#25` flagged held-for-human (no
  ready-for-agent/AFK label).
- `architect.md` responsibility #2 (Issue specs) rewritten per T-002's
  resolution: the GitHub issue is the spec of record (its body sections are
  the `issues/{id}.md` equivalent); local spec files are now supplementary,
  not required, closing the S-001 process tension T-001 flagged.

---

## 2026-07-04 — Restored after being dropped uncommitted

This entire subtree (this file included) existed only as **uncommitted**
changes on `chore/agents-workspace-restructure` — staged/modified but never
committed — while that branch itself sat 5 waves behind `main`. The
Orchestrator stashed it, later judged the stash "not required" without
separating novel content from stale renames, and dropped it. It was recovered
from the not-yet-garbage-collected stash commit
(`652c80b87c7094d8c0b40c97f7a9315d2f11c45a`) and committed properly this time.
See `agents/orchestrator/spawn-environment.md` and the Orchestrator's
postmortem for the full account.

---

## 2026-07-04 — Doc drift reconciled: S-001..S-006 → governance model

QA's full-surface survey flagged design/README docs still describing the removed
hardcoded `S-001..S-006` structural rule library and a stale test count.
Reconciled against the code (`hephaestus/rules/{base,registry,governance,__init__}.py`,
`index.py`, `dashboard.py`) and `docs/design/governance-engine.md`. Confirmed there is
no `hephaestus/rules/structural.py` and no `S-0xx` IDs remain in product code (the only
`S-00` hit under `hephaestus/` is registry.py's docstring recording the removal). Real
suite size observed: **211 passed** (shared `agents/.venv`).

- **`README.md`** — rewrote the intro to point at `docs/design/governance-engine.md` as
  canonical; fixed the `rules/` tree (`base.py` interface, `governance.py`
  G-001/G-002/G-003 + `ALL_GOVERNANCE_RULES`, `registry.py` generic runner with no
  built-in set); dropped the hardcoded `# 27 tests` count; replaced the
  `Structural rules S-001..S-006 ✅` Status row with the governance model.
- **`structural.md`** — rewrote from the S-001..S-006 rule-library doc into the current
  governance model: `HephaestusRule` interface (now `EvaluationContext`), the generic
  `registry` runner, the three run-time governance rules, and user-authored artifact-spec
  predicates; kept a compact honest **History** section recording the removed six rules.
- **`architecture.md`** — added a "partly superseded" banner (points to governance-engine,
  flags the removed S-rules and the superseded §6.2 posture); rewrote §4's built-in rule
  table/interface to the governance rules; fixed §3.3 link, §6.3 Tier-2 wording, and §7
  Phase-1 scope; bumped frontmatter to v0.2.2 / 2026-07-04.

Product code untouched (docs only). Out-of-scope residual S-rule references remain in the
role docs (`agents/architect/architect.md` + `index.md`, `agents/worker/`, `agents/qa/`)
and other spec docs (`architecture-coordinator.md`, `prd-coordinator.md`, `log.md`) — noted
to the Orchestrator for a follow-up pass.

---

## 2026-07-04 — Follow-up pass: S-rules reconciled across role + coordinator docs

Continued the reconciliation above into the role docs and coordinator specs the
first pass flagged as out of scope. Verified each reference against code
(`hephaestus/rules/{base,registry,governance}.py`, `hephaestus/okf_layout.py`,
`hephaestus/handoff.py`) and `docs/design/governance-engine.md` before rewriting —
no blind deletes.

**Ground truth confirmed:**
- `reviewed_by: architect` is **not code-enforced** — grep found no `reviewed_by`
  in any `.py`. It (was `S-005`) is now a **process convention**.
- The OKF *paths* (`issue_path` / `issues_index_path` / `handoff_path` /
  `qa_evidence_path` / `log_entry_path`) are **still code-enforced** by
  `okf_layout.py`; only the `S-0xx` rule IDs that checked their presence/content
  are gone. Rewrote every path reference to say that accurately.
- Live rules are `G-001`/`G-002`/`G-003` (`governance.py`), run by the generic
  `registry.py` (no built-in set).

**Files reconciled:**
- `agents/architect/architect.md` — resp. #2 (S-001 → convention), #4 (S-005 gate
  → convention; handoff path still code-enforced), #6 (rules → governance model +
  G-rules), References + `updated`.
- `agents/architect/index.md` — `rules/` row + "Code-enforced paths" (paths via
  `okf_layout.py`, S-00x checks removed).
- `agents/worker/claude.md`, `agents/worker/index.md` — S-001 spec-of-record and
  S-002 handoff → conventions; handoff path still code-enforced.
- `agents/qa/claude.md`, `agents/qa/index.md` — S-005 review gate + S-003/S-004
  evidence/log → conventions; evidence path still code-enforced via
  `qa_evidence_path`.
- `architecture-coordinator.md` — §5 module map: `structural.py`/`S-001..S-006`
  line struck through + superseded note; `governance.py` set = G-001..G-003.
- `prd-coordinator.md` — §"Per-profile exit rules": removed the false
  "structural rules unchanged and continue to run" claim + added a superseded
  note; corrections-example `violation` changed from the dead `S-002` to a live
  `G-001`.
- `log.md` (repo root) — historical entries left intact (accurate point-in-time
  history); added a 2026-06-23 removal entry so the log reflects the current
  governance model; bumped `updated`.

`agents/qa/readme.md` left unchanged — its `reviewed_by: architect` mention is an
accurate flow step, not a rule claim.

**Left for the Orchestrator (explicitly out of scope this pass):** stale S-rule
references in `agents/qa/test-plan.md` (line 143 "rule S-003 consumer", line 373
"QA rule S-005"), `agents/orchestrator/tasks/*`, `sample/agents/`, and the
`governance-engine-revised.md` duplicate.

Documentation only — no `.py` touched.

---

## 2026-07-05 — ADR-0001 reconciled (→ADR-0003) + node-authoring spec drafted

Two Architect tasks routed by the Orchestrator (2026-07-05 vision-vs-code
verification). Docs + spec only; no `.py`/frontend edits, no commits, no GitHub
issue created.

**Task 1 — ADR-0001 reconciled to the shipped gatekeeper runtime.** Grounded in
`hephaestus/workflow_runtime.py` (`WorkflowRuntime.run` is a real gatekeeper
engine: topo-walk from start placements, entry gate `WF-ENTRY-001`, exit gates
`WF-OUT-*`/`WF-SKILL-*` via `evaluate_spawn_gate`, HITL/AFK, ask/allow confirm,
override, live `on_update` state) and `hephaestus/workflows.py` (uniform `Node` +
`Placement` + `Edge` + `Guard` + `NodeInteractivity` + `AdvanceMode`; guarded
cycles allowed). ADR-0001 was still "Proposed" and decided the graph is "a
planning surface, NOT a runtime engine," rejecting "make the graph the runtime
engine" — a direct contradiction with the shipped code.
- **Form chosen: supersede, not rewrite.** Wrote
  `docs/adr/0003-node-graph-is-an-executable-gatekeeper-runtime.md` (Accepted)
  recording the reversal, the reasoning (the runtime *is* the compliance layer),
  and a full vocabulary-reconciliation table mapping ADR-0001's seven typed nodes
  (`Start/Agent/Condition/Handoff/QA/Notify/End`) onto the structural model
  (Start=no in-edge, End=no out-edge, Agent=the uniform Node, Condition=guarded
  Edge, Handoff=Edge+HandoffMarker, QA=exit gate, Notify=runtime notifications) +
  the two runtime dimensions ADR-0001 omitted (AFK/HITL, ask/allow). Chose
  supersede over in-place rewrite to keep honest history (ADRs are append-only;
  matches ADR-0002's precedent). Added a superseded banner atop ADR-0001, body
  retained verbatim.

**Task 2 — node-authoring spec drafted (spec only, not implemented).** Verified:
`store/nodes.py::create_node` + `store/db.py` already carry the full contract
(inputs/outputs/skills/skill_obligations/allowed_paths/allowed_tools/context_policy),
but `store/nodes.py` has **no `update_node`** (edit path needs a new DAL fn);
`Bridge.create_node` (~L130) and `api.js::createNode` (~L117) both cap at 7 stub
fields; `WorkflowCanvas.jsx` only places existing nodes (no authoring form).
- Wrote `agents/architect/issues/DRAFT-node-authoring.md` (marked DRAFT — pending
  user approval to open on GitHub) with `## What to build` / `## Acceptance
  criteria` / `## Blocked by`. Scope: add `update_node` DAL fn; widen
  `Bridge.create_node` + add `Bridge.update_node`; widen/extend `api.js`; add a
  create/**edit** UI form for the six list-typed guardrail fields.
- **`context_policy` recommendation: hold the active control, plumb the field
  inert.** It has no runtime consumer (compression deferred behind the Headroom
  seam) and — critically — its value vocabulary is undefined until that adapter
  defines it. So plumb it through the bridge/api (data plane symmetric, no later
  migration) but render the UI control disabled/read-only with a "reserved — no
  runtime effect until compression lands" label, to avoid authoring
  un-interpretable values ahead of the consumer.
- **DAG:** added an "ADR-0003 + node-authoring" section to `agents/issue-dag.md`;
  marked ADR-0001 superseded, ADR-0003 accepted, and the node-authoring spec as
  **INDEPENDENT / ready now** — explicitly not blocked by dynamic fan-out or
  compression; builds only on merged #18/#20/#23/#25. One dedicated owner when filed.

**Open questions / follow-ups for the Orchestrator/user:**
- Approve opening `DRAFT-node-authoring.md` as a GitHub issue (gated on user
  confirmation) — then it is immediately dispatchable to a Worker.
- The node-authoring issue necessarily touches `store/nodes.py` (new `update_node`)
  — the "one owner may only edit files for that issue" rule applies; no shared-file
  contention expected since no open issue touches nodes.py.

---

## 2026-07-04 — Link-fix pass: structural.md references repointed to repo root

`structural.md` was rewritten into the governance model and lives only at the repo
root; several docs still linked to it via non-existent paths (`rules/structural.md`,
`../architect/rules/structural.md`, `spec/rules/structural.md`). Repointed each
broken link at the real file and verified resolution:

- `agents/architect/architect.md` — resp. #6 inline `rules/structural.md` →
  `../../structural.md`; References bullet `[rules/structural.md](rules/structural.md)`
  → `[structural.md](../../structural.md)`.
- `agents/qa/claude.md` — References `[../architect/rules/structural.md](...)` →
  `[structural.md](../../structural.md)`.
- `index.md` (repo root) — Related Documents `[spec/rules/structural.md](../spec/rules/structural.md)`
  → `[structural.md](structural.md)`; description reworded from "built-in compliance
  rules" to the governance model (user-authored artifact-spec predicates + run-time
  governance G-rules; hardcoded S-001..S-006 removed 2026-06-23).

Left untouched: `log.md` (repo root) line ~31 `spec/rules/structural.md` — inside a
dated historical entry, accurate as point-in-time history. Remaining
`rules/structural.md`/`spec/rules/structural.md` strings now live only in dated
history. Documentation only — no `.py` touched.

---

## 2026-07-07 — Handoff review: #28 node authoring (APPROVE → QA)

Reviewed the Codex Worker's handoff for issue **#28** ("full Node contract
authorable + editable from the UI"), commit `4e76fc7` on
`feat/028-node-authoring`. **Verdict: APPROVE, ready for QA.** Full per-criterion
findings recorded in `handoffs/028.md` under `## Architect review`.

Walked all acceptance criteria against the diff:
- **DAL `update_node`** (`store/nodes.py`) — updates all mutable fields,
  preserves `node_id`/`created_at`, returns the `Node`, syncs the identity card
  via a new shared `_write_identity_card` helper (same capability derivation as
  create). Existing DAL functions unaffected.
- **Bridge** (`desktop.py`) — `create_node` forwards the 7 previously-dropped
  fields and returns the full payload via `_node_payload`; `update_node` added
  and round-trips (unit test present).
- **api.js** — `createNode` widened, `updateNode` added, both behind the
  bridge-presence guard.
- **UI** — old inline form extracted into shared `NodeForm.jsx` (list editors for
  the six list fields) and wired into both the coordinator roster and canvas
  palette; edit pre-fills; list refreshes after save.
- **`context_policy`** — plumbed but rendered `disabled/readOnly` with the
  reserved label; no free-form value accepted.
- **Key risk — Coordinator refactor** — verified NOT dropped behavior: roster
  list, `removeNode`/Delete (`:384`/`:541`), `loadNodes` (`:219`), model+effort
  selection, rule toggle, and directory browse all survived, relocated into
  `NodeForm`. New Edit button added.
- **Regressions** — test changes additive only; state.db still DAL-only; product
  code untouched outside the four intended surfaces.

One non-blocking latent note: `update_node` rewrites the identity card with
`sessions=[]` (mirrors create); harmless today since `append_session` has no live
producer. Out-of-scope untracked `sample/agents/identities/` left for the
Orchestrator (Worker sandbox blocked removal; not staged in `4e76fc7`).

## 2026-07-07 — Handoff review: #30 Coordinator rehome (APPROVE)

- Reviewed Codex Worker's commit `9575b14` on `feat/030-coordinator-rehome`
  (retire `Coordinator.jsx`; rehome into `Library.jsx` + `Console.jsx`).
- Verdict **APPROVE — ready to merge**. Read both new files in full and
  cross-checked every capability cluster of the deleted 1111-line Coordinator:
  all present (per-capability checklist in `handoffs/030.md`). No drops.
- Confirmed no scope creep: `NodeForm`/`ArtifactForm` reused (not duplicated),
  `ArtifactBindingEditor` reached transitively via `NodeForm`; `api.js` and
  `NodeForm.jsx` edits are cosmetic-only (comment text + one copy string), the
  #349733c `RULE_LABELS` work intact; `mock.js` `COORDINATOR_MOCK` split into
  `NODES_MOCK`/`ARTIFACTS_MOCK` consistent with Library; product diff entirely
  under `frontend/src/**` — nothing in `hephaestus/**` or tests.
- Set `reviewed_by: architect` on `handoffs/030.md`. Did not run the build
  (Orchestrator already confirmed green, 53 modules).
