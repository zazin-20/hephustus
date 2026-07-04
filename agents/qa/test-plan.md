---
title: Hephaestus — QA Test-Case Catalog
role: qa
owner: qa
updated: 2026-07-04
status: active
kind: test-plan
---

# Hephaestus — QA Test-Case Catalog

A full-surface mapping pass of the product as it exists today, plus a durable,
referenceable catalog of concrete test cases. Authored as a pre-feature baseline
under explicit Orchestrator authorization (not a per-issue S-005 gate).

## Why this format

A **single Markdown file with one table per surface area** is the right fit here:

- **Referenceable.** Every case has a stable ID (`TC-<AREA>-<NNN>`). Handoffs,
  bug reports, and `evidence/{issue_id}.md` can cite an exact case without a
  database or external tracker.
- **Diff-friendly + in-repo.** It lives in the OKF tree beside the code it
  covers, versions with git, and reviews as a normal PR. No tooling to stand up.
- **Grep-able and AI-navigable.** One file, `file:line` anchors to real
  behavior, and a fixed column shape the pipeline roles already read.
- **Status-bearing.** The `Status` column doubles as a coverage ledger
  (`covered` / `gap` / `partial`), so the catalog is also the gap map.

When the catalog outgrows one file (hundreds of cases, or per-release
snapshots), split into `test-cases/<area>.md` keeping the same ID scheme and an
`index.md` roll-up. Not needed at today's scale.

## ID scheme

`TC-<AREA>-<NNN>` — area code + zero-padded sequence. Areas:

| Code | Surface |
|---|---|
| `WS` | Workspace bootstrap / OKF scaffold / service-root discovery |
| `OKF` | OKF layout, frontmatter parsing, index/context build, schema errors |
| `RULE` | Governance rules (G-001/2/3), artifact predicates, exit/entry gates |
| `PROV` | Provider registry, routing, model ownership, catalog, identity cards |
| `CTX` | Session-context assembly, constitution/frozen-rule injection, contract resolution |
| `RUN` | Agent service run lifecycle, persistence, governance evaluation |
| `WF` | Workflow model (validation), gatekeeper runtime, HITL/ASK/override |
| `STORE` | SQLite DAL: nodes, threads/turns, runs, trace, violations, frozen rules, corrections |
| `MARK` | Marker protocol: handoff / skill_complete / distillation-candidate parsing |
| `CODE` | Read-only multi-repo code viewer |
| `DESK` | PyWebView desktop bridge (`js_api`) |
| `UI` | Frontend flows: Coordinator, Workflow Canvas, Run Agent, Code, Toasts |
| `SEC` | Security: path-escape, sandbox/permission escalation, scope adherence |

## Legend

- **Type** — `unit` | `integration` | `e2e` | `security` | `manual`
- **Status** — `covered` (a passing test in root `tests/` already exercises this),
  `partial` (touched but the QA-relevant assertion is not made), `gap` (no
  automated coverage anywhere today). QA-owned homes
  (`agents/qa/tests/{security,integration,e2e}/`, `agents/qa/playwright/`) are
  **empty** — every `integration`/`e2e`/`security`/`manual` row below is a `gap`
  until QA authors it, even where a root unit test touches the same code.

---

# Deliverable 1 — Testable surface

## Interaction flows (end-to-end journeys)

| # | Flow | Where it lives | Observable behavior / acceptance surface |
|---|---|---|---|
| F-1 | **Open / scaffold a workspace** | `workspace.py:24 scaffold_okf`, `:78 Workspace.open` | First boot creates the OKF tree (`required_directories()`), writes an `issues/index.md`, appends `.hephaestus/` to `.gitignore`, and opens the SQLite state DB. Idempotent on second open. |
| F-2 | **Discover service repos** | `workspace.py:58 discover_service_roots` | Top-level dirs with a `.git/` become read roots; `agents/archive/node_modules` excluded; dedup preserves order. |
| F-3 | **Live compliance monitor** | `watch.py OKFWatcher`, `monitor.py ComplianceMonitor` | Editing any `*.md` under `agents/` debounces, rescans, and pushes an added/resolved violation delta to the UI. Baseline emitted on start. |
| F-4 | **Dashboard snapshot** | `dashboard.py:28 snapshot` | Single JSON envelope: rows (empty until workflow model feeds it), violations (currently Tier-1 schema load errors), workflow-canvas state, summary counts. |
| F-5 | **Ad-hoc agent run (Run Agent tab)** | `desktop.py start_agent`, `integration/service.py begin/run`, `runners.py` | Pick provider + tags + issue + cwd + prompt → routed to Claude/Codex/Echo, context files injected, events stream to UI, run lifecycle persisted, governance evaluated on completion. |
| F-6 | **Provider routing / identity resolution** | `providers.py resolve_provider`, `routing.py TAG_DIRECTIVE`, `contract_resolution.py` | Model ownership wins; else first non-empty fallback (task → node). Tags map to constitution directive files. One `resolve_provider()` seam (ADR-0002). |
| F-7 | **Node authoring (Coordinator tab)** | `desktop.Bridge.create_node/delete_node/list_nodes`, `store/nodes.py`, `Coordinator.jsx` | Create a node (provider/model/effort/tags/rules/dirs) → row persisted, identity card written; delete cascades threads/turns/runs/trace and removes the card. |
| F-8 | **Workflow authoring (Canvas tab)** | `workflows.py save/load/validate`, `WorkflowCanvas.jsx` | Drag placements, wire edges, set guards/advance/interactivity, save to YAML/JSON under `agents/workflows/`. Validation rejects dup ids, unknown edge endpoints, unguarded cycles. |
| F-9 | **Gatekeeper workflow execution** | `workflow_runtime.py WorkflowRuntime.run`, `desktop.start_workflow` | Node-by-node run: entry gate (inputs present) → run node → exit gate (artifact predicates + skill markers) → GREEN advances, AMBER blocks (override available), ASK awaits confirm, HITL awaits human input; live state pushed per step. |
| F-10 | **Handoff / gated Spawn** | `handoff.py parse_handoff/evaluate_spawn_gate`, `desktop.parse_handoff_marker/evaluate_spawn` | Agent emits a `@@HEPHAESTUS@@` handoff marker → parsed → exit rules evaluated → SpawnCard GREEN/AMBER prefills the next spawn. |
| F-11 | **Skill-obligation enforcement** | `governance.py G003`, `workflow_runtime._SkillExitRule`, `skills.py` | A node/contract with skill obligations fails its gate unless a `skill_complete` marker with `ok=true` is found in turns/trace. |
| F-12 | **Alignment / distillation loop** | `corrections.py capture_distillation_candidates/promote_correction`, `frozen_rules.py` | Distillation-candidate markers on a completed run become correction rows; promotion writes a scope-addressed frozen rule (narrowest-wins, supersede by `(topic-key, scope)`). |
| F-13 | **Frozen-rule / constitution injection** | `context.py _render_constitution`, `frozen_rules.list_frozen_rules_for_address` | On a run, directive frozen rows matching the scope address chain (`global→machine→workflow→tag→node`) are layered into the node's system prompt. |
| F-14 | **Context replay / pruning** | `context.py _render_replay`, `threads.compile_context/set_included` | Prior included turns replay into a node's context; a turn can be soft-excluded and re-included (reversible pruning). |
| F-15 | **Read-only code browse (Code tab)** | `codeview.py CodeViewer`, `CodeView.jsx` | List repos, walk a tree (ignoring vcs/build dirs), read a file with language tag; writes impossible; path traversal outside a root rejected; binary/oversize files flagged. |
| F-16 | **Model/effort catalog** | `catalog.py`, `providers.discover_*` | UI dropdowns fed from provider discovery (Claude aliases + `--effort` levels; Codex model cache) with fallbacks when CLIs absent. |
| F-17 | **Interrupted-run recovery** | `runs.interrupt_running_runs`, `service.AgentService.__init__` | On service construction, any run left `running` (crash/restart) is marked `interrupted`. |
| F-18 | **Corrections feedback queue (UI)** | `desktop.save_correction/get_corrections`, `Toast.jsx`, `Violations.jsx` | A violation toast can capture a human correction note tied to violation/node/issue; queue is listable. |
| F-19 | **Desktop shell lifecycle** | `desktop.py DesktopApp.run/_start_core` | Native window loads built frontend over `file://`; asyncio core + OKF watcher on a daemon thread; missing frontend/pywebview raise actionable errors. |
| F-20 | **CLI dry-run / live run** | `integration/service.py main`, `integration/__main__.py` | `python -m hephaestus.integration <provider> <prompt> --echo` prints routing + injected context without a live call; without `--echo` streams a live run. |

## Components (worth testing)

| Component | Where | Observable behavior |
|---|---|---|
| `OKFLayout` | `okf_layout.py` | Canonical path resolver; the single home for tree shape and the code-enforced `qa/evidence/{issue_id}.md` path. |
| `frontmatter` | `frontmatter.py` | Split YAML fence from body; no-fence = all-body; malformed/unterminated/non-mapping fence → `FrontmatterError`. |
| `OKFContext` / `build_context` | `index.py` | Scans `agents/**/*.md`, parses each, collects malformed frontmatter as `schema` load errors. |
| Governance rules | `rules/governance.py` | G-001 scope adherence (writes within `allowed_paths`), G-002 model compliance (actual vs contracted), G-003 skill obligation. |
| Rule runner | `rules/registry.py` | `run_rules` / `run_all` (adds Tier-1 load errors) / `run_layer` (filters by `.layer`); auto-wraps a bare `OKFContext`. |
| ArtifactSpec engine | `artifact_spec.py` | Loads a spec's `## Predicates`; supports `has_field/has_section/non_empty/min_items/matches/has_*`; deterministic pass/fail vs a target doc. |
| Provider registry | `integration/providers.py` | Register/resolve providers; `owns_model`, `provider_for_model`, effort→flag mapping, model discovery. |
| Session context builder | `integration/context.py` | Assembles constitution + skills + input artifacts + output specs + frozen rules + replay into `system_prompt`; surfaces missing files. |
| Contract resolver | `integration/contract_resolution.py` | Builds the immutable `ExecutionContract` (provider/model/effort/scope/allowed_paths/skill_obligations). |
| Runners | `integration/runners.py` | `EchoRunner` (deterministic), `ClaudeRunner` (SDK, guarded import), `CodexRunner` (subprocess JSONL); `build_codex_argv` pure. |
| Agent service | `integration/service.py` | begin → run → persist turns/trace → finish run → evaluate governance → raise on ERROR violations; per-node async lock. |
| Workflow model | `workflows.py` | Dataclasses + YAML/JSON round-trip + graph validation (unique ids, known endpoints, no unguarded cycles). |
| Workflow runtime | `workflow_runtime.py` | Gatekeeper executor: entry/exit gates, GREEN/AMBER/ASK/HITL/BLOCKED statuses, override, live `on_update`. |
| Marker/handoff | `handoff.py` | Line-anchored `@@HEPHAESTUS@@` + strict-JSON marker parsing; legacy `{"handoff":…}`; skill/distillation markers; spawn gate. |
| Store DAL | `store/*.py` | Typed SQLite CRUD for nodes/threads/turns/runs/trace/violations/frozen_rules/corrections + schema/`connect`. |
| Dashboard | `dashboard.py` | Snapshot envelope; per-placement gate checklist, artifact preview, edge-state derivation. |
| Compliance monitor/watcher | `monitor.py`, `watch.py` | Stateful rescan + added/resolved diff; watchdog debounce pipeline. |
| Code viewer | `codeview.py` | Root-constrained read-only browse. |
| Desktop bridge | `desktop.py Bridge` | ~25 `js_api` methods = the entire UI ↔ core contract. |
| Frontend | `frontend/src/**` | 4 tabs (Coordinator, Canvas, Code, Agent) + toasts; falls back to mock data with no bridge. |
| Catalog/skills/identity | `catalog.py`, `skills.py`, `identity.py` | Model catalog, skill-ref resolution, identity-card provenance. |

---

# Deliverable 2 — Test cases

> Root `tests/` (211 passing unit tests) already exercises much of the core;
> those rows are `covered`. The QA remit is the **`gap` rows** — integration,
> e2e, security, and manual/browser cases with no home yet.

## WS — Workspace & scaffold

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-WS-001 | First-boot scaffold creates OKF tree | empty temp dir | `Workspace.open(root)` | All `required_directories()` exist; `issues/index.md` written with today's date + `open_issues: []` | integration | covered |
| TC-WS-002 | `.hephaestus/` appended to `.gitignore` | dir with existing `.gitignore` | open workspace | marker line added once; existing content preserved | integration | covered |
| TC-WS-003 | Second open is idempotent | scaffolded dir | open again | no dir/file rewrites; `scaffold_okf` returns `False` | integration | covered |
| TC-WS-004 | State DB created and closable | fresh workspace | open | `.hephaestus/state.db` exists; schema present | integration | covered |
| TC-WS-005 | `agents`-named root not double-nested | root ending in `agents/` | `OKFLayout.for_workspace` | workspace_root = parent, no `agents/agents` | unit | covered |
| TC-WS-006 | Service-root discovery filters correctly | dirs with/without `.git`, plus `agents`,`archive` | `discover_service_roots` | only `.git` dirs, excludes reserved names, ordered | integration | covered |
| TC-WS-007 | Explicit service roots override discovery | workspace + explicit list | `Workspace.open(root, service_roots=[...])` | `code_roots` = root + given roots, deduped | integration | covered |

## OKF — Layout, frontmatter, index

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-OKF-001 | Evidence path is code-enforced location | any root | `OKFLayout.qa_evidence_path("issue-x")` | resolves `agents/qa/evidence/issue-x.md` (rule S-003 consumer) | unit | covered |
| TC-OKF-002 | Frontmatter split | doc with `---` fence | `frontmatter.parse` | `(frontmatter dict, body)` correct | unit | covered |
| TC-OKF-003 | No fence = all-body | prose file | parse | empty frontmatter, full body, no error | unit | covered |
| TC-OKF-004 | Unterminated fence errors | `---` with no closing fence | parse | `FrontmatterError("unterminated…")` | unit | covered |
| TC-OKF-005 | Non-mapping frontmatter errors | `---\n- a\n---` | parse | `FrontmatterError("must be a mapping")` | unit | covered |
| TC-OKF-006 | Malformed YAML surfaced as schema load error | broken `.md` under `agents/` | `build_context` then `run_all` | one `schema` ERROR violation citing the file | integration | partial |
| TC-OKF-007 | Every `agents/**/*.md` parsed into documents | sample tree | `build_context` | all markdown docs present in `documents` | integration | covered |

## RULE — Governance rules, predicates, gates

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-RULE-001 | G-001 no allowed_paths → pass | contract without `allowed_paths` | evaluate | no violation | unit | covered |
| TC-RULE-002 | G-001 write within allowed path → pass | trace write inside allowed | evaluate | no violation | unit | covered |
| TC-RULE-003 | G-001 write outside allowed → ERROR | trace write outside `allowed_paths` | evaluate | ERROR violation naming path | security | covered |
| TC-RULE-004 | G-001 `bash` counts as write | trace bash action outside path | evaluate | flagged | security | covered |
| TC-RULE-005 | G-001 read not flagged | trace read action | evaluate | no violation | unit | covered |
| TC-RULE-006 | G-002 actual == contracted → pass | contract model + matching actual | evaluate | no violation | unit | covered |
| TC-RULE-007 | G-002 drift → WARNING | actual != contracted | evaluate | WARNING violation | integration | covered |
| TC-RULE-008 | G-003 missing skill marker → ERROR | contract skill_obligations, no marker | evaluate | ERROR per unmet skill | integration | covered |
| TC-RULE-009 | G-003 satisfied by ok marker | skill_complete ok=true in turns | evaluate | no violation | integration | covered |
| TC-RULE-010 | Predicate `has_field` non-trivial | spec + target missing field | `check_artifact` | violation for missing/trivial field | unit | covered |
| TC-RULE-011 | Predicate `min_items` counts list | spec `min_items(x,2)` vs 1 item | check | violation | unit | partial |
| TC-RULE-012 | Predicate `matches` regex | spec `matches(x, pattern)` | check | pass/fail per regex | unit | partial |
| TC-RULE-013 | Trivial values rejected (`tbd/todo/none`) | field = "TBD" | check | treated as missing | unit | partial |
| TC-RULE-014 | Invalid predicate expression rejected | malformed `## Predicates` line | `load_artifact_spec` | `ValueError` | unit | partial |
| TC-RULE-015 | Entry gate: missing input artifact blocks | node with declared input absent | runtime step | `WF-ENTRY-001` ERROR, status BLOCKED | integration | covered |
| TC-RULE-016 | Exit gate: missing output artifact blocks | node output not produced | runtime step | `WF-OUT-nnn` ERROR | integration | partial |
| TC-RULE-017 | `run_all` merges schema + rule violations | tree with a load error | `run_all` | includes both load errors and rule violations | integration | partial |

## PROV — Providers, routing, identity

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-PROV-001 | Model ownership resolves provider | model = a Claude alias | `resolve_provider(model, ...)` | returns `claude` regardless of fallbacks | unit | covered |
| TC-PROV-002 | Fallback precedence when model unknown | no owning model, task+node providers | resolve | first non-empty fallback wins | unit | covered |
| TC-PROV-003 | `owns_model` heuristics | `gpt-*`/`claude*`/alias ids | `owns_model` | correct provider claims model | unit | partial |
| TC-PROV-004 | Catalog shape from discovery | registry | `catalog()` | `{providers:[{provider,models:[{id,label,efforts}]}]}` | integration | covered |
| TC-PROV-005 | Claude effort levels parsed from `--help` | claude CLI present | `_claude_efforts` | parsed levels or fallback list | integration | gap |
| TC-PROV-006 | Codex models from cache w/ fallback | cache absent | `_discover_codex` | returns `_CODEX_MODEL_FALLBACK` | integration | partial |
| TC-PROV-007 | Effort→permission/sandbox mapping | effort low/med/high | `_claude_flags`/`_codex_flags` | high → `bypassPermissions` / `danger-full-access` | security | gap |
| TC-PROV-008 | Tag → directive path table | tag = each known role | `TAG_DIRECTIVE` lookup | maps to correct constitution file | unit | partial |
| TC-PROV-009 | Identity card written on node create | create node | inspect `identities/{node}.json` | card with tags + default capabilities | integration | covered |
| TC-PROV-010 | `default_capabilities` per tag | tags list | call | mapped capabilities, deduped | unit | covered |

## CTX — Context assembly & contract resolution

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-CTX-001 | Constitution injected for tag | worker node | `build_session_context` | worker directive + `worker/tdd.md` in files | integration | partial |
| TC-CTX-002 | Issue spec injected for consumer tags | issue_id + worker/qa/architect tag | build ctx | `issues/{id}.md` added to inputs | integration | partial |
| TC-CTX-003 | Missing referenced files surfaced not fatal | declared input absent | build ctx | path in `missing`, not `files` | integration | covered |
| TC-CTX-004 | Frozen directive rows layered by scope | frozen rule at node scope | build ctx | body appears under `# Constitution` | integration | partial |
| TC-CTX-005 | Replay includes only included turns | thread with excluded turn | build ctx | excluded turn absent from `# Prior context` | integration | partial |
| TC-CTX-006 | Contract carries scope + allowed_paths | node with allowed_paths | `resolve` | contract scope + allowed_paths + skill_obligations set | integration | covered |
| TC-CTX-007 | Workflow scope string format | workflow_id + placement | resolve | `scope = workflow:<id>/placement:<pid>` | unit | covered |
| TC-CTX-008 | node_id mismatch rejected | ctx.node_id != node.node_id | resolve | `ValueError` | unit | partial |

## RUN — Agent service lifecycle

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-RUN-001 | Echo run streams + persists | EchoRunner service | `begin` then `run` | system/text/result events; user+assistant turns persisted | integration | covered |
| TC-RUN-002 | Trace events captured from tool calls | runner emits tool_call | run | `trace_events` row with action + target_path | integration | covered |
| TC-RUN-003 | Run finishes `done` on clean pass | clean run | run to completion | run status `done`, usage recorded | integration | covered |
| TC-RUN-004 | ERROR governance violation fails run + raises | run that writes outside allowed_paths | run | status `error`, `GovernanceViolationError` raised, violation persisted | security | gap |
| TC-RUN-005 | Exception path records error turn + finishes | runner raises | run | error turn appended, run `error`, re-raised | integration | partial |
| TC-RUN-006 | Interrupted runs recovered on startup | run left `running` | new `AgentService` | prior run → `interrupted` | integration | covered |
| TC-RUN-007 | Ad-hoc run auto-creates a node | task without node_id, provider given | `begin` | node created with derived name/tags | integration | covered |
| TC-RUN-008 | Distillation candidates captured post-run | run trace with distillation marker | run | correction row created (idempotent) | integration | partial |
| TC-RUN-009 | Per-node lock serializes runs | two runs same node | run concurrently | second awaits first (no interleave) | integration | gap |

## WF — Workflow model & gatekeeper runtime

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-WF-001 | YAML round-trip under OKF | workflow object | `save_workflow` then `load_workflow` | identical graph; file under `agents/workflows/` | integration | covered |
| TC-WF-002 | JSON round-trip | suffix `.json` | save/load | preserved | integration | covered |
| TC-WF-003 | Reject duplicate placement ids | graph with dup id | validate | `WorkflowValidationError` | unit | covered |
| TC-WF-004 | Reject edge to unknown placement | edge to missing id | validate | `WorkflowValidationError` | unit | covered |
| TC-WF-005 | Reject unguarded cycle | cyclic edges, no guard | validate | `WorkflowValidationError` | unit | covered |
| TC-WF-006 | Allow guarded cycle | cycle with a guarded edge | validate | accepted | unit | covered |
| TC-WF-007 | Canvas fields preserved (x/y/interactivity/advance) | full graph | dict round-trip | fields intact | unit | covered |
| TC-WF-008 | `list_workflows` stable order | several saved | list | sorted by stem then suffix | integration | covered |
| TC-WF-009 | Runtime blocks on failing exit gate | node output fails predicate | `runtime.run` | status BLOCKED, override_available, SpawnCard AMBER | integration | covered |
| TC-WF-010 | ASK edge awaits confirm on green | green exit + ASK edge | run | status AWAITING_CONFIRM until confirm_edges supplied | integration | covered |
| TC-WF-011 | HITL node pauses for human input | HITL placement, no input | run | status WAITING_HUMAN, hitl_needed notification | integration | covered |
| TC-WF-012 | Live `on_update` emitted per step | callback supplied | run | RUNNING→terminal states pushed with node_states | integration | covered |
| TC-WF-013 | Override advances past AMBER | override_placements includes id | run | proceeds despite failing gate | integration | partial |
| TC-WF-014 | Entry gate blocks on missing input | declared input absent | run | BLOCKED at entry, `WF-ENTRY-001` | integration | partial |
| TC-WF-015 | Multi-output binding arity check | outputs count != routed artifacts | run | `ValueError` on binding | unit | gap |
| TC-WF-016 | Start placements = zero in-degree | graph with roots | `_start_placements` | correct initial queue | unit | partial |

## STORE — Persistence DAL

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-STORE-001 | Node create/list/get round-trip | db | create then get | all JSON columns preserved | integration | covered |
| TC-STORE-002 | Node id auto-increments | existing `node-001` | create | `node-002` | unit | covered |
| TC-STORE-003 | Delete cascades children + card | node with threads/runs/trace | `delete_node` | rows + identity card removed | integration | covered |
| TC-STORE-004 | Thread get-or-create dedup by scope key | same node/workflow/issue | `get_or_create_thread` | one thread reused | integration | covered |
| TC-STORE-005 | Turn seq monotonic per thread | append several | `append_turn` | seq increments; `list_turns` ordered | integration | covered |
| TC-STORE-006 | `compile_context` only included turns | mixed included flags | compile | excluded omitted | integration | covered |
| TC-STORE-007 | `set_included` reversible | toggle turn | set false then true | reflected in compile | integration | partial |
| TC-STORE-008 | Run lifecycle create→finish | run | create then finish | status/usage/ended_at set | integration | covered |
| TC-STORE-009 | Trace filter by run/node/thread | events across runs | `list_trace_events` filters | correct subset | integration | covered |
| TC-STORE-010 | Violation attributed persistence | violation | `append_violation` | row with run/node/issue/layer/severity | integration | covered |
| TC-STORE-011 | Frozen rule upsert supersede | same (scope,topic_key) | upsert then promote | prior disabled, new active, narrowest-wins query | integration | covered |
| TC-STORE-012 | Scope address chain ordering | rules at multiple scopes | `list_frozen_rules_for_address` | global→machine→workflow→tag→node order | integration | partial |
| TC-STORE-013 | Correction append + promote to rule | candidate correction | `promote_correction` | frozen rule written, correction `promoted` | integration | covered |
| TC-STORE-014 | Distillation candidate capture idempotent | run trace with marker twice | capture | single correction per (event,topic) | integration | partial |

## MARK — Marker protocol & handoff

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-MARK-001 | Parse line-anchored handoff marker | text with `@@HEPHAESTUS@@ {v:1,type:handoff,...}` | `parse_handoff` | HandoffMarker(role,task,issue_id) | unit | covered |
| TC-MARK-002 | Legacy `{"handoff":…}` still parsed | legacy JSON | parse_handoff | marker returned | unit | covered |
| TC-MARK-003 | Invalid/incomplete markers ignored | missing fields | parse | `None` | unit | covered |
| TC-MARK-004 | skill_complete marker parsed | `type:skill_complete, ok:true` | `parse_marker` | SkillCompleteMarker | unit | covered |
| TC-MARK-005 | distillation_candidate valid scope only | scope in allowed set | parse | marker; bad scope → None | unit | partial |
| TC-MARK-006 | Markers from assistant turns, ignore thinking | turns incl thinking | `iter_markers_from_turns` | thinking skipped | unit | covered |
| TC-MARK-007 | Markers from trace command strings | trace raw with `command` | `iter_markers_from_trace` | markers yielded | unit | covered |
| TC-MARK-008 | `has_skill_completion` true only on ok | ok=false marker | check | False | unit | partial |
| TC-MARK-009 | Spawn gate GREEN when no failures | passing exit rules | `evaluate_spawn_gate` | GREEN card | unit | covered |
| TC-MARK-010 | Spawn gate AMBER on any failure | failing exit rule | evaluate | AMBER + failures listed | unit | covered |

## CODE — Code viewer

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-CODE-001 | List configured repos | roots | `list_repos` | name+path per existing dir | integration | covered |
| TC-CODE-002 | Tree ignores vcs/build dirs | repo with `.git`,`node_modules` | `tree` | ignored entries absent; dirs-before-files order | integration | covered |
| TC-CODE-003 | Read file returns language + content | source file | `read_file` | correct language tag, content | integration | covered |
| TC-CODE-004 | Binary file flagged | file with NUL bytes | read_file | `binary: true`, empty content | integration | partial |
| TC-CODE-005 | Oversize file truncated | file > 1MB | read_file | `truncated: true` | integration | gap |
| TC-CODE-006 | Path escape rejected | `../` outside root | `read_file`/`tree` | `ValueError("path escapes repo root")` | security | covered |
| TC-CODE-007 | Unknown repo rejected | bad repo name | any call | `ValueError("unknown repo")` | integration | partial |

## DESK — Desktop bridge

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-DESK-001 | `get_state`/`rescan` return snapshot | app bound | call | dashboard envelope with keys | integration | covered |
| TC-DESK-002 | `list_rules` returns governance layer | app | `list_rules` | G-001/2/3 with id/name/severity/fix_hint | integration | covered |
| TC-DESK-003 | `create_node`/`delete_node`/`list_nodes` | app | round-trip | node appears then removed | integration | covered |
| TC-DESK-004 | `save_workflow`/`list_workflows` | app | save then list | workflow persisted + returned | integration | covered |
| TC-DESK-005 | `run_workflow` starts session | app + saved workflow | call | returns running status; session captured | integration | gap |
| TC-DESK-006 | `parse_handoff_marker` bridge | agent text | call | dict or null | integration | covered |
| TC-DESK-007 | `evaluate_spawn` bridge | role/task/issue | call | SpawnCard dict with gating | integration | covered |
| TC-DESK-008 | `save_correction`/`get_corrections` | app | round-trip | correction persisted + listed | integration | covered |
| TC-DESK-009 | `get_trace` filters | app | call w/ run/node/thread | filtered events | integration | partial |
| TC-DESK-010 | `pick_directory` returns choice or null | app window | call | chosen path or null | manual | gap |
| TC-DESK-011 | Bridge without app raises | Bridge, no app | node calls | `RuntimeError("no app bound")` | unit | covered |

## UI — Frontend flows (Playwright / manual)

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-UI-001 | Preview fallback with no bridge | browser, no pywebview | load app | mock snapshot renders after 500ms; "Preview" badge | e2e | gap |
| TC-UI-002 | Tab switching | app loaded | click coordinator/canvas/code/agent | correct view mounts | e2e | gap |
| TC-UI-003 | Coordinator create node | Coordinator tab | fill form, submit | node row appears; provider/model/effort dropdowns from catalog | e2e | gap |
| TC-UI-004 | Coordinator delete node | node exists | delete | row removed | e2e | gap |
| TC-UI-005 | Canvas add placement + edge | Canvas tab | drag node, wire edge | graph reflects placement + edge | e2e | gap |
| TC-UI-006 | Canvas save workflow (YAML/JSON) | edited graph | choose format, save | success toast; persisted | e2e | gap |
| TC-UI-007 | Canvas run + live status | saved workflow, bridge | run | node chips transition; edge states animate | e2e | gap |
| TC-UI-008 | Run Agent streams events | Agent tab | fill + run | events stream by category color; routed-to meta shown | e2e | gap |
| TC-UI-009 | Run Agent bridge-unavailable message | no bridge | run | error event "bridge unavailable" | e2e | gap |
| TC-UI-010 | Violation → toast → correction capture | snapshot w/ violation | observe toast, add note | correction saved | e2e | gap |
| TC-UI-011 | Workflow notification toasts dedup | repeated notifications | push | each id shown once | e2e | gap |
| TC-UI-012 | Code tab browse + highlight | Code tab | pick repo, open file | tree renders, file shown with syntax highlight | e2e | gap |

## SEC — Security-focused

| ID | Title | Pre | Steps | Expected | Type | Status |
|---|---|---|---|---|---|---|
| TC-SEC-001 | Code viewer path traversal blocked | repo root | request `../../etc` | `ValueError`, no read | security | covered |
| TC-SEC-002 | Code viewer is read-only | any repo | attempt write path | no write method exists on surface | security | gap |
| TC-SEC-003 | Scope adherence blocks out-of-scope writes | run with allowed_paths | agent writes elsewhere | G-001 ERROR, run fails | security | gap |
| TC-SEC-004 | Effort escalation is explicit | high-effort contract | resolve flags | `bypassPermissions`/`danger-full-access` only at high; documented risk | security | gap |
| TC-SEC-005 | Codex argv sandbox default safe | contract no effort | `build_codex_argv` | `workspace-write` sandbox, `auto` approval by default | security | partial |
| TC-SEC-006 | Marker injection cannot forge cross-scope frozen rule | untrusted marker text | parse + promote flow | promotion requires confirmer; scope validated | security | gap |
| TC-SEC-007 | `.hephaestus/` state kept out of git | scaffold | inspect `.gitignore` | state dir ignored | security | covered |

---

## Coverage summary & top gaps

**Mapped:** 20 interaction flows, ~22 components, **107 test cases** across 13 areas.

**Root suite today:** 211 unit tests, all passing — strong coverage of pure
logic (rules, predicates, workflow validation, store DAL, markers, contract
resolution).

**Top gaps (no coverage in the QA-owned homes, which are empty):**

1. **UI / e2e — entirely absent.** No Playwright or manual browser coverage for
   any of the 4 tabs (`TC-UI-001..012`). `agents/qa/playwright/` is empty. This
   is the single largest hole: the whole desktop UX is unverified end-to-end.
2. **Security suite — absent.** Path-traversal (`TC-SEC-001`), read-only
   guarantee (`TC-SEC-002`), scope-adherence-fails-the-run (`TC-SEC-003/RUN-004`),
   and effort→permission/sandbox escalation (`TC-SEC-004`, `TC-PROV-007`) have no
   tests. These are the highest-risk behaviors and belong in
   `agents/qa/tests/security/`.
3. **Desktop bridge integration — absent.** The ~25 `js_api` methods (the entire
   UI↔core contract) have no bridge-level integration tests
   (`TC-DESK-*`); only the underlying store functions are unit-tested.
4. **Full-pipeline / workflow-run integration through the bridge**
   (`TC-DESK-005`, `TC-WF-013/014` override + entry paths, `TC-RUN-004/009`)
   — the gatekeeper is unit-tested but not exercised as a live end-to-end run.
5. **Live provider discovery** (`TC-PROV-005/006/007`) depends on external CLIs
   (`claude`, `codex`) and is untested against real CLI output.

**Recommended QA build order:** security suite → desktop-bridge integration →
Playwright e2e for the 4 tabs. These map cleanly onto the empty
`agents/qa/tests/security/`, `agents/qa/tests/integration/`, and
`agents/qa/playwright/` homes.

## Risks / ambiguities to route onward

- **Doc vs. code drift (Architect):** `structural.md` and `README.md` still
  describe the S-001..S-006 structural rules and "27 tests", but those hardcoded
  rules were **removed** (`rules/registry.py` docstring; `dashboard.py` /
  `index.py` note governance moved to user-authored specs). QA can only test
  observable behavior — the removed S-rules are **not** an acceptance surface
  today. Recommend Architect reconcile the spec docs so future QA gates cite the
  right rule set.
- **Acceptance criteria ownership (Product Manager / Architect):** many `gap`
  rows (esp. UI/e2e and security) assert behavior QA *observed in code* but for
  which no issue spec states the intended contract (e.g. exact effort→permission
  policy, oversize-file threshold semantics). Per QA rule S-005/scope, QA does
  not invent acceptance criteria — these need a spec before they become gating
  tests.
- **External-CLI dependence:** `TC-PROV-005/006/007` and any live Claude/Codex
  run tests require logged-in CLIs; they cannot run in a hermetic CI without
  fixtures/mocks. Route a decision on fixture strategy (recorded CLI output vs.
  skip-in-CI) to DevOps/Architect.
- **Frozen-rule / distillation promotion is a trust boundary** (`TC-SEC-006`):
  markers are parsed from untrusted agent output and can seed corrections;
  promotion to a scoped frozen rule requires a confirmer. Whether marker-sourced
  candidates should ever auto-promote is a governance-policy question for
  Product Manager/Architect, not something QA should assume.
