# Hephaestus Issue DAG

## Current Open Sequence

```text
#1  DONE
  |
  -> #2  DONE
       |
       -> #3  DONE
            |
            -> #4  DONE
                 |
                 -> #5  DONE
                      |
                      -> #6  DONE
                           |
                           -> #7  DONE
                                |
                                -> #8  DONE
                                     |
                                     -> #9  DONE

#10  Introduce an OKF-layout module
#11  Normalize the agent-turn vocabulary and event taxonomy
#12  Move run-construction out of the desktop shell into AgentService
  |
  -> #13  Make ExecutionContract the single run-config seam
           (blocked by #12)
```

## Parallel Waves

1. `#10`, `#11`, and `#12` are the current open wave.
2. `#10` is an independent locality refactor and can run in parallel with the others.
3. `#11` is unblocked, but it is a deeper design seam and should stay coordinated with the run/execution work.
4. `#12` is the critical-path implementation issue because it unblocks `#13`.
5. After `#12`, run `#13`.

## Agent Ownership Rule

- Each issue gets one dedicated sub-agent owner.
- The owner may only edit files needed for that issue.
- Shared files must be coordinated through the parent agent before merge.
- Blocked issues may do read-only prep, test planning, and seam discovery, but
  should not land speculative implementation ahead of their dependency.

## Live GitHub Snapshot

Open issues confirmed on `2026-06-23`:

- `#10` `Introduce an OKF-layout module — one home for the agents/ tree shape`
- `#11` `Normalize the agent-turn vocabulary and concentrate the event taxonomy`
- `#12` `Move run-construction out of the desktop shell into AgentService`
- `#13` `Make ExecutionContract the single run-config seam (remove the bypass)`
