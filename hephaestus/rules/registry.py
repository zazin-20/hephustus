"""Rule registry and runner.

`run_rules` executes the structural rules; `run_all` also surfaces Tier-1 schema
load errors collected while building the index, so a single call returns every
problem in the tree.

Both `run_all` and `run_rules` accept either an `OKFContext` or an
`EvaluationContext`.  When passed a bare `OKFContext` they auto-wrap it so that
existing callers (tests, monitor) continue to work without modification.
"""
from __future__ import annotations

from hephaestus.core import Violation
from hephaestus.rules.base import HephaestusRule
from hephaestus.rules.structural import ALL_STRUCTURAL_RULES


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
    rules = rules if rules is not None else ALL_STRUCTURAL_RULES
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
