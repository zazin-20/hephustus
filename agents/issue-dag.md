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

## Current Open Sequence

```text
#20 DONE, #23 DONE
  |
  -> #25  Node-graph editor + live monitor  [HELD — see below]
```

Only one issue remains open: `#25`, blocked-by `#20` (done) and `#23` (done)
— technically unblocked, but held regardless (see below). No other open
issues exist as of the live GitHub snapshot below.

## Held for Human

- `#25` (node-graph editor + live monitor) carries no `ready-for-agent`/`AFK`
  label — frontend-heavy, held for human review by default. Do not
  auto-dispatch without explicit human go-ahead, even though its
  dependencies (`#20`, `#23`) are done.
- **2026-07-04: human explicitly authorized dispatch of #25** (Architect
  review + Worker implementation). This is a one-time authorization for this
  issue, not a standing change to the hold policy — future frontend-heavy
  issues should still default to held-for-human unless similarly confirmed.

## Agent Ownership Rule

- Each issue gets one dedicated sub-agent owner.
- The owner may only edit files needed for that issue.
- Shared files must be coordinated through the parent agent before merge.
- Blocked issues may do read-only prep, test planning, and seam discovery, but
  should not land speculative implementation ahead of their dependency.

## Live GitHub Snapshot

Checked `2026-07-04`:

- `#1`-`#24` — all **closed**, all merged to `main` (see landing history above).
- `#25` Node-graph editor + live monitor — **open**, held for human (no
  `ready-for-agent`/`AFK` label).

No open, dispatchable work remains. The pipeline is idle until `#25` is
picked up by a human, or new issues are filed.
