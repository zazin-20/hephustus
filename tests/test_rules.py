from __future__ import annotations

from hephaestus.core import Severity, Violation, ViolationResult
from hephaestus.index import build_context
from hephaestus.rules.base import HephaestusRule
from hephaestus.rules.registry import run_all, run_rules


class _SampleRule(HephaestusRule):
    id = "T-001"
    name = "sample"

    def check(self, ctx):
        return ViolationResult.of(
            [Violation(rule_id=self.id, severity=Severity.ERROR, message="boom", artifact="x")]
        )


def test_no_builtin_rules_clean_tree(clean_tree):
    ctx = build_context(clean_tree)
    assert ctx.load_errors == []
    assert run_rules(ctx) == []   # no built-in rule set anymore
    assert run_all(ctx) == []


def test_run_rules_executes_supplied_rules(clean_tree):
    ctx = build_context(clean_tree)
    out = run_rules(ctx, rules=[_SampleRule()])
    assert {v.rule_id for v in out} == {"T-001"}


def test_run_rules_honors_enabled_filter(clean_tree):
    ctx = build_context(clean_tree)
    assert run_rules(ctx, rules=[_SampleRule()], enabled=set()) == []
    assert run_rules(ctx, rules=[_SampleRule()], enabled={"T-001"})


def test_schema_error_surfaces_as_load_error(schema_error_tree):
    ctx = build_context(schema_error_tree)
    assert any(v.rule_id == "schema" for v in ctx.load_errors)
    assert any(v.rule_id == "schema" for v in run_all(ctx))
