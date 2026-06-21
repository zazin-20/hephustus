# 004 — Client-owned compiled context + pruning

**Type:** AFK (live verify) · **Status:** ready-for-agent

## What to build

Make Hephaestus the owner of context, and let the user curate it.

- `compile_context(thread)` assembles model input from **included turns** + the role
  directive + injected OKF artifacts (a query, not a stored blob).
- Flip the Claude adapter **off opaque provider-resume** so both backends consume
  client-compiled context (Codex already does). One context path for both.
- Per-turn **include/exclude** toggle in the conversation UI — soft and reversible;
  shapes the next run's context without deleting the transcript record.

Reference: `architecture-coordinator.md` D5, §4 (`turns.included`).

## Acceptance criteria

- [ ] A run's input is assembled from `compile_context` (unit test: excluded turns absent, included present, order preserved).
- [ ] Claude no longer relies on provider resume; a multi-turn conversation still coheres.
- [ ] Toggling a turn to excluded removes it from the next run's context; the transcript record remains.
- [ ] Codex and Claude use the same context-construction path.
- [ ] Tests: compile_context inclusion/exclusion/order; both adapters receive compiled context.

## Blocked by

- 003 — Threads + Runs + transcript
