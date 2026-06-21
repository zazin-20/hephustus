"""SQLite operational store bootstrap and migrations."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

_SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS profiles (
  agent_id     TEXT PRIMARY KEY,
  name         TEXT NOT NULL,
  role         TEXT NOT NULL,
  rules        JSON NOT NULL,
  model        TEXT,
  effort       TEXT,
  working_dir  TEXT,
  created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS threads (
  id           TEXT PRIMARY KEY,
  agent_id     TEXT NOT NULL REFERENCES profiles(agent_id),
  name         TEXT NOT NULL,
  issue_id     TEXT,
  created_at   TEXT NOT NULL,
  updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
  id           TEXT PRIMARY KEY,
  thread_id    TEXT NOT NULL REFERENCES threads(id),
  agent_id     TEXT NOT NULL REFERENCES profiles(agent_id),
  contract     JSON NOT NULL,
  status       TEXT NOT NULL,
  usage        JSON,
  outcome      JSON,
  started_at   TEXT NOT NULL,
  ended_at     TEXT
);

CREATE TABLE IF NOT EXISTS turns (
  id           TEXT PRIMARY KEY,
  thread_id    TEXT NOT NULL REFERENCES threads(id),
  run_id       TEXT REFERENCES runs(id),
  seq          INTEGER NOT NULL,
  role         TEXT NOT NULL,
  kind         TEXT,
  text         TEXT NOT NULL,
  included     INTEGER NOT NULL DEFAULT 1,
  created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trace_events (
  id           TEXT PRIMARY KEY,
  run_id       TEXT NOT NULL REFERENCES runs(id),
  agent_id     TEXT NOT NULL,
  ts           TEXT NOT NULL,
  action       TEXT NOT NULL,
  target_path  TEXT,
  raw          JSON
);

CREATE TABLE IF NOT EXISTS violations (
  id           TEXT PRIMARY KEY,
  rule_id      TEXT NOT NULL,
  layer        TEXT NOT NULL,
  severity     TEXT NOT NULL,
  message      TEXT NOT NULL,
  artifact     TEXT,
  run_id       TEXT REFERENCES runs(id),
  agent_id     TEXT,
  issue_id     TEXT,
  fix_hint     TEXT,
  created_at   TEXT NOT NULL,
  resolved_at  TEXT
);

CREATE TABLE IF NOT EXISTS corrections (
  id           TEXT PRIMARY KEY,
  violation_id TEXT REFERENCES violations(id),
  agent_id     TEXT,
  issue_id     TEXT,
  note         TEXT NOT NULL,
  created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
  key          TEXT PRIMARY KEY,
  value        TEXT
);
"""


def dumps_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def loads_json(value: str | bytes | bytearray | None) -> Any:
    if value is None:
        return None
    return json.loads(value)


def connect(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    apply_migrations(conn)
    return conn


def apply_migrations(conn: sqlite3.Connection) -> list[int]:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
          key   TEXT PRIMARY KEY,
          value TEXT
        )
        """
    )

    current = _schema_version(conn)
    applied: list[int] = []
    if current < 1:
        conn.executescript(_SCHEMA_V1)
        _set_schema_version(conn, 1)
        applied.append(1)

    conn.commit()
    return applied


def _schema_version(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT value FROM meta WHERE key = 'schema_version'"
    ).fetchone()
    if row is None:
        return 0
    try:
        return int(row[0])
    except (TypeError, ValueError):
        return 0


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(
        """
        INSERT INTO meta(key, value) VALUES('schema_version', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (str(version),),
    )
