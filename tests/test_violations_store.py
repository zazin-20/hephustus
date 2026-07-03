"""Tests for violation attribution persistence (issue #7)."""
from __future__ import annotations

import pytest
from hephaestus.store.db import connect
from hephaestus.store.violations import append_violation, list_violations
from hephaestus.core import Violation, Severity


def _db(tmp_path):
    return connect(tmp_path / ".hephaestus" / "state.db")


def test_append_and_list_violations(tmp_path):
    db = _db(tmp_path)
    v = Violation(
        rule_id="G-001",
        severity=Severity.ERROR,
        message="out of scope write by work-001",
        artifact="hephaestus/core.py",
        fix_hint="restrict to agents/",
    )
    append_violation(db, v, run_id="run-abc", node_id="node-001")
    rows = list_violations(db)
    assert len(rows) == 1
    row = rows[0]
    assert row["rule_id"] == "G-001"
    assert row["run_id"] == "run-abc"
    assert row["node_id"] == "node-001"
    assert row["message"] == "out of scope write by work-001"


def test_list_violations_filters_by_run_id(tmp_path):
    db = _db(tmp_path)
    v1 = Violation(rule_id="G-001", severity=Severity.ERROR, message="a", artifact="f")
    v2 = Violation(rule_id="G-002", severity=Severity.WARNING, message="b", artifact="g")
    append_violation(db, v1, run_id="run-1", node_id="node-001")
    append_violation(db, v2, run_id="run-2", node_id="node-002")
    rows = list_violations(db, run_id="run-1")
    assert len(rows) == 1
    assert rows[0]["rule_id"] == "G-001"


def test_list_violations_filters_by_node_id(tmp_path):
    db = _db(tmp_path)
    v1 = Violation(rule_id="G-001", severity=Severity.ERROR, message="a", artifact="f")
    v2 = Violation(rule_id="G-002", severity=Severity.WARNING, message="b", artifact="g")
    append_violation(db, v1, run_id="run-1", node_id="node-001")
    append_violation(db, v2, run_id="run-2", node_id="node-002")
    rows = list_violations(db, node_id="node-002")
    assert len(rows) == 1
    assert rows[0]["rule_id"] == "G-002"


def test_append_violation_returns_row_id(tmp_path):
    db = _db(tmp_path)
    v = Violation(rule_id="G-001", severity=Severity.ERROR, message="x", artifact="f")
    row_id = append_violation(db, v, run_id="run-1", node_id="node-001")
    assert isinstance(row_id, int)
    assert row_id > 0
