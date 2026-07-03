from __future__ import annotations

import time
from pathlib import Path

import pytest

from hephaestus.store.db import connect
from hephaestus.store.runs import create_run
from hephaestus.store.threads import get_or_create_thread
from hephaestus.store.profiles import create_profile
from hephaestus.store.trace import TraceEvent, append_trace_event, list_trace_events
from hephaestus.integration.providers import _codex_normalize_event
from hephaestus.integration.runners import _extract_target_path


def _db(tmp_path: Path) -> Path:
    return tmp_path / ".hephaestus" / "state.db"


def _setup(tmp_path: Path):
    db = _db(tmp_path)
    profile = create_profile(db, tmp_path, "Arch", "architect", [])
    thread = get_or_create_thread(db, agent_id=profile.agent_id, name="thread-1")
    run = create_run(db, thread_id=thread.id, agent_id=profile.agent_id, contract={})
    return db, profile, thread, run


def test_append_and_list_trace_events(tmp_path):
    db, profile, _, run = _setup(tmp_path)

    append_trace_event(db, run_id=run.id, agent_id=profile.agent_id,
                       action="write_file", target_path="foo.py")
    append_trace_event(db, run_id=run.id, agent_id=profile.agent_id,
                       action="read_file", target_path="bar.py")

    events = list_trace_events(db, run_id=run.id)
    assert len(events) == 2
    assert all(isinstance(e, TraceEvent) for e in events)
    assert {e.action for e in events} == {"write_file", "read_file"}


def test_list_filters_by_run_id(tmp_path):
    db, profile, thread, run1 = _setup(tmp_path)
    run2 = create_run(db, thread_id=thread.id, agent_id=profile.agent_id, contract={})

    append_trace_event(db, run_id=run1.id, agent_id=profile.agent_id, action="write_file")
    append_trace_event(db, run_id=run2.id, agent_id=profile.agent_id, action="read_file")

    assert len(list_trace_events(db, run_id=run1.id)) == 1
    assert list_trace_events(db, run_id=run1.id)[0].action == "write_file"


def test_list_filters_by_agent_id(tmp_path):
    db = _db(tmp_path)
    p1 = create_profile(db, tmp_path, "Arch", "architect", [])
    p2 = create_profile(db, tmp_path, "Worker", "worker", [])
    t1 = get_or_create_thread(db, agent_id=p1.agent_id, name="t1")
    t2 = get_or_create_thread(db, agent_id=p2.agent_id, name="t2")
    r1 = create_run(db, thread_id=t1.id, agent_id=p1.agent_id, contract={})
    r2 = create_run(db, thread_id=t2.id, agent_id=p2.agent_id, contract={})

    append_trace_event(db, run_id=r1.id, agent_id=p1.agent_id, action="write_file")
    append_trace_event(db, run_id=r2.id, agent_id=p2.agent_id, action="read_file")

    result = list_trace_events(db, agent_id=p1.agent_id)
    assert len(result) == 1
    assert result[0].agent_id == p1.agent_id


def test_list_ordered_by_ts(tmp_path):
    db, profile, _, run = _setup(tmp_path)

    append_trace_event(db, run_id=run.id, agent_id=profile.agent_id, action="a")
    time.sleep(0.01)
    append_trace_event(db, run_id=run.id, agent_id=profile.agent_id, action="b")
    time.sleep(0.01)
    append_trace_event(db, run_id=run.id, agent_id=profile.agent_id, action="c")

    events = list_trace_events(db, run_id=run.id)
    assert [e.action for e in events] == ["a", "b", "c"]


def test_append_returns_trace_event(tmp_path):
    db, profile, _, run = _setup(tmp_path)

    ev = append_trace_event(db, run_id=run.id, agent_id=profile.agent_id,
                            action="bash", target_path="py -m pytest",
                            raw={"cmd": "py -m pytest"})
    assert isinstance(ev, TraceEvent)
    assert ev.action == "bash"
    assert ev.target_path == "py -m pytest"
    assert ev.raw == {"cmd": "py -m pytest"}


def test_list_no_filters_returns_all(tmp_path):
    db, profile, _, run = _setup(tmp_path)

    append_trace_event(db, run_id=run.id, agent_id=profile.agent_id, action="write_file")
    append_trace_event(db, run_id=run.id, agent_id=profile.agent_id, action="read_file")

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
