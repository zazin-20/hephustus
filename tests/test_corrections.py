from __future__ import annotations

from pathlib import Path

import pytest

from hephaestus.store.corrections import append_correction, list_corrections, promote_correction
from hephaestus.store.db import connect
from hephaestus.store.frozen_rules import ScopeAddress, list_frozen_rules_for_address


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


def test_promote_correction_supersedes_prior_rule_and_records_provenance(tmp_path):
    db = make_db(tmp_path)

    first = append_correction(
        db,
        node_id="node-001",
        note="Use the workspace venv interpreter.",
        source_kind="distillation_candidate",
        topic_key="python-invocation",
        candidate_scope="machine",
        trace_event_id="trace-001",
        source_run_id="run-001",
        source_node_id="node-001",
    )
    first_rule = promote_correction(
        db,
        first.id,
        confirmer="alice",
        machine="workspace-a",
    )

    second = append_correction(
        db,
        node_id="node-001",
        note="Use the workspace venv interpreter and never bare python.",
        source_kind="distillation_candidate",
        topic_key="python-invocation",
        candidate_scope="machine",
        trace_event_id="trace-002",
        source_run_id="run-002",
        source_node_id="node-001",
    )
    second_rule = promote_correction(
        db,
        second.id,
        confirmer="bob",
        machine="workspace-a",
    )

    active = list_frozen_rules_for_address(
        db,
        ScopeAddress(
            machine="workspace-a",
            workflow_id=None,
            workflow_run_id=None,
            placement_id=None,
            node_id="node-001",
            tags=["worker"],
        ),
    )

    assert [rule.id for rule in active] == [second_rule.id]
    assert active[0].body == "Use the workspace venv interpreter and never bare python."

    with connect(db) as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                body,
                disabled_at,
                superseded_by_rule_id,
                source_correction_id,
                source_trace_event_id,
                source_run_id,
                confirmer,
                confirmed_at
            FROM frozen_rules
            WHERE topic_key = ?
            ORDER BY created_at ASC
            """,
            ("python-invocation",),
        ).fetchall()

    assert len(rows) == 2

    assert rows[0][0] == first_rule.id
    assert rows[0][1] == "Use the workspace venv interpreter."
    assert rows[0][2] is not None
    assert rows[0][3] == second_rule.id
    assert rows[0][4] == first.id
    assert rows[0][5] == "trace-001"
    assert rows[0][6] == "run-001"
    assert rows[0][7] == "alice"
    assert rows[0][8] is not None

    assert rows[1][0] == second_rule.id
    assert rows[1][2] is None
    assert rows[1][4] == second.id
    assert rows[1][5] == "trace-002"
    assert rows[1][6] == "run-002"
    assert rows[1][7] == "bob"
    assert rows[1][8] is not None
