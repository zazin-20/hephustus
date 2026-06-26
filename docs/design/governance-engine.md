# Hephaestus as a User-Authored Workflow Governance Engine

**Status:** Design (captured from a grilling session, 2026-06-23)
**Supersedes (in part):** `architecture.md` §6.2 ("does not gate writes / detect-and-flag, not prevent") and the "Hephaestus is NOT the orchestrator" framing — for the *workflow path*. Those decisions should be re-recorded as ADRs (see "Decisions to formalize").

---

## 1. Thesis

LLM providers (Claude, Codex, …) are **engines** — interchangeable, stateless executors that take a fully-assembled prompt and produce output. **All** compliance, governance, context control, and alignment live in **Hephaestus**.

Hephaestus is not a fixed compliance system with a built-in pipeline. It is a **user-authored workflow governance engine**: the user authors the nodes, the artifact structures, the rules, the scopes, and wires them into a graph. Hephaestus's job is to **ensure work happens strictly per the workflow the user drew** — gating the transitions between nodes.

The architect → general → worker → verifier loop is **one workflow a user can draw**, not something baked into the code.

## 2. Core concepts (glossary)

- **Engine** — a provider+model behind one runner interface (Claude/Codex). Stateless from Hephaestus's view; holds no cross-node memory.
- **Node** — the core unit: *an engine + governance attached to it*. A node declares its engine (provider/model/effort), its **required input artifact(s)**, its **required output artifact(s)**, its **capabilities/scope** (allowed tools/paths), its **constraints** (rules), and its **context policy**. (Today's `Profile` is the skeletal static form of a node.)
- **Artifact** — a produced document (PRD, ADR, issue spec, handoff, …). Artifacts are the *only* thing that crosses an edge.
- **Artifact-spec** — a user-authored markdown doc that defines an artifact type. It does **double duty**: (1) Hephaestus's deterministic gate checklist, and (2) the *directives* injected into the agent that generates the artifact.
- **Edge** — an allowed transition between nodes. Carries an artifact, never a transcript.
- **Gate** — the check Hephaestus runs at a node boundary. **Entry gate:** required inputs present + context scoped correctly (enforced *by construction*). **Exit gate:** required outputs produced and predicate-valid.
- **Constitutional Directives** — directives always present in a node's context, **layered**: `global → machine/environment → workflow → role → node`.
- **Distillation** — turning a successful trace into a frozen rule (the alignment/learning loop).
- **Frozen rule** — a learned directive (or constraint) injected into the constitution at a chosen scope.

## 3. Resolved decisions

### 3.1 Posture: gatekeeper of transitions (choice A)
Hephaestus **blocks advancing to the next node until the gate passes**. It orchestrates *the graph*, not *the work* — the engine still does the work inside a node. This consciously supersedes the old "never prevent / not the orchestrator" posture for the workflow path. Human override on a blocked gate is available (policy per gate).

### 3.2 Everything is user-authored (declarative-first hybrid)
- Nodes, artifact specs, edges, scopes, and the *checkable* constraints are **authored as data** and interpreted by a generic engine.
- The current hardcoded `S-001..S-006` structural rules and the issue→handoff→qa→log Pydantic models are **not the engine** — they are at most one *example template*. They are being removed from code to avoid confusion (see §6).
- Behavioral/quality judgment (LLM-judge) is deferred — not needed when the generator is given good directives.
- Hand-written code rules remain only as a power-user escape hatch.

### 3.3 Artifact gates: one spec doc, two consumers
The artifact-spec MD lists the artifact's description, its **mandatory fields as predicates** (`has_title()`, `has_problem_statement()`, `has_user_stories()`, …, `has_release_criteria()`), and free-text **"good looks like"** exemplars.
- **Hephaestus** runs the predicates as the exit gate (deterministic).
- **The generating agent** receives the whole spec (template + exemplars) as input directives.

**Layout:** frontmatter for short scalars (`title`, `status`, `owner`); named markdown `## Sections` for prose/lists. `has_X()` resolves to "this frontmatter key is set" or "this section exists and is non-empty."

**Predicate library (shipped, user-composed — no user-written code):** `has_field`, `has_section`, `non_empty`, `min_items(n)`, `matches(regex)`. `has_X()` means **present *and* non-trivial** (closes the `## User Stories\nTBD` loophole).

**Verification strength:** presence + non-trivial by default; LLM-judge opt-in per node, later. Principle: *any format we can force the LLM to emit and deterministically check.*

### 3.4 Context: client-owned, clean-slate per node (choice A)
- **Hephaestus owns every token and replays.** The provider holds **no** cross-call memory. (No native `resume` across node boundaries.)
- A node's context is assembled fresh each invocation from exactly: **layered Constitutional Directives + declared input artifacts + the node's artifact-spec + the task**. Nothing else.
- **Edges carry only artifacts**, never transcripts. The worker gets the *issue spec doc*, not the architect's grill-me transcript. The PM's user-flow discussion never reaches the worker because the worker's node never declared it as an input.
- A node may be **multi-turn internally** (e.g. the architect's grill-me loop); that transcript is private to the node and dies at the edge.
- Rationale: this is the only model where Hephaestus — not the provider — controls context, which was the founding requirement, and it makes clean-slate the default.

### 3.5 Constitutional Directives are layered
`global → machine/environment → workflow → role → node`. A node's effective constitution is the concatenation of all layers in scope. Frozen rules inject at the layer matching their scope (§3.7).

### 3.6 Pruning → compression behind a seam (Headroom)
- **Inter-node noise** is eliminated *structurally* by node scopes — nothing irrelevant is ever admitted.
- **Intra-node noise** (one node's loop bloating with tool outputs / back-and-forth) is handled by **content-aware compression behind a seam** — Headroom (`headroomlabs-ai/headroom`) is the candidate adapter (compresses tool outputs/logs/history; reversible via CCR; CacheAligner offsets choice-A replay cost). Manual per-turn pruning and hand-rolled keep-last-K are **dropped**.
- **Carve-outs (governance-owned, never compressed):** the Constitutional Directives and artifact-specs are **pinned** out of compression — they must reach the engine verbatim.
- Headroom is **not** a governance solution — only the intra-node context-management adapter. It is swappable behind the seam.

### 3.7 Distillation → rules (the alignment/learning loop)
Freeze what worked into something that shapes future runs (e.g. a worker discovers the one `gh` command that connects on this machine after several fail).

- **Trigger:** the agent emits a structured **"this worked" marker** (same pattern as the existing handoff marker) → Hephaestus captures it from the trace as a **candidate** → routed into the **Correction Box** → **human-confirmed** before it is active. (Trace-heuristic and LLM-judge proposers can be added later behind the same candidate seam. Auto-active is a later per-rule opt-in.)
- **Scope:** chosen at promotion time from the ladder `global → machine/environment → workflow → role → node`, with a smart default by rule kind (an environment/command discovery → **machine**; a behavioral correction → **role/instance**). Injection mechanism = the layered constitution. *(The `gh` example is machine-scoped — the auto-grown version of `agents/worker-brief-template.md`.)*
- **Shape:** **directive by default** (injected into the constitution at scope; soft). `promote_to_rule` (a hard, **trace-checked** constraint, à la `G-001`/`G-002`) is reserved for the minority of learnings expressible as a deterministic check. Both are already the Correction Box's two promotion targets (`promoted_to_directive` / `promoted_to_rule`).
- **Lifecycle:**
  - *Staleness* self-heals via re-learning — when a frozen approach later fails, the agent finds a new one and emits a new candidate that **supersedes** the stale rule at promotion. No timers, no active staleness detector.
  - *Conflicts/dedup:* every frozen rule carries a **`(topic-key, scope)`**; a new candidate with the same key+scope **supersedes** (not stacks). No semantic conflict engine.
  - *Provenance (mandatory):* every frozen rule links to its **source trace(s)**, origin run/agent, confirmer, and timestamps — so "why is this directive in my agent's context?" is always answerable.
  - *Revocation:* **soft-disable** (kept for audit); superseded rules point to their replacement (a supersede chain = versioning).
- **Reuse:** the distillation pipeline **is** the Correction Box, extended to accept trace-sourced candidates alongside human notes.

## 4. Worked example — the architect → worker loop as *one authored workflow*

1. **Architect node** — engine: Claude/opus; input: a PRD artifact; obligation: produce an ADR; directive: run `grill-me` with the user first; context: PRD + Constitutional Directives only. Hephaestus's gates: PRD present (entry), ADR present + predicate-valid (exit).
2. **Planner node** — input: the ADR; obligation: GitHub issues via `to-issues`. Hephaestus checks issues produced.
3. **Worker node(s)** — engine: Codex/gpt-5.4-high; input: an issue spec **only** (clean slate); obligation: produce a handoff. Hephaestus ensures clean-slate context *by construction* and gates on the handoff's presence.
4. **Verifier node** — input: the handoff; verifies.

Every node boundary is a gate; the user gets **node-level visual feedback** (PRD ✓, ADR ✓, issues ✓, handoff ✓, verified). None of this loop is hardcoded — it is the shape of one authored graph.

## 5. Distance from the current code

- **Have the primitives (~35%):** runners-as-engines + provider-aware routing; trace capture (tool calls w/ command+output) + thinking capture; rule engine + `EvaluationContext`; `Profile` (node skeleton); handoff parsing + gated-spawn (`SpawnCard` GREEN/AMBER); Correction Box; dashboard; the `included`/`compile_context` context substrate.
- **Don't have the governed behavior (~10%):** user-authored workflows/specs; the artifact predicate engine; clean-slate replay (today the code does the *opposite* — it accumulates included turns); the layered constitution; the gatekeeper transition model; the Headroom seam; the distillation loop.

## 6. Removal: the hardcoded issue-lifecycle — DONE (2026-06-23)

The hardcoded issue-lifecycle was **stripped, not gutted** — a reuse audit found the
"compliance app" was mostly reusable engine + surfaces with hardcoded *content*
bolted on. Only three things were disposable.

**Stripped:**
- `rules/structural.py` (the `S-001..S-006` classes) — deleted.
- the issue-lifecycle Pydantic doc classes in `models.py` (`IssueSpec/Handoff/QAEvidence/LogEntry/IssuesIndex`) — deleted; the generic `OKFModel` base kept.
- the issue-lifecycle derivation in `index.py` (typed collections) and `dashboard.py` (`build_dashboard`/`_pipeline_state`).

**Kept + marked `REUSABLE` (in each module's docstring):**
- `core.py` (gate-result vocabulary), `rules/base.py` (check interface), `rules/registry.py` (generic gate-runner — default rule set is now empty), `eval_context.py`, `frontmatter.py`, `monitor.py` (rescan+diff), `watch.py` (change→re-evaluate), `handoff.py` (transition gate), `okf_layout.py` (tree shape).
- `index.py` → generic artifact-store reader (`OKFContext` = parsed documents + schema load errors).
- `dashboard.py` → generic `snapshot` (rows empty until a workflow/node model feeds it; violations still flow).
- frontend `Dashboard.jsx` / `Violations.jsx` — the node-status surface, repurposable.
- `G-001`/`G-002` governance — kept (not issue-lifecycle-specific).

**Result:** 166 tests green; frontend builds. The Dashboard renders empty (awaiting the user-authored workflow model) but all machinery is intact. The coupled tests were rewritten to exercise the *generic* engine (sample rules + Tier-1 schema load errors) instead of `S-001..6`.

## 7. Resolved architecture (grilled 2026-06-23)

The five branches above are now decided. This section is the authoritative model.

### 7.1 Ontology — model state by *scope*, not by a heavyweight instance

**Authored (OKF tree, reusable, user-writes):**
- **ArtifactSpec** — a document contract (frontmatter scalars + named sections + a composed predicate list + "good looks like" exemplars). Referenced by nodes as inputs/outputs.
- **Engine** — `{provider, model, effort}`, referenced from the catalog. Separated so it's swappable/A-B-able under a node.
- **Node** — the unit you *run*: an executor + governance (`inputs: [ArtifactSpec]`, `outputs: [ArtifactSpec]`, scope = allowed paths/tools, required `skills`, attached rules, context policy, `tags`). Reusable. **Runs standalone** (ad-hoc) *or* placed in a graph.
- **Workflow** — a graph of **placements** (a Node at a position) + **edges** (output→input routing) + per-edge guards.
- **Constitution (authored layers)** — directive text per scope.

**State (scope-addressed, no owning object):**
- The "instance" is an **address**, not an entity. `Profile` and `AgentTask` **dissolve**: Profile's config → `Node`; its identity/threads/learned-rules → scope-addressed state.
- **`role` is removed entirely** (routing is model-provider-based; context comes from node I/O specs). Replaced by free-form **`tags`** (many-to-many grouping; a rule can be scoped to a tag).

**Runtime (SQLite, derived per execution):**
- **Run** — one node execution: the resolved, immutable **`ExecutionContract`** (engine, scope, allowed paths, resolved context, actual input artifacts, `actual_model`) + trace + produced artifacts + gate verdicts + status. Derived, never authored.

### 7.2 Executor model + UI discriminator
A node carries `executor: {kind, …}`:
- `kind: "engine"` → `{provider, model, effort}` → rendered as a **provider-colored box** with the model label.
- `kind: "builtin"` → `{name}` (e.g. `condition`, `notify`) → rendered as a **distinct neutral glyph** (diamond / bell).
- **Start/End** are graph topology; **branch conditions** render as **edge labels**. One data model; the `executor` field drives both execution *and* canvas rendering.

### 7.3 Gates + edges
- **Gates are derived from the node's declared I/O specs** (never authored separately): **exit gate** = the output ArtifactSpec predicates (+ enforced skill obligations); **entry gate** = required input artifacts present + valid, context scoped by construction. Inputs are **AND-required** (optionality via an `optional` marker).
- **Edges = routing only**, plus an optional **guard** (a deterministic predicate / `condition` builtin) for branching.

### 7.4 Gate mechanics (choice A)
- **A failed gate always blocks**, with a human-override affordance — non-negotiable.
- **On a green gate**, advance is a per-edge **allow-advance / ask-before-advance** switch (ask → the `SpawnCard`).
- **Node interactivity** is a separate per-node **HITL / AFK** flag (HITL pauses for human turns *inside* the run, e.g. grill-me; default AFK).

### 7.5 Skills — Hephaestus-owned, cross-provider
- A **skill** = a Hephaestus-owned, versioned **playbook** (markdown), injected into a requiring node's **context** regardless of provider. Engines are dumb; they just follow the injected instructions. Tools the skill needs come from the node's **scope**, not the skill.
- **Enforcement = the marker protocol** (7.6): directive-by-default; a skill obligation can be marked *enforced* → an exit-gate that checks the trace for the skill's completion marker. Cross-provider (text marker), so no dependency on Claude's native skill system (deferred as an optimization).

### 7.6 The marker protocol (agent → Hephaestus signals)
One unified, reserved **line-sentinel + strict JSON + `type`** format for every signal (handoff / skill_complete / distillation_candidate / …):
```
@@HEPHAESTUS@@ {"v":1,"type":"skill_complete","skill":"grill-me","ok":true}
```
Deterministic rules: **line-anchored** (sentinel begins the trimmed line); **reserved token**; **strict JSON, schema-validated per `type`** (malformed ⇒ not a marker); **first valid wins**; **ignore `thinking`** turns (scan assistant text + tool-call commands only); tied to the run/trace for provenance. The injected skill playbook instructs the agent to emit its marker.

### 7.7 Addressing (the scope ladder)
`global → machine → workflow → tag → node(instance)`. A run collects every directive/frozen-rule row whose `(scope, key)` matches its address chain, layered **narrowest-wins**:

| scope | key |
|---|---|
| global | — |
| machine | the workspace |
| workflow | `workflow-id` |
| tag | each tag on the node |
| node (instance) | `(workflow-id, placement-id)` — or `node-id` standalone |

**Learn persists, conversation resets:** frozen rules are keyed at `(workflow, placement)` (persist across runs); threads/loop-history at `(workflow-run, placement)` (per-run, clean-slate).

### 7.8 Storage
- **OKF tree (markdown, git-diffable):** ArtifactSpecs, Skills, Nodes (YAML frontmatter), Constitution layers, **frozen rules** (markdown in the constitution at their scope, with provenance — durable learned knowledge, not telemetry).
- **OKF tree (structured graph):** Workflows as a **YAML/JSON** file the node-graph editor round-trips (a DSL *behind* the visual editor).
- **SQLite (`.hephaestus/state.db`):** Runs, `ExecutionContract`s, traces, threads/turns.
- All paths go through the `okf_layout` seam.

### 7.9 Visual feedback
- **Primary monitor = the graph canvas itself**, with an **author ↔ run mode toggle**: nodes show executor-kind shape/color (7.2) + a run-state badge; edges show active / blocked / awaiting-confirm. ("PRD ✓ → ADR ✓ → …" reads off the graph.)
- **Node run-state machine:** `NOT_STARTED → RUNNING → WAITING_HUMAN (HITL) → BLOCKED (gate failed) | AWAITING_CONFIRM (green+ask) → DONE`.
- **Node drill-in:** gate checklist (predicate pass/fail + skill markers), produced artifact, conversation + trace.
- **State source:** the repurposed `snapshot`/`monitor` (issue→node, stage→gate, violation→gate-failure), pushed live via `evaluate_js`. Secondary: the tabular `Dashboard` as a runs/nodes list. Plus human-attention notifications (HITL needs input / node done+green). Detailed component states deferred.

## 8. Decisions to formalize as ADRs

- The **posture flip** (choice A — gatekeeper of transitions) supersedes `architecture.md` §6.2.
- **User-authored governance** (declarative-first hybrid) — rules/specs as data, engine as interpreter.
- **Client-owned clean-slate context** (choice A) and the **layered constitution**.
- **Distillation → rules** via the Correction Box.
