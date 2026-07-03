from __future__ import annotations

import time
from pathlib import Path

import pytest

from hephaestus.store.nodes import create_node
from hephaestus.store.runs import create_run
from hephaestus.store.threads import get_or_create_thread
from hephaestus.store.trace import TraceEvent, append_trace_event, list_trace_events
from hephaestus.integration.providers import _codex_normalize_event
from hephaestus.integration.runners import _extract_target_path


def _db(tmp_path: Path) -> Path:
    return tmp_path / ".hephaestus" / "state.db"


def _setup(tmp_path: Path):
    db = _db(tmp_path)
    node = create_node(db, tmp_path, "Arch", "claude", ["architect"], [])
    thread = get_or_create_thread(db, node_id=node.node_id, name="thread-1")
    run = create_run(db, thread_id=thread.id, node_id=node.node_id, contract={})
    return db, node, thread, run


def test_append_and_list_trace_events(tmp_path):
    db, node, _, run = _setup(tmp_path)

    append_trace_event(db, run_id=run.id, node_id=node.node_id,
                       action="write_file", target_path="foo.py")
    append_trace_event(db, run_id=run.id, node_id=node.node_id,
                       action="read_file", target_path="bar.py")

    events = list_trace_events(db, run_id=run.id)
    assert len(events) == 2
    assert all(isinstance(e, TraceEvent) for e in events)
    assert {e.action for e in events} == {"write_file", "read_file"}


def test_list_filters_by_run_id(tmp_path):
    db, node, thread, run1 = _setup(tmp_path)
    run2 = create_run(db, thread_id=thread.id, node_id=node.node_id, contract={})

    append_trace_event(db, run_id=run1.id, node_id=node.node_id, action="write_file")
    append_trace_event(db, run_id=run2.id, node_id=node.node_id, action="read_file")

    assert len(list_trace_events(db, run_id=run1.id)) == 1
    assert list_trace_events(db, run_id=run1.id)[0].action == "write_file"


def test_list_filters_by_node_id(tmp_path):
    db = _db(tmp_path)
    n1 = create_node(db, tmp_path, "Arch", "claude", ["architect"], [])
    n2 = create_node(db, tmp_path, "Worker", "codex", ["worker"], [])
    t1 = get_or_create_thread(db, node_id=n1.node_id, name="t1")
    t2 = get_or_create_thread(db, node_id=n2.node_id, name="t2")
    r1 = create_run(db, thread_id=t1.id, node_id=n1.node_id, contract={})
    r2 = create_run(db, thread_id=t2.id, node_id=n2.node_id, contract={})

    append_trace_event(db, run_id=r1.id, node_id=n1.node_id, action="write_file")
    append_trace_event(db, run_id=r2.id, node_id=n2.node_id, action="read_file")

    result = list_trace_events(db, node_id=n1.node_id)
    assert len(result) == 1
    assert result[0].node_id == n1.node_id


def test_list_ordered_by_ts(tmp_path):
    db, node, _, run = _setup(tmp_path)

    append_trace_event(db, run_id=run.id, node_id=node.node_id, action="a")
    time.sleep(0.01)
    append_trace_event(db, run_id=run.id, node_id=node.node_id, action="b")
    time.sleep(0.01)
    append_trace_event(db, run_id=run.id, node_id=node.node_id, action="c")

    events = list_trace_events(db, run_id=run.id)
    assert [e.action for e in events] == ["a", "b", "c"]


def test_append_returns_trace_event(tmp_path):
    db, node, _, run = _setup(tmp_path)

    ev = append_trace_event(db, run_id=run.id, node_id=node.node_id,
                            action="bash", target_path="py -m pytest",
                            raw={"cmd": "py -m pytest"})
    assert isinstance(ev, TraceEvent)
    assert ev.action == "bash"
    assert ev.target_path == "py -m pytest"
    assert ev.raw == {"cmd": "py -m pytest"}


def test_list_no_filters_returns_all(tmp_path):
    db, node, _, run = _setup(tmp_path)

    append_trace_event(db, run_id=run.id, node_id=node.node_id, action="write_file")
    append_trace_event(db, run_id=run.id, node_id=node.node_id, action="read_file")

    assert len(list_trace_events(db)) == 2


# ---------- _extract_target_path helpers ----------

def test_extract_target_path_file_path():
    assert _extract_target_path({"file_path": "foo.py"}) == "foo.py"


def test_extract_target_path_path_key():
    assert _extract_target_path({"path": "src/bar.py"}) == "src/bar.py"


def test_extract_target_path_cmd():
    assert _extract_target_path({"cmd": "py -m pytest"}) == "py -m pytest"


def test_extract_target_path_command():
    assert _extract_target_path({"command": "git status"}) == "git status"


def test_extract_target_path_unknown():
    assert _extract_target_path({}) is None
    assert _extract_target_path({"other": "x"}) is None


# ---------- codex function_call event ----------

def test_codex_function_call_emits_tool_call():
    raw = {
        "type": "item.completed",
        "item": {
            "type": "function_call",
            "name": "shell",
            "arguments": {"cmd": "py -m pytest"},
        },
    }
    ev = _codex_normalize_event(raw)
    assert ev.kind == "tool_call"
    assert ev.text == "shell"
    assert ev.raw["action"] == "shell"
    assert ev.raw["input"] == {"cmd": "py -m pytest"}


def test_codex_agent_message_not_tool_call():
    raw = {
        "type": "item.completed",
        "item": {"type": "agent_message", "text": "Hello"},
    }
    ev = _codex_normalize_event(raw)
    assert ev.kind == "text"
