# 006 — EvaluationContext + unified rule engine

**Type:** AFK · **Status:** ready-for-agent

## What to build

Unify the compliance engine onto one interface and one context, ahead of the
governance/behavioral layers.

- Introduce **`EvaluationContext { okf, trace, contract, actor, scope }`**. Today's
  `OKFContext` becomes the `okf` member.
- Widen `HephaestusRule.check(ctx: EvaluationContext)` and have each rule declare
  `layer` (structural | exit | governance | behavioral), `trigger`, and `scope`.
- Refactor `S-001..S-006` to read `ctx.okf` — **mechanical, behavior unchanged**.
- Registry selects rules by layer/trigger/scope.

This collapses the PRD's free-function exit rules into the same interface (no second
rule system).

Reference: `architecture-coordinator.md` D7, §5.

## Acceptance criteria

- [ ] `EvaluationContext` bundles okf + trace + contract + actor + scope.
- [ ] All six structural rules pass unchanged under the new interface (regression).
- [ ] Rules declare layer/trigger/scope; registry can select a subset.
- [ ] Existing rule tests are green after the refactor; no behavior change to S-001..S-006.

## Blocked by

- 005 — Trace capture + audit view
