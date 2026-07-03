"""Tests for handoff marker parsing and gated Spawn (issue #8)."""
from __future__ import annotations

import json
import pytest
from hephaestus.handoff import (
    DistillationCandidateMarker,
    HandoffMarker,
    SkillCompleteMarker,
    parse_handoff,
    parse_marker,
    parse_marker_from_trace,
    parse_marker_from_turns,
    SpawnCard,
    SpawnGating,
    evaluate_spawn_gate,
)
from hephaestus.rules.base import HephaestusRule
from hephaestus.core import Severity, Violation, ViolationResult
from hephaestus.eval_context import EvaluationContext
from hephaestus.index import build_context
from hephaestus.store.threads import Turn
from hephaestus.store.trace import TraceEvent


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


def test_parse_handoff_protocol_marker():
    text = '\n'.join([
        "Implementation complete.",
        '@@HEPHAESTUS@@ {"v":1,"type":"handoff","role":"qa","task":"verify issue-017","issue_id":"issue-017"}',
    ])
    marker = parse_handoff(text)
    assert marker == HandoffMarker(role="qa", task="verify issue-017", issue_id="issue-017")


def test_parse_marker_handoff_protocol():
    text = '\n'.join([
        "Implementation complete.",
        '@@HEPHAESTUS@@ {"v":1,"type":"handoff","role":"qa","task":"verify issue-017","issue_id":"issue-017"}',
    ])
    marker = parse_marker(text)
    assert marker == HandoffMarker(role="qa", task="verify issue-017", issue_id="issue-017")


def test_parse_marker_skill_complete_protocol():
    marker = parse_marker(
        '@@HEPHAESTUS@@ {"v":1,"type":"skill_complete","skill":"grill-me","ok":true}'
    )
    assert marker == SkillCompleteMarker(skill="grill-me", ok=True)


def test_parse_marker_distillation_candidate_protocol():
    marker = parse_marker(
        '@@HEPHAESTUS@@ {"v":1,"type":"distillation_candidate","topic_key":"gh-auth","scope":"machine","directive":"Use gh auth status before fetching issues."}'
    )
    assert marker == DistillationCandidateMarker(
        topic_key="gh-auth",
        scope="machine",
        directive="Use gh auth status before fetching issues.",
    )


def test_parse_marker_malformed_skipped_first_valid_wins():
    text = '\n'.join([
        '@@HEPHAESTUS@@ {"v":1,"type":"skill_complete","skill":"grill-me","ok":"yes"}',
        '@@HEPHAESTUS@@ {"v":1,"type":"handoff","role":"qa","task":"verify issue-017","issue_id":"issue-017"}',
        '@@HEPHAESTUS@@ {"v":1,"type":"skill_complete","skill":"later","ok":true}',
    ])
    marker = parse_marker(text)
    assert marker == HandoffMarker(role="qa", task="verify issue-017", issue_id="issue-017")


def test_parse_marker_ignores_in_prose_mentions():
    text = 'Please do not emit @@HEPHAESTUS@@ {"v":1,"type":"handoff","role":"qa","task":"verify","issue_id":"issue-017"} in prose.'
    assert parse_marker(text) is None


def test_parse_marker_from_turns_ignores_thinking_turns():
    turns = [
        Turn(
            id="turn-1",
            thread_id="thread-1",
            run_id="run-1",
            seq=1,
            role="assistant",
            kind="thinking",
            text='@@HEPHAESTUS@@ {"v":1,"type":"skill_complete","skill":"grill-me","ok":true}',
            included=True,
            created_at="2026-07-03T00:00:00Z",
        ),
        Turn(
            id="turn-2",
            thread_id="thread-1",
            run_id="run-1",
            seq=2,
            role="assistant",
            kind="text",
            text='@@HEPHAESTUS@@ {"v":1,"type":"handoff","role":"qa","task":"verify issue-017","issue_id":"issue-017"}',
            included=True,
            created_at="2026-07-03T00:00:01Z",
        ),
    ]
    marker = parse_marker_from_turns(turns)
    assert marker == HandoffMarker(role="qa", task="verify issue-017", issue_id="issue-017")


def test_parse_marker_from_trace_scans_tool_command_strings():
    trace = [
        TraceEvent(
            id="trace-1",
            run_id="run-1",
            agent_id="worker-1",
            ts="2026-07-03T00:00:00Z",
            action="shell",
            target_path=None,
            raw={"action": "shell", "input": {"command": "echo ok"}},
        ),
        TraceEvent(
            id="trace-2",
            run_id="run-1",
            agent_id="worker-1",
            ts="2026-07-03T00:00:01Z",
            action="shell",
            target_path=None,
            raw={
                "action": "shell",
                "input": {
                    "command": '\n@@HEPHAESTUS@@ {"v":1,"type":"skill_complete","skill":"grill-me","ok":true}\n',
                },
            },
        ),
    ]
    marker = parse_marker_from_trace(trace)
    assert marker == SkillCompleteMarker(skill="grill-me", ok=True)


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
