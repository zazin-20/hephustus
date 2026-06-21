"""Rule registry and runner.

`run_rules` executes the structural rules; `run_all` also surfaces Tier-1 schema
load errors collected while building the index, so a single call returns every
problem in the tree.
"""
from __future__ import annotations

from hephaestus.core import Violation
from hephaestus.index import OKFContext
from hephaestus.rules.base import HephaestusRule
from hephaestus.rules.structural import ALL_STRUCTURAL_RULES


def run_rules(
    ctx: OKFContext,
    rules: list[HephaestusRule] | None = None,
    enabled: set[str] | None = None,
) -> list[Violation]:
    rules = rules if rules is not None else ALL_STRUCTURAL_RULES
    out: list[Violation] = []
    for rule in rules:
        if enabled is not None and rule.id not in enabled:
            continue
        out.extend(rule.check(ctx).violations)
    return out


def run_all(ctx: OKFContext, enabled: set[str] | None = None) -> list[Violation]:
    """Schema (Tier 1) load errors + compliance (Tier 2) rule violations."""
    return list(ctx.load_errors) + run_rules(ctx, enabled=enabled)
