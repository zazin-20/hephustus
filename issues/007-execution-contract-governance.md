# 007 — Execution Contract + hard governance + governance rules

**Type:** AFK (live verify) · **Status:** ready-for-agent

## What to build

Turn the run spec into a governed contract and enforce it.

- First-class **`ExecutionContract`** (actor, context, scope, model, effort, tools).
- Provider **adapters** translate the contract to native flags and **hard-enforce**
  what each provider supports:
  - Claude: allowed/disallowed tools, permission mode, cwd, hooks.
  - Codex: sandbox, approval policy, `-C` working dir.
- **Governance rules** (`layer="governance"`) verify scope adherence using
  `ctx.trace` + `ctx.contract`. Violations persisted with **attribution**
  (`run_id` / `agent_id`).

Hard governance at the boundary; compliance is the backstop where a provider can't
enforce a given constraint.

Reference: `architecture-coordinator.md` D6, §6.

## Acceptance criteria

- [ ] A run is governed by an `ExecutionContract` carrying model/effort/scope/tools.
- [ ] An out-of-scope write is prevented at the boundary where the provider supports it; otherwise flagged by a governance rule.
- [ ] Violations persisted with `run_id` + `agent_id`; attributable to the causing agent.
- [ ] `model` / `effort` from the profile reach the provider invocation.
- [ ] Tests: contract → adapter flag mapping; governance scope rule fails on an out-of-scope trace; attribution recorded.

## Blocked by

- 006 — EvaluationContext + unified rule engine
