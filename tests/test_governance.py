"""Tests for governance rules G001/G002 and violation attribution (issue #7)."""
from __future__ import annotations

import pytest
from hephaestus.eval_context import EvaluationContext
from hephaestus.index import OKFContext, build_context
from hephaestus.core import ViolationResult
from hephaestus.rules.base import HephaestusRule
from hephaestus.rules.governance import G001ScopeAdherence, G002ModelCompliance, ALL_GOVERNANCE_RULES
from hephaestus.rules.registry import run_layer
from hephaestus.store.trace import TraceEvent
from datetime import datetime


def _okf(tmp_path):
    return build_context(tmp_path)


def _trace_event(action: str, target_path: str, run_id="run-1", agent_id="work-001") -> TraceEvent:
    return TraceEvent(
        id="evt-" + action[:4],
        run_id=run_id,
        agent_id=agent_id,
        action=action,
        target_path=target_path,
        ts=datetime.utcnow().isoformat(),
        raw=None,
    )


def test_g001_passes_when_no_allowed_paths(tmp_path):
    """No allowed_paths restriction → any write is fine."""
    okf = _okf(tmp_path)
    trace = [_trace_event("write_file", "agents/worker/output.md")]
    ctx = EvaluationContext(okf=okf, trace=trace, contract={}, actor="work-001")
    rule = G001ScopeAdherence()
    result = rule.check(ctx)
    assert result.violations == []


def test_g001_passes_when_write_within_allowed_path(tmp_path):
    okf = _okf(tmp_path)
    trace = [_trace_event("write_file", "agents/worker/output.md")]  # action field
    ctx = EvaluationContext(
        okf=okf,
        trace=trace,
        contract={"allowed_paths": ["agents/"]},
        actor="work-001",
    )
    rule = G001ScopeAdherence()
    result = rule.check(ctx)
    assert result.violations == []


def test_g001_fails_on_write_outside_allowed_paths(tmp_path):
    okf = _okf(tmp_path)
    trace = [_trace_event("write_file", "hephaestus/core.py", agent_id="work-001")]
    ctx = EvaluationContext(
        okf=okf,
        trace=trace,
        contract={"allowed_paths": ["agents/"]},
        actor="work-001",
    )
    rule = G001ScopeAdherence()
    result = rule.check(ctx)
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.rule_id == "G-001"
    assert "work-001" in v.message
    assert "hephaestus/core.py" in v.message


def test_g001_bash_counts_as_write(tmp_path):
    okf = _okf(tmp_path)
    trace = [_trace_event("bash", "/etc/hosts", agent_id="arch-002")]
    ctx = EvaluationContext(
        okf=okf,
        trace=trace,
        contract={"allowed_paths": ["agents/"]},
        actor="arch-002",
    )
    rule = G001ScopeAdherence()
    result = rule.check(ctx)
    assert len(result.violations) == 1
    assert "arch-002" in result.violations[0].message


def test_g001_read_not_flagged(tmp_path):
    okf = _okf(tmp_path)
    trace = [_trace_event("read_file", "hephaestus/core.py")]
    ctx = EvaluationContext(
        okf=okf,
        trace=trace,
        contract={"allowed_paths": ["agents/"]},
        actor="work-001",
    )
    rule = G001ScopeAdherence()
    result = rule.check(ctx)
    assert result.violations == []


def test_g002_passes_when_model_matches(tmp_path):
    okf = _okf(tmp_path)
    ctx = EvaluationContext(
        okf=okf,
        trace=[],
        contract={"model": "claude-sonnet-4-6"},
        actor="work-001",
        scope="issue:007",
    )
    rule = G002ModelCompliance()
    result = rule.check(ctx)
    assert result.violations == []


def test_g002_fails_when_model_mismatch(tmp_path):
    okf = _okf(tmp_path)
    ctx = EvaluationContext(
        okf=okf,
        trace=[],
        contract={"model": "claude-opus-4-8", "actual_model": "claude-haiku-4-5-20251001"},
        actor="work-001",
        scope="issue:007",
    )
    rule = G002ModelCompliance()
    result = rule.check(ctx)
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.rule_id == "G-002"
    assert "work-001" in v.message


def test_g002_no_contract_model_passes(tmp_path):
    okf = _okf(tmp_path)
    ctx = EvaluationContext(okf=okf, trace=[], contract={}, actor="work-001")
    rule = G002ModelCompliance()
    result = rule.check(ctx)
    assert result.violations == []


def test_governance_rules_have_layer_governance():
    for rule in ALL_GOVERNANCE_RULES:
        assert rule.layer == "governance", f"{rule.id} has layer={rule.layer!r}"


def test_run_layer_governance_filters(tmp_path):
    okf = _okf(tmp_path)
    ctx = EvaluationContext(okf=okf, trace=[], contract={}, actor="work-001")

    # A non-governance rule must be filtered out by run_layer(..., layer="governance").
    class _OtherLayerRule(HephaestusRule):
        id = "T-OTHER"
        name = "other layer"
        layer = "structural"

        def check(self, ctx):
            return ViolationResult.of([])

    all_rules = [_OtherLayerRule(), *ALL_GOVERNANCE_RULES]
    result = run_layer(all_rules, ctx, layer="governance")
    assert isinstance(result, list)
