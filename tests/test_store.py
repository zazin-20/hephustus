from __future__ import annotations

import sqlite3
from pathlib import Path

from hephaestus.store.db import SCHEMA_VERSION, apply_migrations, connect


EXPECTED_TABLES = {
    "nodes",
    "threads",
    "turns",
    "runs",
    "trace_events",
    "violations",
    "corrections",
    "frozen_rules",
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
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE profiles (
              agent_id     TEXT PRIMARY KEY,
              name         TEXT NOT NULL,
              role         TEXT NOT NULL,
              rules        TEXT NOT NULL,
              model        TEXT,
              effort       TEXT,
              working_dir  TEXT,
              created_at   TEXT NOT NULL
            );
            CREATE TABLE threads (
              id           TEXT PRIMARY KEY,
              agent_id     TEXT NOT NULL,
              name         TEXT NOT NULL,
              issue_id     TEXT,
              created_at   TEXT NOT NULL,
              updated_at   TEXT NOT NULL
            );
            CREATE TABLE runs (
              id           TEXT PRIMARY KEY,
              thread_id    TEXT NOT NULL,
              agent_id     TEXT NOT NULL,
              contract     TEXT NOT NULL,
              status       TEXT NOT NULL,
              usage        TEXT,
              outcome      TEXT,
              started_at   TEXT NOT NULL,
              ended_at     TEXT
            );
            CREATE TABLE trace_events (
              id           TEXT PRIMARY KEY,
              run_id       TEXT NOT NULL,
              agent_id     TEXT NOT NULL,
              ts           TEXT NOT NULL,
              action       TEXT NOT NULL,
              target_path  TEXT,
              raw          TEXT
            );
            CREATE TABLE violations (
              id           TEXT PRIMARY KEY,
              rule_id      TEXT NOT NULL,
              layer        TEXT NOT NULL,
              severity     TEXT NOT NULL,
              message      TEXT NOT NULL,
              artifact     TEXT,
              run_id       TEXT,
              agent_id     TEXT,
              issue_id     TEXT,
              fix_hint     TEXT,
              created_at   TEXT NOT NULL,
              resolved_at  TEXT
            );
            CREATE TABLE corrections (
              id           TEXT PRIMARY KEY,
              violation_id TEXT,
              agent_id     TEXT,
              issue_id     TEXT,
              note         TEXT NOT NULL,
              created_at   TEXT NOT NULL
            );
            CREATE TABLE meta (
              key          TEXT PRIMARY KEY,
              value        TEXT
            );
            INSERT INTO meta(key, value) VALUES ('schema_version', '2');
            """
        )
        conn.execute(
            """
            INSERT INTO profiles(agent_id, name, role, rules, model, effort, working_dir, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("arch-001", "Architect", "architect", "[]", None, None, None, "2026-06-22T00:00:00Z"),
        )
        conn.commit()

    with connect(db_path) as conn:
        version = conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        node = conn.execute(
            "SELECT name, provider, tags FROM nodes WHERE node_id = ?",
            ("arch-001",),
        ).fetchone()

    assert "nodes" in _table_names(db_path)
    assert version == (str(SCHEMA_VERSION),)
    assert node == ("Architect", "claude", '["architect"]')
