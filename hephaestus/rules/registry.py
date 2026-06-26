"""Rule registry and runner.

REUSABLE — the generic gate-runner. `run_rules` executes whatever rules it is
given against a context; `run_all` also surfaces Tier-1 schema load errors, so a
single call returns every problem in the tree. There is no built-in rule set
anymore — callers pass the rules (e.g. user-authored artifact predicates, or
`ALL_GOVERNANCE_RULES`). The hardcoded `S-001..S-006` default was removed when
governance moved to user-authored specs. See docs/design/governance-engine.md.

Both `run_all` and `run_rules` accept either an `OKFContext` or an
`EvaluationContext`.  When passed a bare `OKFContext` they auto-wrap it so that
existing callers (tests, monitor) continue to work without modification.
"""
from __future__ import annotations

from hephaestus.core import Violation
from hephaestus.rules.base import HephaestusRule


def _ensure_eval_ctx(ctx):
    from hephaestus.eval_context import EvaluationContext
    from hephaestus.index import OKFContext
    if isinstance(ctx, EvaluationContext):
        return ctx
    if isinstance(ctx, OKFContext):
        return EvaluationContext(okf=ctx)
    raise TypeError(f"Expected OKFContext or EvaluationContext, got {type(ctx)}")


def run_rules(
    ctx,
    rules: list[HephaestusRule] | None = None,
    enabled: set[str] | None = None,
) -> list[Violation]:
    eval_ctx = _ensure_eval_ctx(ctx)
    rules = rules if rules is not None else []
    out: list[Violation] = []
    for rule in rules:
        if enabled is not None and rule.id not in enabled:
            continue
        out.extend(rule.check(eval_ctx).violations)
    return out


def run_all(ctx, enabled: set[str] | None = None) -> list[Violation]:
    """Schema (Tier 1) load errors + compliance (Tier 2) rule violations."""
    eval_ctx = _ensure_eval_ctx(ctx)
    load_errors = eval_ctx.okf.load_errors
    return list(load_errors) + run_rules(eval_ctx, enabled=enabled)


def run_layer(
    rules: list[HephaestusRule],
    ctx,
    *,
    layer: str,
) -> list[Violation]:
    """Run only rules whose `.layer` matches *layer*."""
    eval_ctx = _ensure_eval_ctx(ctx)
    filtered = [r for r in rules if r.layer == layer]
    return run_rules(eval_ctx, rules=filtered)
