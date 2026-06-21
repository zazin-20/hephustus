# 009 — Compliance notifications + Correction Box

**Type:** AFK · **Status:** ready-for-agent

## What to build

Move compliance from a tab into the workflow, and capture human feedback.

- Violations surface as **toast notifications** (severity, rule, issue, agent, message).
- **Remove the standalone Compliance tab** → navigation becomes two tabs:
  **Coordinator | Code**. Compliance runs in the background.
- "Correct →" opens a **Correction Box** pre-filled with the violation/agent/issue;
  submitting writes a **`corrections`** row linked to the violation (the seed of the
  self-improving OKF loop — capture now, promote later).

Reference: `architecture-coordinator.md` §4 (`corrections`), §6 step 9, `prd-coordinator.md`.

## Acceptance criteria

- [ ] Detected violations raise toasts with rule / issue / agent / message; auto-dismiss with manual override.
- [ ] Compliance tab removed; nav is Coordinator | Code.
- [ ] "Correct →" writes a `corrections` row (`violation_id`, `agent_id`, `issue_id`, `note`).
- [ ] Dismiss acknowledges in-session; unresolved violations re-fire on the next cycle.
- [ ] Tests: correction persisted + linked to violation; notification payload shape.

## Blocked by

- 007 — Execution Contract + hard governance + governance rules
