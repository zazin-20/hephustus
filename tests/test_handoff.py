"""Tests for handoff marker parsing and gated Spawn (issue #8)."""
from __future__ import annotations

import json
import pytest
from hephaestus.handoff import (
    HandoffMarker,
    parse_handoff,
    SpawnCard,
    SpawnGating,
    evaluate_spawn_gate,
)
from hephaestus.rules.base import HephaestusRule
from hephaestus.core import Severity, Violation, ViolationResult
from hephaestus.eval_context import EvaluationContext
from hephaestus.index import build_context


# ---------- HandoffMarker parsing ----------

def test_parse_handoff_valid_json():
    text = json.dumps({"handoff": {"role": "qa", "task": "verify issue-008", "issue_id": "issue-008"}})
    marker = parse_handoff(text)
    assert marker is not None
    assert marker.role == "qa"
    assert marker.task == "verify issue-008"
    assert marker.issue_id == "issue-008"


def test_parse_handoff_embedded_mid_text():
    prefix = "All work is done. "
    payload = json.dumps({"handoff": {"role": "architect", "task": "review", "issue_id": "issue-009"}})
    suffix = " Handoff complete."
    marker = parse_handoff(prefix + payload + suffix)
    assert marker is not None
    assert marker.role == "architect"


def test_parse_handoff_returns_none_for_non_handoff_json():
    text = json.dumps({"status": "done", "result": 42})
    assert parse_handoff(text) is None


def test_parse_handoff_returns_none_for_malformed_json():
    assert parse_handoff("{not valid json}") is None


def test_parse_handoff_returns_none_for_plain_text():
    assert parse_handoff("The task is complete. No JSON here.") is None


def test_parse_handoff_missing_required_fields():
    text = json.dumps({"handoff": {"role": "qa"}})  # missing task + issue_id
    marker = parse_handoff(text)
    assert marker is None


def test_parse_handoff_partial_match_prefers_first():
    """When multiple JSON blobs appear, first valid handoff wins."""
    first = json.dumps({"handoff": {"role": "qa", "task": "task-1", "issue_id": "issue-001"}})
    second = json.dumps({"handoff": {"role": "worker", "task": "task-2", "issue_id": "issue-002"}})
    marker = parse_handoff(first + " " + second)
    assert marker is not None
    assert marker.role == "qa"


# ---------- SpawnCard + exit-rule gating ----------

class _PassRule(HephaestusRule):
    id = "E-001"
    name = "always passes"
    layer = "exit"
    scope = "issue"
    def check(self, ctx):
        return ViolationResult.of([])


class _FailRule(HephaestusRule):
    id = "E-002"
    name = "always fails"
    layer = "exit"
    scope = "issue"
    def check(self, ctx):
        return ViolationResult.of([
            Violation(rule_id="E-002", severity=Severity.ERROR,
                      message="exit check failed", artifact="agents/")
        ])


def _ctx(tmp_path):
    okf = build_context(tmp_path)
    return EvaluationContext(okf=okf, trace=[], contract={}, actor="work-001")


def test_evaluate_spawn_gate_all_pass(tmp_path):
    marker = HandoffMarker(role="qa", task="verify", issue_id="issue-008")
    ctx = _ctx(tmp_path)
    card = evaluate_spawn_gate(marker, ctx, exit_rules=[_PassRule()])
    assert card.gating == SpawnGating.GREEN
    assert card.failures == []
    assert card.marker.role == "qa"


def test_evaluate_spawn_gate_failures_amber(tmp_path):
    marker = HandoffMarker(role="qa", task="verify", issue_id="issue-008")
    ctx = _ctx(tmp_path)
    card = evaluate_spawn_gate(marker, ctx, exit_rules=[_PassRule(), _FailRule()])
    assert card.gating == SpawnGating.AMBER
    assert len(card.failures) == 1
    assert card.failures[0].rule_id == "E-002"


def test_evaluate_spawn_gate_no_rules_is_green(tmp_path):
    marker = HandoffMarker(role="worker", task="fix bug", issue_id="issue-010")
    ctx = _ctx(tmp_path)
    card = evaluate_spawn_gate(marker, ctx, exit_rules=[])
    assert card.gating == SpawnGating.GREEN


def test_spawn_card_prefilled_from_marker(tmp_path):
    marker = HandoffMarker(role="qa", task="run full suite", issue_id="issue-008")
    ctx = _ctx(tmp_path)
    card = evaluate_spawn_gate(marker, ctx, exit_rules=[])
    assert card.prefill_role == "qa"
    assert card.prefill_task == "run full suite"


def test_spawn_card_amber_has_fix_hints(tmp_path):
    marker = HandoffMarker(role="qa", task="verify", issue_id="issue-008")
    ctx = _ctx(tmp_path)
    card = evaluate_spawn_gate(marker, ctx, exit_rules=[_FailRule()])
    assert card.gating == SpawnGating.AMBER
    assert card.failures[0].rule_id == "E-002"
