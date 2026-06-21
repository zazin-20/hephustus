from __future__ import annotations

from hephaestus.monitor import ComplianceMonitor


def test_clean_tree_baseline_is_empty(clean_tree):
    mon = ComplianceMonitor(clean_tree)
    delta = mon.refresh()
    assert delta.added == []
    assert delta.current == []
    assert not delta.changed


def test_no_change_between_refreshes_yields_empty_delta(violations_tree):
    mon = ComplianceMonitor(violations_tree)
    mon.refresh()              # baseline
    again = mon.refresh()      # nothing touched
    assert again.added == []
    assert again.resolved == []
    assert not again.changed
    assert again.current  # violations still present, just unchanged


def test_detects_then_resolves_a_violation(violations_tree, write_okf):
    mon = ComplianceMonitor(violations_tree)
    first = mon.refresh()
    assert first.changed
    assert "S-002" in {v.rule_id for v in first.added}

    # Resolve S-002 for issue-010 by supplying the missing handoff.
    write_okf(
        violations_tree / "agents" / "architect" / "handoffs" / "issue-010.md",
        {"issue_id": "issue-010", "worker": "codex", "status": "complete",
         "created": "2026-06-02", "reviewed_by": "architect"},
    )
    after = mon.refresh()
    assert "S-002" in {v.rule_id for v in after.resolved}
    assert "S-002" not in {v.rule_id for v in after.current}


def test_new_violation_surfaces_as_added(clean_tree, write_okf):
    mon = ComplianceMonitor(clean_tree)
    mon.refresh()  # clean baseline

    # Mark the open issue done with no handoff -> S-002.
    write_okf(
        clean_tree / "agents" / "architect" / "issues" / "issue-002.md",
        {"id": "issue-002", "status": "done", "role": "worker",
         "sprint": "sprint-02", "created": "2026-06-10"},
    )
    delta = mon.refresh()
    assert "S-002" in {v.rule_id for v in delta.added}
