from __future__ import annotations

import json

import pytest

from hephaestus.okf_layout import OKFLayout
from hephaestus.store.db import connect
from hephaestus.store.runs import create_run
from hephaestus.store.threads import append_turn, get_or_create_thread
from hephaestus.store.nodes import (
    create_node,
    delete_node,
    get_node,
    list_nodes,
)


def make_db_path(tmp_path):
    return tmp_path / ".hephaestus" / "state.db"


def test_create_node_returns_node_with_governance_fields(tmp_path):
    db_path = make_db_path(tmp_path)

    node = create_node(
        db_path,
        tmp_path,
        name="Architecture Lead",
        provider="claude",
        tags=["architect", "design"],
        rules=["S-001", "S-002"],
        inputs=["artifact:prd"],
        outputs=["artifact:adr"],
        skills=["skill:grill-me"],
        allowed_paths=["agents/architect"],
        allowed_tools=["read_file", "write_file"],
        context_policy="inputs-only",
    )

    assert node.node_id == "node-001"
    assert node.name == "Architecture Lead"
    assert node.provider == "claude"
    assert node.tags == ["architect", "design"]
    assert node.rules == ["S-001", "S-002"]
    assert node.inputs == ["artifact:prd"]
    assert node.outputs == ["artifact:adr"]
    assert node.skills == ["skill:grill-me"]
    assert node.allowed_paths == ["agents/architect"]
    assert node.allowed_tools == ["read_file", "write_file"]
    assert node.context_policy == "inputs-only"
    assert node.created_at.endswith("Z")


def test_node_id_increments_globally(tmp_path):
    db_path = make_db_path(tmp_path)

    first = create_node(db_path, tmp_path, "Architect One", "claude", ["architect"], [])
    second = create_node(db_path, tmp_path, "Worker One", "codex", ["worker"], [])

    assert first.node_id == "node-001"
    assert second.node_id == "node-002"


def test_list_nodes_returns_all(tmp_path):
    db_path = make_db_path(tmp_path)
    first = create_node(db_path, tmp_path, "Architect One", "claude", ["architect"], ["S-001"])
    second = create_node(db_path, tmp_path, "Worker One", "codex", ["worker"], ["S-002"])

    nodes = list_nodes(db_path)

    assert [node.node_id for node in nodes] == [first.node_id, second.node_id]


def test_get_node_returns_correct(tmp_path):
    db_path = make_db_path(tmp_path)
    created = create_node(db_path, tmp_path, "QA One", "claude", ["qa"], ["S-003"])

    node = get_node(db_path, created.node_id)

    assert node == created


def test_get_node_raises_keyerror_for_missing(tmp_path):
    db_path = make_db_path(tmp_path)
    with connect(db_path):
        pass

    with pytest.raises(KeyError):
        get_node(db_path, "node-999")


def test_delete_removes_node(tmp_path):
    db_path = make_db_path(tmp_path)
    created = create_node(db_path, tmp_path, "Worker One", "codex", ["worker"], [])

    delete_node(db_path, created.node_id, tmp_path)

    assert list_nodes(db_path) == []


def test_delete_node_cascades_runtime_rows_and_identity_card(tmp_path):
    db_path = make_db_path(tmp_path)
    created = create_node(db_path, tmp_path, "Worker One", "codex", ["worker"], [])
    thread = get_or_create_thread(
        db_path,
        node_id=created.node_id,
        name="workflow-run-003",
        workflow_run_id="workflow-run-003",
        placement_id="implement",
    )
    run = create_run(
        db_path,
        thread_id=thread.id,
        node_id=created.node_id,
        contract={"node_id": created.node_id},
    )
    append_turn(db_path, thread.id, role="user", text="hello", kind="text", run_id=run.id)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO trace_events(id, run_id, node_id, ts, action, target_path, raw)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("trace-001", run.id, created.node_id, "2026-06-22T00:00:00Z", "write_file", "foo.py", "{}"),
        )
        conn.commit()

    delete_node(db_path, created.node_id, tmp_path)

    with connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM nodes").fetchone() == (0,)
        assert conn.execute("SELECT COUNT(*) FROM threads").fetchone() == (0,)
        assert conn.execute("SELECT COUNT(*) FROM runs").fetchone() == (0,)
        assert conn.execute("SELECT COUNT(*) FROM turns").fetchone() == (0,)
        assert conn.execute("SELECT COUNT(*) FROM trace_events").fetchone() == (0,)
    assert not (tmp_path / "agents" / "identities" / f"{created.node_id}.json").exists()


def test_delete_node_accepts_agents_root_for_identity_cleanup(tmp_path):
    db_path = make_db_path(tmp_path)
    created = create_node(db_path, tmp_path, "Worker One", "codex", ["worker"], [])

    delete_node(db_path, created.node_id, tmp_path / "agents")

    assert not (tmp_path / "agents" / "identities" / f"{created.node_id}.json").exists()


def test_optional_fields_default_to_none_or_empty(tmp_path):
    db_path = make_db_path(tmp_path)

    node = create_node(db_path, tmp_path, "Worker One", "codex", ["worker"], [])

    assert node.model is None
    assert node.effort is None
    assert node.working_dir is None
    assert node.inputs == []
    assert node.outputs == []
    assert node.skills == []
    assert node.allowed_paths == []
    assert node.allowed_tools == []
    assert node.context_policy is None


def test_identity_card_written_on_create(tmp_path):
    db_path = make_db_path(tmp_path)

    created = create_node(db_path, tmp_path, "Architect One", "claude", ["architect"], ["S-001"])
    card_path = tmp_path / "agents" / "identities" / f"{created.node_id}.json"

    assert card_path.exists()


def test_create_node_accepts_agents_root_for_identity_card(tmp_path):
    db_path = make_db_path(tmp_path)
    agents_root = tmp_path / "agents"

    created = create_node(db_path, agents_root, "Architect One", "claude", ["architect"], ["S-001"])

    assert OKFLayout.for_existing_root(agents_root).identity_card_path(created.node_id).exists()


def test_identity_card_has_correct_fields(tmp_path):
    db_path = make_db_path(tmp_path)

    created = create_node(
        db_path,
        tmp_path,
        name="Orchestrator One",
        provider="claude",
        tags=["orchestrator", "planner"],
        rules=["S-009"],
    )
    card_path = tmp_path / "agents" / "identities" / f"{created.node_id}.json"

    payload = json.loads(card_path.read_text(encoding="utf-8"))

    assert payload == {
        "node_id": created.node_id,
        "name": "Orchestrator One",
        "tags": ["orchestrator", "planner"],
        "created_at": created.created_at,
        "capabilities": ["plan", "write_handoff"],
        "sessions": [],
    }
