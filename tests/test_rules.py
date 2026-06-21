from __future__ import annotations

from hephaestus.core import Severity
from hephaestus.index import build_context
from hephaestus.rules.registry import run_all, run_rules


def _rule_ids(violations):
    return {v.rule_id for v in violations}


def test_clean_tree_has_no_violations(clean_tree):
    ctx = build_context(clean_tree)
    assert ctx.load_errors == []
    assert run_all(ctx) == []


def test_clean_tree_index_loaded(clean_tree):
    ctx = build_context(clean_tree)
    assert len(ctx.issues) == 2
    assert len(ctx.handoffs) == 1
    assert len(ctx.qa_evidence) == 1
    assert len(ctx.log_entries) == 1
    assert [r.id for r in ctx.issues_index.open_issues] == ["issue-002"]


def test_violations_tree_triggers_each_rule(violations_tree):
    ctx = build_context(violations_tree)
    found = _rule_ids(run_rules(ctx))
    for rule_id in ("S-001", "S-002", "S-003", "S-004", "S-005", "S-006"):
        assert rule_id in found, f"expected {rule_id} to fire"


def test_severities_are_set(violations_tree):
    ctx = build_context(violations_tree)
    by_id = {v.rule_id: v for v in run_rules(ctx)}
    assert by_id["S-002"].severity is Severity.ERROR
    assert by_id["S-004"].severity is Severity.WARNING
    assert by_id["S-006"].severity is Severity.WARNING


def test_schema_error_surfaces_as_load_error(tmp_path):
    bad = tmp_path / "agents" / "architect" / "issues" / "issue-x.md"
    bad.parent.mkdir(parents=True)
    bad.write_text("---\nid: issue-x\nstatus: open\n---\n", encoding="utf-8")  # missing role/sprint/created
    ctx = build_context(tmp_path)
    assert any(v.rule_id == "schema" for v in ctx.load_errors)
    assert any(v.rule_id == "schema" for v in run_all(ctx))
