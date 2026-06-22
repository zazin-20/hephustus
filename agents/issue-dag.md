# Hephaestus Issue DAG

## Current Open Sequence

```text
#2  DONE
  |
  -> #3  Threads + Runs + transcript
       |
       +-> #4  Client-owned compiled context + pruning
       |
       +-> #5  Trace capture + audit view
             |
             -> #6  EvaluationContext + unified rule engine
                   |
                   +-> #7  Execution Contract + hard governance + governance rules
                   |
                   +-> #8  Orchestrator handoff -> gated Spawn
                         |
                         -> #9  Compliance notifications + Correction Box
                              (also depends on #7)
```

## Parallel Waves

1. `#3` is the current critical path.
2. After `#3`, run `#4` and `#5` in parallel.
3. After `#5`, run `#6`.
4. After `#6`, run `#7` and `#8` in parallel.
5. After both `#7` and `#8`, run `#9`.

## Agent Ownership Rule

- Each issue gets one dedicated sub-agent owner.
- The owner may only edit files needed for that issue.
- Shared files must be coordinated through the parent agent before merge.
- Blocked issues may do read-only prep, test planning, and seam discovery, but
  should not land speculative implementation ahead of their dependency.

## Live GitHub Snapshot

Open issues confirmed on `2026-06-22`:

- `#3` `003 - Threads + Runs + transcript`
- `#4` `004 - Client-owned compiled context + pruning`
- `#5` `005 - Trace capture + audit view`
- `#6` `006 - EvaluationContext + unified rule engine`
- `#7` `007 - Execution Contract + hard governance + governance rules`
- `#8` `008 - Orchestrator handoff -> gated Spawn`
- `#9` `009 - Compliance notifications + Correction Box`
