from __future__ import annotations

from hephaestus.dashboard import snapshot


def test_clean_snapshot_has_no_violations(clean_tree):
    snap = snapshot(clean_tree)
    assert snap["summary"]["violations"] == 0
    rows = {r["id"]: r for r in snap["issues"]}
    assert rows["issue-001"]["state"] == "DONE"
    assert all(s == "ok" for s in rows["issue-001"]["stages"].values())
    assert rows["issue-002"]["state"] == "OPEN"


def test_violation_attached_to_issue_row(violations_tree):
    snap = snapshot(violations_tree)
    rows = {r["id"]: r for r in snap["issues"]}
    # issue-010: done, no handoff -> S-002 + HANDOFF_PENDING
    assert "S-002" in rows["issue-010"]["violations"]
    assert rows["issue-010"]["state"] == "HANDOFF_PENDING"
    assert rows["issue-010"]["stages"]["handoff"] == "pending"


def test_summary_counts_both_severities(violations_tree):
    snap = snapshot(violations_tree)
    assert snap["summary"]["error"] >= 1
    assert snap["summary"]["warning"] >= 1
    assert snap["summary"]["issues"] == len(snap["issues"])


def test_snapshot_is_json_serializable(violations_tree):
    import json
    json.dumps(snapshot(violations_tree))  # must not raise
