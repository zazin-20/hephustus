# Hephaestus Issue DAG

## Completed

```text
#1  DONE -> #2  DONE -> #3  DONE -> #4  DONE -> #5  DONE -> #6  DONE
  -> #7  DONE -> #8  DONE -> #9  DONE
       (foundation wave — MVP core)

#10 DONE  OKF-layout module
#11 DONE  Normalized agent-turn taxonomy
#12 DONE  Run-construction moved into AgentService
  |
  -> #13 DONE  ExecutionContract as the run-config seam

#14 DONE  CONTEXT.md domain glossary
#16 DONE  ArtifactSpec + predicate checker
#17 DONE  Marker protocol parser
  |
  -> #18 DONE  Node model + scope-addressed state (Role removed, tags added)
       |
       -> #15 DONE  Provider registry (reconciled onto #18's tags foundation)

#19 DONE  Clean-slate context assembly (layered constitution + replay)
#20 DONE  Workflow model + storage (YAML/JSON graph under agents/workflows/)
#21 DONE  ExecutionContract as a derived record
#22 DONE  Skill registry + cross-provider injection + obligation exit-gate
#23 DONE  Gatekeeper runtime (node-by-node advance, entry/exit gates, HITL/AFK)
#24 DONE  Distillation loop (marker -> Correction Box -> promote -> inject)
```

All of #1-#24 are closed on GitHub and merged to `main` (confirmed live,
2026-07-04). Landing history:

- #1-13: foundation wave, on `main` before the governance-engine waves began.
- #14-18/#15 merged at `7d2b8d6` (`integration/wave1-014-015-016-017-018`).
- #19-20 merged at `c44e0e0` (`integration/wave2-019-020`).
- #21-22 merged at `1cc47ad` (`integration/wave3-021-022`).
- #23-24 merged at `602a015` (`integration/wave4-023-024`), pushed to origin
  2026-07-04.
- #25 merged at `b5129d4` (`integration/wave5-025`), pushed to origin
  2026-07-04. GitHub issue #25 closed.

## ADR-0002 provider-identity finish work — DONE

```text
#26 DONE  resolve_provider() single seam
  |
  -> #27 DONE  Remove the vestigial Tool enum
```

Both issues derived from **ADR-0002**
(`docs/adr/0002-provider-identity-single-seam.md`), which formalized the
pending "Provider registry" decision (governance-engine-revised.md §8, audit
#1) after a `/improve-codebase-architecture` pass + Architect grill. #26
merged at `16bc96d`, #27 at `3b311c2`; both closed on GitHub 2026-07-04.
ADR-0002 is fully landed — provider identity is one registry-owned seam, the
closed `Tool` enum is gone, and a new provider is now genuinely one registered
module (regression test proves `gemini_cli` is CLI-accepted with no routing
edits).

A third architecture-pass finding (context-accumulation) was investigated and
**dropped** — the clean-slate-per-run behavior it named already exists (thread
keyed by workflow-run), and the only open part (long-thread compaction) is
already owned by the deferred Headroom compression seam.

## ADR-0003 reconciliation + node-authoring (#28 DONE) + artifact-authoring

```text
ADR-0001  SUPERSEDED by ADR-0003 (graph is an executable gatekeeper runtime)
ADR-0003  ACCEPTED  (docs only — reconciles record to the shipped runtime)
  |
  -> #28  DONE  Node authoring (full Node contract authorable + editable)
       |
       -> #29  DONE  Artifact authoring (author + connect to a node)
             |
             -> [coordinator-rehome]  DRAFT — retire Coordinator; rehome to Library + Console  (frontend-only)
```

- **ADR-0003** (`docs/adr/0003-node-graph-is-an-executable-gatekeeper-runtime.md`)
  supersedes ADR-0001: the node graph is the executable gatekeeper runtime, not a
  planning-only surface; the `Start/Agent/Condition/…` typed-node set is
  reconciled to the shipped uniform `Node` + `Placement` + `Edge` + `Guard` +
  AFK/HITL + ask/allow model. ADR-0001 retained verbatim with a superseded banner
  (honest history). Docs only — no code touched.
- **#28 node-authoring — DONE.** Merged to `main` at `91a222e` (impl `4e76fc7`,
  Architect review `1624a21`), pushed, issue closed 2026-07-07. Widened
  `Bridge.create_node` + `api.js` to the full `Node` contract, added
  `store/nodes.py::update_node` + `Bridge.update_node`, and a create/edit UI form
  (`NodeForm.jsx`) for `inputs, outputs, skills, skill_obligations, allowed_paths,
  allowed_tools`. `context_policy` plumbed but held read-only. 213 backend tests
  (+2), vite build green.
- **[artifact-authoring]** — draft spec at
  `agents/architect/issues/DRAFT-artifact-authoring.md` (pending user approval to
  open on GitHub). Makes the **artifact definition** authorable + bindable to a
  node: adds `store/artifacts.py` (thin `artifact_id → path` index), an
  `okf_layout.artifacts_dir()` home, a `create/edit Artifact` UI + catalog, and an
  id-resolution seam so node `outputs`/`inputs` bind by artifact id (backward-
  compatible with #28's literal paths). **No runtime gating change** — `context.py`
  injection + `WF-OUT-*` check already do both halves of the loop. v1 acceptance:
  *author an artifact and connect it to a node*; richer predicates (`matches`/
  `has_field`), live preview, and external sanity-checkers are deferred fast-
  follows. **INDEPENDENT** — builds only on merged work (#28 + the artifact-spec
  engine); dispatchable the moment it is filed. Grill record:
  `product-manager/todo/artifact-spec-authoring.md`. One dedicated owner.

## Held for Human

- None currently. (`#25` was held-for-human by default but human-authorized
  and landed 2026-07-04. #26/#27 are `ready-for-agent`/`AFK` — mechanical
  refactors with no open design questions, resolved by ADR-0002.)

## Agent Ownership Rule

- Each issue gets one dedicated sub-agent owner.
- The owner may only edit files needed for that issue.
- Shared files must be coordinated through the parent agent before merge.
- Blocked issues may do read-only prep, test planning, and seam discovery, but
  should not land speculative implementation ahead of their dependency.

## Live GitHub Snapshot

Checked `2026-07-07`:

- `#1`-`#28` — all **closed**, all merged to `main` (#28 merged `91a222e`,
  pushed + closed 2026-07-07).

No GitHub issues are open. The **artifact-authoring** work above has a drafted
spec ready to file (`agents/architect/issues/DRAFT-artifact-authoring.md`),
pending user approval to open it on GitHub — dispatchable the moment it is filed.
Additional candidate follow-ups exist from the 2026-07-04 architecture pass
(frontend Coordinator.jsx god-component, dead evaluate_spawn, unclosed DB
connections, dual marker-parser, stale root architecture.md, the 4 other
pending-ADR decisions from governance-engine-revised.md §8) — none filed yet.
