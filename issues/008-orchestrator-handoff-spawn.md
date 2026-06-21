# 008 — Orchestrator handoff → gated Spawn

**Type:** AFK · **Status:** ready-for-agent

## What to build

The pipeline flow: the Orchestrator signals readiness, the human confirms.

- Parse the **handoff marker** from Orchestrator output:
  `{"handoff": {"role": "...", "task": "...", "issue_id": "..."}}`.
- On detection, evaluate the outgoing actor's **exit rules**
  (`layer="exit"`, `scope="issue"`) and render a **Spawn card** pre-filled with
  role + task, **gated** on the result:
  - all pass → green;
  - failures → amber, listing which rules failed with fix hints (force-spawn allowed).
- Confirming Spawn starts the next actor's run with the pre-filled task.

Reference: `architecture-coordinator.md` §6 (trigger), `prd-coordinator.md` (handoff marker).

## Acceptance criteria

- [ ] A valid handoff marker in Orchestrator output surfaces a Spawn card with role + task pre-filled.
- [ ] Exit rules evaluate for the issue; pass → green, fail → amber listing failures.
- [ ] Confirming Spawn starts the next actor's run with the pre-filled task.
- [ ] Malformed or non-handoff JSON does not trigger a card.
- [ ] Tests: marker parse (valid / embedded mid-text / malformed); exit-rule gating result.

## Blocked by

- 006 — EvaluationContext + unified rule engine
