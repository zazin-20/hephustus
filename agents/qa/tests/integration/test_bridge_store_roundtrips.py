"""Desktop Bridge integration — store round-trips over a temp workspace.

Exercises the app-bound `hephaestus.desktop.Bridge` methods that read/write the
SQLite state DB and the OKF tree. Each test runs against a throwaway
``DesktopApp(tmp_path)`` — no browser, no live LLM calls.

Run (from repo root)::

    agents/.venv/Scripts/python.exe -m pytest agents/qa/tests -q

Catalog cases covered: TC-DESK-003, TC-DESK-004, TC-DESK-008, TC-DESK-011,
TC-WF-001 (via the bridge), TC-STORE-005/007 (thread/turn round-trip via the
bridge).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from hephaestus.store.threads import append_turn, get_or_create_thread


# --- Node lifecycle (TC-DESK-003) -------------------------------------------

def test_create_list_delete_node_round_trip(app):
    created = app._bridge.create_node("Worker", "claude", ["worker"], [])
    node_id = created["node_id"]
    assert created["status"] == "idle"

    listed = app._bridge.list_nodes()
    assert node_id in {node["node_id"] for node in listed}
    assert all(node["status"] == "idle" for node in listed)

    app._bridge.delete_node(node_id)
    assert node_id not in {node["node_id"] for node in app._bridge.list_nodes()}


# --- Thread / turn transcript (TC-STORE-005/007 via bridge) -----------------

def test_list_threads_and_transcript_round_trip(app):
    node = app._bridge.create_node("Architect", "claude", ["architect"], [])
    thread = get_or_create_thread(
        app._workspace.state_db_path,
        node_id=node["node_id"],
        name="issue-1",
        issue_id="issue-1",
    )
    append_turn(app._workspace.state_db_path, thread.id, role="user", kind="text", text="hello")
    append_turn(app._workspace.state_db_path, thread.id, role="assistant", kind="text", text="world")

    threads = app._bridge.list_threads(node["node_id"])
    assert thread.id in {row["id"] for row in threads}

    transcript = app._bridge.get_transcript(thread.id)
    assert [turn["text"] for turn in transcript] == ["hello", "world"]

    # set_turn_included soft-excludes a turn; still present in transcript but flagged.
    second = transcript[1]
    app._bridge.set_turn_included(second["id"], False)
    after = app._bridge.get_transcript(thread.id)
    assert after[1]["included"] is False
    # reversible
    app._bridge.set_turn_included(second["id"], True)
    assert app._bridge.get_transcript(thread.id)[1]["included"] is True


# --- Workflow persistence (TC-DESK-004 / TC-WF-001 via bridge) --------------

def test_save_and_list_workflow_round_trip(app):
    payload = {
        "workflow_id": "issue-100",
        "placements": [
            {"placement_id": "draft", "node_id": "node-001", "x": 10, "y": 20, "interactivity": "afk"}
        ],
        "edges": [],
    }
    saved = app._bridge.save_workflow(payload)
    assert Path(saved["path"]).as_posix().endswith("agents/workflows/issue-100.yaml")

    workflows = app._bridge.list_workflows()
    ids = {wf["workflow_id"] for wf in workflows}
    assert "issue-100" in ids


# --- Corrections queue (TC-DESK-008) ----------------------------------------

def test_save_and_get_corrections_round_trip(app):
    node = app._bridge.create_node("QA", "claude", ["qa"], [])
    saved = app._bridge.save_correction(None, node["node_id"], "issue-7", "prefer smaller diffs")
    assert saved["note"] == "prefer smaller diffs"
    assert saved["node_id"] == node["node_id"]

    listed = app._bridge.get_corrections(node_id=node["node_id"])
    assert [c["note"] for c in listed] == ["prefer smaller diffs"]
    assert listed[0]["issue_id"] == "issue-7"


# --- Guard: unbound bridge (TC-DESK-011) ------------------------------------

def test_store_methods_require_bound_app(tmp_path):
    from hephaestus.desktop import Bridge

    bridge = Bridge(tmp_path, [])   # app=None
    with pytest.raises(RuntimeError, match="no app bound"):
        bridge.list_nodes()
    with pytest.raises(RuntimeError, match="no app bound"):
        bridge.list_threads("node-001")
