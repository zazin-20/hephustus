"""SQLite operational store bootstrap and migrations."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 3

# V2: drop FK on violations.run_id so governance violations can be recorded
# without a matching run row (e.g. triggered by rule scan, not by a runner).
_SCHEMA_V2 = """
CREATE TABLE IF NOT EXISTS violations_v2 (
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
INSERT OR IGNORE INTO violations_v2
  SELECT id, rule_id, layer, severity, message, artifact,
         run_id, agent_id, issue_id, fix_hint, created_at, resolved_at
  FROM violations;
DROP TABLE violations;
ALTER TABLE violations_v2 RENAME TO violations;
"""

_SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS profiles (
  agent_id     TEXT PRIMARY KEY,
  name         TEXT NOT NULL,
  role         TEXT NOT NULL,
  rules        TEXT NOT NULL,
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
  contract     TEXT NOT NULL,
  status       TEXT NOT NULL,
  usage        TEXT,
  outcome      TEXT,
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
  raw          TEXT
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

_SCHEMA_V3 = """
CREATE TABLE IF NOT EXISTS nodes_v3 (
  node_id         TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  provider        TEXT NOT NULL,
  tags            TEXT NOT NULL,
  rules           TEXT NOT NULL,
  model           TEXT,
  effort          TEXT,
  working_dir     TEXT,
  inputs          TEXT NOT NULL,
  outputs         TEXT NOT NULL,
  skills          TEXT NOT NULL,
  allowed_paths   TEXT NOT NULL,
  allowed_tools   TEXT NOT NULL,
  context_policy  TEXT,
  created_at      TEXT NOT NULL
);

INSERT OR IGNORE INTO nodes_v3(
  node_id, name, provider, tags, rules, model, effort, working_dir,
  inputs, outputs, skills, allowed_paths, allowed_tools, context_policy, created_at
)
SELECT
  agent_id,
  name,
  CASE
    WHEN role = 'worker' THEN 'codex'
    ELSE 'claude'
  END,
  json_array(role),
  rules,
  model,
  effort,
  working_dir,
  '[]',
  '[]',
  '[]',
  '[]',
  '[]',
  NULL,
  created_at
FROM profiles;

CREATE TABLE IF NOT EXISTS threads_v3 (
  id              TEXT PRIMARY KEY,
  node_id         TEXT NOT NULL REFERENCES nodes_v3(node_id),
  name            TEXT NOT NULL,
  workflow_id     TEXT,
  workflow_run_id TEXT,
  placement_id    TEXT,
  issue_id        TEXT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);

INSERT OR IGNORE INTO threads_v3(id, node_id, name, workflow_id, workflow_run_id, placement_id, issue_id, created_at, updated_at)
SELECT id, agent_id, name, NULL, NULL, NULL, issue_id, created_at, updated_at
FROM threads;

CREATE TABLE IF NOT EXISTS runs_v3 (
  id           TEXT PRIMARY KEY,
  thread_id    TEXT NOT NULL REFERENCES threads_v3(id),
  node_id      TEXT NOT NULL REFERENCES nodes_v3(node_id),
  contract     TEXT NOT NULL,
  status       TEXT NOT NULL,
  usage        TEXT,
  outcome      TEXT,
  started_at   TEXT NOT NULL,
  ended_at     TEXT
);

INSERT OR IGNORE INTO runs_v3(id, thread_id, node_id, contract, status, usage, outcome, started_at, ended_at)
SELECT id, thread_id, agent_id, contract, status, usage, outcome, started_at, ended_at
FROM runs;

CREATE TABLE IF NOT EXISTS trace_events_v3 (
  id           TEXT PRIMARY KEY,
  run_id       TEXT NOT NULL REFERENCES runs_v3(id),
  node_id      TEXT NOT NULL,
  ts           TEXT NOT NULL,
  action       TEXT NOT NULL,
  target_path  TEXT,
  raw          TEXT
);

INSERT OR IGNORE INTO trace_events_v3(id, run_id, node_id, ts, action, target_path, raw)
SELECT id, run_id, agent_id, ts, action, target_path, raw
FROM trace_events;

CREATE TABLE IF NOT EXISTS violations_v3 (
  id           TEXT PRIMARY KEY,
  rule_id      TEXT NOT NULL,
  layer        TEXT NOT NULL,
  severity     TEXT NOT NULL,
  message      TEXT NOT NULL,
  artifact     TEXT,
  run_id       TEXT,
  node_id      TEXT,
  issue_id     TEXT,
  fix_hint     TEXT,
  created_at   TEXT NOT NULL,
  resolved_at  TEXT
);

INSERT OR IGNORE INTO violations_v3
SELECT id, rule_id, layer, severity, message, artifact,
       run_id, agent_id, issue_id, fix_hint, created_at, resolved_at
FROM violations;

CREATE TABLE IF NOT EXISTS corrections_v3 (
  id           TEXT PRIMARY KEY,
  violation_id TEXT REFERENCES violations_v3(id),
  node_id      TEXT,
  issue_id     TEXT,
  note         TEXT NOT NULL,
  created_at   TEXT NOT NULL
);

INSERT OR IGNORE INTO corrections_v3
SELECT id, violation_id, agent_id, issue_id, note, created_at
FROM corrections;

CREATE TABLE IF NOT EXISTS frozen_rules (
  id           TEXT PRIMARY KEY,
  scope        TEXT NOT NULL,
  scope_key    TEXT NOT NULL,
  topic_key    TEXT NOT NULL,
  kind         TEXT NOT NULL,
  body         TEXT NOT NULL,
  node_id      TEXT,
  workflow_id  TEXT,
  placement_id TEXT,
  tag          TEXT,
  created_at   TEXT NOT NULL,
  updated_at   TEXT NOT NULL,
  UNIQUE(scope, scope_key, topic_key)
);

DROP TABLE trace_events;
DROP TABLE runs;
DROP TABLE threads;
DROP TABLE profiles;
DROP TABLE violations;
DROP TABLE corrections;
ALTER TABLE nodes_v3 RENAME TO nodes;
ALTER TABLE threads_v3 RENAME TO threads;
ALTER TABLE runs_v3 RENAME TO runs;
ALTER TABLE trace_events_v3 RENAME TO trace_events;
ALTER TABLE violations_v3 RENAME TO violations;
ALTER TABLE corrections_v3 RENAME TO corrections;
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
    if current < 2:
        conn.executescript(_SCHEMA_V2)
        _set_schema_version(conn, 2)
        applied.append(2)
    if current < 3:
        conn.executescript(_SCHEMA_V3)
        _set_schema_version(conn, 3)
        applied.append(3)

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
