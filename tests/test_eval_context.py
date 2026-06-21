from __future__ import annotations

from hephaestus.core import Severity, ViolationResult
from hephaestus.eval_context import EvaluationContext
from hephaestus.index import OKFContext, build_context
from hephaestus.rules.base import HephaestusRule
from hephaestus.rules.registry import run_all, run_layer
from hephaestus.rules.structural import S001WorkerNeedsSpec
from pathlib import Path


def test_eval_context_defaults(tmp_path):
    okf = build_context(tmp_path)
    ctx = EvaluationContext(okf=okf)
    assert ctx.trace == []
    assert ctx.contract == {}
    assert ctx.actor == ""
    assert ctx.scope == ""


def test_structural_rules_pass_through_eval_context(clean_tree):
    okf = build_context(clean_tree)
    ctx = EvaluationContext(okf=okf)
    assert run_all(ctx) == []


def test_structural_rules_detect_violation_through_eval_context(violations_tree):
    okf = build_context(violations_tree)
    ctx = EvaluationContext(okf=okf)
    violations = run_all(ctx)
    rule_ids = {v.rule_id for v in violations}
    for expected in ("S-001", "S-002", "S-003", "S-004", "S-005", "S-006"):
        assert expected in rule_ids


def test_run_layer_filters_by_layer(tmp_path):
    class StructuralRule(HephaestusRule):
        id = "T-001"
        name = "test structural"
        layer = "structural"
        def check(self, ctx):
            return ViolationResult.of([])

    class ExitRule(HephaestusRule):
        id = "T-002"
        name = "test exit"
        layer = "exit"
        def check(self, ctx):
            return ViolationResult.of([])

    rules = [StructuralRule(), ExitRule()]
    okf = build_context(tmp_path)
    ctx = EvaluationContext(okf=okf)

    result = run_layer(rules, ctx, layer="structural")
    assert result == []  # no violations — just verifying it ran without error

    called_ids = []

    class TrackingStructural(HephaestusRule):
        id = "T-003"
        name = "tracking structural"
        layer = "structural"
        def check(self, ctx):
            called_ids.append(self.id)
            return ViolationResult.of([])

    class TrackingExit(HephaestusRule):
        id = "T-004"
        name = "tracking exit"
        layer = "exit"
        def check(self, ctx):
            called_ids.append(self.id)
            return ViolationResult.of([])

    tracking = [TrackingStructural(), TrackingExit()]
    run_layer(tracking, ctx, layer="structural")
    assert called_ids == ["T-003"]


def test_rule_layer_defaults():
    rule = S001WorkerNeedsSpec()
    assert rule.layer == "structural"
    assert rule.trigger == "on_change"
    assert rule.scope == "workspace"
