"""DAL for violations table — attributed persistence."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import sqlite3

from hephaestus.core import Violation
from hephaestus.store.db import connect
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def append_violation(
    db: sqlite3.Connection,
    violation: Violation,
    *,
    run_id: str,
    agent_id: str,
    issue_id: str | None = None,
) -> int:
    row_id_holder: list[int] = []
    vid = uuid.uuid4().hex
    db.execute(
        """
        INSERT INTO violations(id, rule_id, layer, severity, message, artifact,
                               run_id, agent_id, issue_id, fix_hint, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            vid,
            violation.rule_id,
            getattr(violation, "layer", "governance"),
            violation.severity.value if hasattr(violation.severity, "value") else str(violation.severity),
            violation.message,
            violation.artifact or "",
            run_id,
            agent_id,
            issue_id,
            violation.fix_hint or "",
            _utc_now(),
        ),
    )
    db.commit()
    row = db.execute("SELECT rowid FROM violations WHERE id = ?", (vid,)).fetchone()
    return row[0] if row else 0


def list_violations(
    db: sqlite3.Connection,
    *,
    run_id: str | None = None,
    agent_id: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if run_id is not None:
        clauses.append("run_id = ?")
        params.append(run_id)
    if agent_id is not None:
        clauses.append("agent_id = ?")
        params.append(agent_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = db.execute(
        f"""
        SELECT id, rule_id, layer, severity, message, artifact,
               run_id, agent_id, issue_id, fix_hint, created_at
        FROM violations
        {where}
        ORDER BY created_at ASC
        """,
        params,
    ).fetchall()
    keys = ("id", "rule_id", "layer", "severity", "message", "artifact",
            "run_id", "agent_id", "issue_id", "fix_hint", "created_at")
    return [dict(zip(keys, row)) for row in rows]
