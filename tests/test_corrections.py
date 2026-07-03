from __future__ import annotations

from pathlib import Path

import pytest

from hephaestus.store.corrections import append_correction, list_corrections


def make_db(tmp_path: Path) -> Path:
    return tmp_path / ".hephaestus" / "state.db"


def test_append_correction_returns_correction(tmp_path):
    db = make_db(tmp_path)
    # violation_id is FK to violations; pass None to avoid needing a real violation row
    c = append_correction(db, node_id="node-001", issue_id="issue-003", note="Fix this")
    assert c.id
    assert c.violation_id is None
    assert c.node_id == "node-001"
    assert c.issue_id == "issue-003"
    assert c.note == "Fix this"
    assert c.created_at


def test_list_corrections_returns_all(tmp_path):
    db = make_db(tmp_path)
    append_correction(db, note="one")
    append_correction(db, note="two")
    append_correction(db, note="three")
    assert len(list_corrections(db)) == 3


def test_list_corrections_filters_by_node_id(tmp_path):
    db = make_db(tmp_path)
    append_correction(db, node_id="node-001", note="a")
    append_correction(db, node_id="node-002", note="b")
    result = list_corrections(db, node_id="node-001")
    assert len(result) == 1
    assert result[0].node_id == "node-001"


def test_list_corrections_filters_by_issue_id(tmp_path):
    db = make_db(tmp_path)
    append_correction(db, issue_id="issue-003", note="x")
    append_correction(db, issue_id="issue-004", note="y")
    result = list_corrections(db, issue_id="issue-003")
    assert len(result) == 1
    assert result[0].issue_id == "issue-003"


def test_correction_without_violation_id(tmp_path):
    db = make_db(tmp_path)
    c = append_correction(db, note="no violation ref")
    assert c.violation_id is None
    assert c.note == "no violation ref"


def test_corrections_ordered_by_created_at(tmp_path):
    db = make_db(tmp_path)
    append_correction(db, note="first")
    append_correction(db, note="second")
    append_correction(db, note="third")
    result = list_corrections(db)
    assert [r.note for r in result] == ["first", "second", "third"]
