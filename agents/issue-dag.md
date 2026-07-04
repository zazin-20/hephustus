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

## Current Open Sequence (ADR-0002 provider-identity finish work)

```text
#26  resolve_provider() single seam  (unblocked)
  |
  -> #27  Remove the vestigial Tool enum  (blocked by #26)
```

Both issues derive from **ADR-0002**
(`docs/adr/0002-provider-identity-single-seam.md`), which formalized the
pending "Provider registry" decision (governance-engine-revised.md §8, audit
#1) after a `/improve-codebase-architecture` pass + Architect grill. A third
finding (context-accumulation) was investigated and **dropped** — the
clean-slate-per-run behavior it named already exists (thread keyed by
workflow-run), and the only open part (long-thread compaction) is already
owned by the deferred Headroom compression seam.

Dependency edges:

| Issue | Blocked by |
|---|---|
| #26 resolve_provider() single seam | none — ready now |
| #27 Remove Tool enum | #26 (both touch service.py provider-resolution) |

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

Checked `2026-07-04`:

- `#1`-`#25` — all **closed**, all merged to `main` (see landing history above).
- `#26` resolve_provider() single seam — **open**, `ready-for-agent`/`AFK`, unblocked.
- `#27` Remove the vestigial Tool enum — **open**, `ready-for-agent`/`AFK`, blocked by #26.

Open wave: `#26` is dispatchable now; `#27` follows once #26 lands.
