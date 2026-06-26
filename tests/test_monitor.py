from __future__ import annotations

from hephaestus.monitor import ComplianceMonitor


def test_clean_tree_baseline_is_empty(clean_tree):
    mon = ComplianceMonitor(clean_tree)
    delta = mon.refresh()
    assert delta.added == []
    assert delta.current == []
    assert not delta.changed


def test_no_change_between_refreshes_yields_empty_delta(clean_tree):
    mon = ComplianceMonitor(clean_tree)
    mon.refresh()
    again = mon.refresh()
    assert again.added == []
    assert again.resolved == []
    assert not again.changed


def test_detects_then_resolves_a_schema_error(clean_tree):
    mon = ComplianceMonitor(clean_tree)
    mon.refresh()  # clean baseline

    broken = clean_tree / "agents" / "architect" / "issues" / "broken.md"
    broken.write_text("---\nid: x\nunterminated", encoding="utf-8")
    first = mon.refresh()
    assert first.changed
    assert any(v.rule_id == "schema" for v in first.added)

    broken.write_text("---\nid: x\n---\nok\n", encoding="utf-8")
    after = mon.refresh()
    assert any(v.rule_id == "schema" for v in after.resolved)
    assert all(v.rule_id != "schema" for v in after.current)
