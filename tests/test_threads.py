"""Tests for compile_context and set_included in store/threads.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from hephaestus.store.db import connect
from hephaestus.store.nodes import create_node
from hephaestus.store.threads import (
    append_turn,
    compile_context,
    get_or_create_thread,
    set_included,
)


def _db(tmp_path: Path):
    return tmp_path / ".hephaestus" / "state.db"


def _make_thread(db_path, tmp_path, node_id="node-001"):
    create_node(db_path, tmp_path, "Arch", "claude", ["architect"], [])
    return get_or_create_thread(db_path, node_id=node_id, name="thread-a")


def test_compile_context_returns_only_included_turns(tmp_path):
    db = _db(tmp_path)
    t = _make_thread(db, tmp_path)
    for i in range(3):
        append_turn(db, t.id, role="user", text=f"msg {i}", included=True)

    turns = compile_context(db, t.id)

    assert len(turns) == 3
    assert all(turn.included for turn in turns)


def test_compile_context_excludes_excluded_turns(tmp_path):
    db = _db(tmp_path)
    t = _make_thread(db, tmp_path)
    t1 = append_turn(db, t.id, role="user", text="keep a", included=True)
    t2 = append_turn(db, t.id, role="assistant", text="drop me", included=True)
    append_turn(db, t.id, role="user", text="keep b", included=True)

    set_included(db, t2.id, False)
    turns = compile_context(db, t.id)

    assert len(turns) == 2
    assert all(turn.text != "drop me" for turn in turns)


def test_compile_context_ordered_by_seq(tmp_path):
    db = _db(tmp_path)
    t = _make_thread(db, tmp_path)
    append_turn(db, t.id, role="user", text="first")
    append_turn(db, t.id, role="assistant", text="second")
    append_turn(db, t.id, role="user", text="third")

    turns = compile_context(db, t.id)

    assert [turn.text for turn in turns] == ["first", "second", "third"]


def test_set_included_is_reversible(tmp_path):
    db = _db(tmp_path)
    t = _make_thread(db, tmp_path)
    turn = append_turn(db, t.id, role="user", text="toggle me")

    set_included(db, turn.id, False)
    assert compile_context(db, t.id) == []

    set_included(db, turn.id, True)
    turns = compile_context(db, t.id)
    assert len(turns) == 1
    assert turns[0].text == "toggle me"


def test_set_included_unknown_id_is_silent(tmp_path):
    db = _db(tmp_path)
    _make_thread(db, tmp_path)
    # should not raise
    set_included(db, "nonexistent-id-xyz", False)
