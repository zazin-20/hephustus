# Hephaestus Issue DAG

## Completed

```text
#1  DONE -> #2  DONE -> #3  DONE -> #4  DONE -> #5  DONE -> #6  DONE
  -> #7  DONE -> #8  DONE -> #9  DONE
       (foundation wave - MVP core)

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
#25 DONE  Node-graph editor + live monitor (canvas author/run modes)

#26 DONE  resolve_provider() single seam
  |
  -> #27 DONE  Remove the vestigial Tool enum

ADR-0001  SUPERSEDED by ADR-0003 (graph is an executable gatekeeper runtime)
ADR-0003  ACCEPTED  (docs only - reconciles record to shipped runtime)
  |
  -> #28 DONE  Node authoring (full Node contract authorable + editable)
       |
       -> #29 DONE  Artifact authoring (author + connect to a node)
            |
            -> #30 DONE  Retire Coordinator; rehome to Library + Console
                 |
                 -> [graph-runtime-convergence] BACKLOG / needs-design
                    Console -> canvas drill-in; role spawn card -> graph gatekeeper
```

## Landing History

All of `#1` through `#30` are closed on GitHub and merged to `main`.

- `#1`-`#13`: foundation wave, on `main` before the governance-engine waves began.
- `#14`-`#18` plus `#15`: merged at `7d2b8d6` (`integration/wave1-014-015-016-017-018`).
- `#19`-`#20`: merged at `c44e0e0` (`integration/wave2-019-020`).
- `#21`-`#22`: merged at `1cc47ad` (`integration/wave3-021-022`).
- `#23`-`#24`: merged at `602a015` (`integration/wave4-023-024`), pushed 2026-07-04.
- `#25`: merged at `b5129d4` (`integration/wave5-025`), pushed and closed 2026-07-04.
- `#26`: merged at `16bc96d`, closed 2026-07-04.
- `#27`: merged at `3b311c2`, closed 2026-07-04.
- `#28`: merged at `91a222e` (impl `4e76fc7`, Architect review `1624a21`), pushed and closed 2026-07-07.
- `#29`: merged at `1d4f80e` (impl `d833d4a`, Architect review `0eb566e`), pushed and closed 2026-07-07.
- `#30`: merged at `077047b` (impl `9575b14`, Architect review `0d5887f`), pushed and closed 2026-07-07.
- `446d3aa`: #30 closeout bookkeeping commit; local `main` and remote `main` match here.

## ADR-0002 Provider Identity Finish Work

Issues `#26` and `#27` derived from ADR-0002
(`docs/adr/0002-provider-identity-single-seam.md`), which formalized the
pending provider-registry decision from `governance-engine-revised.md`.

ADR-0002 is fully landed: provider identity is registry-owned, the closed
`Tool` enum is gone, and a new provider is now one registered module. The
regression suite proves a `gemini_cli` provider can be CLI-accepted without
routing edits.

A third architecture-pass finding, context accumulation, was investigated and
dropped: clean-slate per-run behavior already exists. The remaining long-thread
compaction concern is owned by the deferred prompt-compression seam.

## ADR-0003 UI Authoring Wave

- ADR-0003 (`docs/adr/0003-node-graph-is-an-executable-gatekeeper-runtime.md`)
  supersedes ADR-0001. The node graph is the executable gatekeeper runtime, not
  a planning-only surface. ADR-0001 is retained as history with a superseded
  banner.
- `#28` made the full Node contract authorable/editable: `update_node`, widened
  desktop bridge and API payloads, and `NodeForm.jsx` list editors for inputs,
  outputs, skills, skill obligations, allowed paths, and allowed tools.
  `context_policy` is plumbed but read-only/inert.
- `#29` made artifact definitions authorable: the UI writes markdown artifact
  specs under `agents/artifacts/`, indexes them through `store/artifacts.py`,
  and lets nodes bind inputs/outputs by `artifact_id` with literal-path fallback.
  This reused the existing context injection and `WF-OUT-*` gate.
- `#30` retired the old Coordinator surface: authored-state CRUD moved into
  `Library.jsx`, single-node conversation/trace moved into `Console.jsx`, and
  Library became the default app view.

## Held For Human

- None currently.

## Agent Ownership Rule

- Each issue gets one dedicated sub-agent owner.
- The owner may only edit files needed for that issue.
- Shared files must be coordinated through the parent agent before merge.
- Blocked issues may do read-only prep, test planning, and seam discovery, but
  should not land speculative implementation ahead of their dependency.

## Live GitHub Snapshot

Checked 2026-07-07 with:

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" issue list --repo zazin-20/hephustus --state all --limit 40
```

- `#1`-`#30` are all closed on GitHub.
- No GitHub issues are open.
- No open PRs were returned by `gh pr list --state all --limit 20`.
- Local and remote `main` both point at `446d3aa`.

## Local Backlog / Deferred Work

- `agents/architect/issues/DRAFT-graph-runtime-convergence.md` is backlog /
  needs-design, not a filed GitHub issue. It records the ADR-0003 convergence
  flags from #30: Console should become a canvas node drill-in, and role-based
  spawn cards should be absorbed into graph gatekeeping.
- `agents/orchestrator/tasks/T-dynamic-fanout.md` is deferred by user direction.
- `agents/orchestrator/tasks/T-prompt-compression.md` is deferred by user
  direction. `Node.context_policy` remains stored but inert until this lands.
