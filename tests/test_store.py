from __future__ import annotations

import sqlite3
from pathlib import Path

from hephaestus.store.db import SCHEMA_VERSION, apply_migrations, connect


EXPECTED_TABLES = {
    "profiles",
    "threads",
    "turns",
    "runs",
    "trace_events",
    "violations",
    "corrections",
    "meta",
}


def _table_names(db_path: Path) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    return {name for (name,) in rows}


def test_connect_bootstraps_full_schema_and_wal(tmp_path):
    db_path = tmp_path / "workspace" / ".hephaestus" / "state.db"

    with connect(db_path) as conn:
        version = conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()

    assert db_path.exists()
    assert EXPECTED_TABLES.issubset(_table_names(db_path))
    assert version == (str(SCHEMA_VERSION),)
    assert journal_mode == ("wal",)


def test_reopen_is_idempotent_and_does_not_wipe(tmp_path):
    db_path = tmp_path / "workspace" / ".hephaestus" / "state.db"

    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("sentinel", "keep"),
        )
        conn.commit()

    with connect(db_path) as conn:
        applied = apply_migrations(conn)
        sentinel = conn.execute(
            "SELECT value FROM meta WHERE key = 'sentinel'"
        ).fetchone()

    assert applied == []
    assert sentinel == ("keep",)


def test_connect_migrates_when_schema_version_is_behind(tmp_path):
    db_path = tmp_path / "workspace" / ".hephaestus" / "state.db"

    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO profiles(agent_id, name, role, rules, model, effort, working_dir, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("arch-001", "Architect", "architect", "[]", None, None, None, "2026-06-22T00:00:00Z"),
        )
        conn.execute("DROP TABLE corrections")
        conn.execute(
            "UPDATE meta SET value = ? WHERE key = 'schema_version'",
            ("0",),
        )
        conn.commit()

    with connect(db_path) as conn:
        version = conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        profile = conn.execute(
            "SELECT name FROM profiles WHERE agent_id = ?",
            ("arch-001",),
        ).fetchone()

    assert "corrections" in _table_names(db_path)
    assert version == (str(SCHEMA_VERSION),)
    assert profile == ("Architect",)
