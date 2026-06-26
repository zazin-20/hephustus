from __future__ import annotations

from hephaestus.core import ViolationResult
from hephaestus.eval_context import EvaluationContext
from hephaestus.index import build_context
from hephaestus.rules.base import HephaestusRule
from hephaestus.rules.registry import run_all, run_layer


def test_eval_context_defaults(tmp_path):
    okf = build_context(tmp_path)
    ctx = EvaluationContext(okf=okf)
    assert ctx.trace == []
    assert ctx.contract == {}
    assert ctx.actor == ""
    assert ctx.scope == ""


def test_run_all_clean_is_empty(clean_tree):
    okf = build_context(clean_tree)
    assert run_all(EvaluationContext(okf=okf)) == []


def test_run_layer_filters_by_layer(tmp_path):
    called_ids: list[str] = []

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

    okf = build_context(tmp_path)
    ctx = EvaluationContext(okf=okf)

    run_layer([TrackingStructural(), TrackingExit()], ctx, layer="structural")
    assert called_ids == ["T-003"]


def test_rule_interface_defaults():
    class R(HephaestusRule):
        id = "T-1"
        name = "t"

        def check(self, ctx):
            return ViolationResult.of([])

    rule = R()
    assert rule.layer == "structural"
    assert rule.trigger == "on_change"
    assert rule.scope == "workspace"
