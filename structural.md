---
title: Hephaestus — Governance & Compliance Rules
version: 0.3.0
status: active
created: 2026-06-21
updated: 2026-07-04
owner: architect
layer: spec
---

# Governance & Compliance Rules

> **Canonical model:** [`docs/design/governance-engine.md`](docs/design/governance-engine.md).
> This doc used to define a hardcoded `S-001..S-006` **structural rule library** (the
> issue → worker → handoff → QA → log pipeline). That library was **removed on
> 2026-06-23** when Hephaestus pivoted to a *user-authored workflow governance engine*.
> Compliance now comes from two places — **user-authored artifact-spec predicates** and a
> small **fixed set of run-time governance rules** — not from a built-in structural rule set.
> The former S-rules are recorded under [History](#history) for context only.

Rules are checkable **deterministically** — from the filesystem/OKF frontmatter, or from a
run's execution contract + trace — no LLM required. They form the compliance layer of
Hephaestus. Behavioral/LLM-judged rules remain a deferred, opt-in extension.

## Rule Interface

Every rule (built-in governance rule or user-authored rule) implements the
`HephaestusRule` interface in `hephaestus/rules/base.py`:

```python
class HephaestusRule(ABC):
    id: str
    name: str
    layer: str = "structural"          # e.g. "structural" | "governance"
    trigger: str = "on_change"         # "on_change" | "on_run"
    scope: str = "workspace"
    severity: Severity = Severity.ERROR
    roles_involved: list[str] = []
    auto_fixable: bool = False
    fix_hint: str = ""

    def check(self, ctx: EvaluationContext) -> ViolationResult:
        ...
```

```python
class ViolationResult:
    violations: list[Violation]        # empty ⇒ passed

class Violation:
    rule_id: str
    severity: Severity
    message: str
    artifact: str       # file path (or skill id / target) that triggered the violation
    fix_hint: str
```

The `EvaluationContext` a rule reads is the run-scoped view: the parsed OKF tree
(`ctx.okf`, an `OKFContext` = documents + schema load errors), plus, for run-time rules,
the execution contract (`ctx.contract`), the captured `ctx.trace`, `ctx.turns`, and the
acting agent (`ctx.actor`). `on_change` rules read the tree; `on_run` rules read the trace.

## The generic runner (`hephaestus/rules/registry.py`)

`registry.py` is a **generic gate-runner with no built-in rule set** — the caller passes
the rules to run:

- `run_rules(ctx, rules=[...], enabled=None)` — run the given rules against a context.
- `run_all(ctx, enabled=None)` — Tier-1 schema (load) errors **plus** `run_rules` — one call
  surfaces every problem in the tree. (The default `rules` list is empty, so with no rules
  passed it returns only the Tier-1 load errors.)
- `run_layer(rules, ctx, layer=...)` — run only the rules whose `.layer` matches.

Callers supply either **user-authored artifact predicates** or `ALL_GOVERNANCE_RULES`.

## Built-in governance rules (`hephaestus/rules/governance.py`)

These are **not** issue-lifecycle rules — they are the fixed, cross-workflow guarantees
Hephaestus enforces at a node/run boundary. They are `layer: "governance"`, `trigger:
"on_run"`, and read the run's `ExecutionContract` + trace. `ALL_GOVERNANCE_RULES` exports
all three.

| Rule ID | Class | Severity | Checks |
|---|---|---|---|
| `G-001` | `G001ScopeAdherence` | error | No write action (`write_file`/`bash`) in the trace targets a path outside the contract's `allowed_paths`. |
| `G-002` | `G002ModelCompliance` | warning | The run's `actual_model` matches the contracted `model`. |
| `G-003` | `G003SkillObligation` | error | Every enforced skill in the contract's `skill_obligations` emitted a `@@HEPHAESTUS@@ skill_complete` marker (`ok=true`) in the trace/turns. |

## User-authored artifact-spec predicates

The replacement for the removed structural library. An **artifact-spec** is a user-authored
markdown doc that both (1) directs the agent generating the artifact and (2) is Hephaestus's
deterministic **exit gate**. Its mandatory fields are expressed as composable, shipped
predicates (no user-written code):

`has_field`, `has_section`, `non_empty`, `min_items(n)`, `matches(regex)`.

`has_X()` means **present *and* non-trivial** (a `## User Stories\nTBD` section fails), so a
gate is presence + non-triviality by default; an LLM-judge is an opt-in per-node extension.
See `docs/design/governance-engine.md` §3.3 and §7.3 for the full model (entry gate = required
inputs present + valid; exit gate = output-spec predicates + enforced skill markers).

## Violation Severity Guide

| Severity | Meaning | Dashboard Treatment |
|---|---|---|
| `error` | Blocks the gate / pipeline progression. Work should not advance until resolved. | Red badge, node/gate blocked |
| `warning` | Drift detected. Should be resolved but does not block. | Yellow badge, flagged |
| `info` | Informational. No action required but worth knowing. | Grey badge, collapsible |

---

## History

**The hardcoded `S-001..S-006` structural rule library (removed 2026-06-23).**
Before the governance-engine pivot, Hephaestus shipped six built-in rules that hardcoded a
single issue → worker → handoff → QA → log pipeline. They lived in `hephaestus/rules/structural.py`
(now deleted) and read a typed `OKFContext` of `IssueSpec`/`Handoff`/`QAEvidence`/`LogEntry`
collections (those Pydantic doc classes were deleted at the same time). They were removed
deliberately — governance moved to user-authored specs — not because the pipeline was wrong;
that loop is now expressible as *one authored workflow* rather than baked into code.

For the record, the six were:

| Rule ID | What it enforced |
|---|---|
| `S-001` | Worker must have an Architect issue spec before starting |
| `S-002` | Worker must leave a handoff artifact after completing |
| `S-003` | QA must produce evidence before an issue is logged as done |
| `S-004` | A completion log entry must exist for every completed issue |
| `S-005` | A handoff must have Architect review (`reviewed_by: architect`) before QA starts |
| `S-006` | Sprint state must be consistent (issues/index vs the completion log) |

Referenced by (kept intentionally, as narrative history, until re-recorded as ADRs):
`docs/design/governance-engine.md` §6 (the removal record) and the Architect role docs.
