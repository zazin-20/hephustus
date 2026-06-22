"""Typed DAL for the corrections feedback queue."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from hephaestus.store.db import connect


@dataclass(slots=True)
class Correction:
    id: str
    violation_id: str | None
    agent_id: str | None
    issue_id: str | None
    note: str
    created_at: str


def append_correction(
    db_path: str | Path,
    *,
    violation_id: str | None = None,
    agent_id: str | None = None,
    issue_id: str | None = None,
    note: str,
) -> Correction:
    c = Correction(
        id=uuid.uuid4().hex,
        violation_id=violation_id,
        agent_id=agent_id,
        issue_id=issue_id,
        note=note,
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO corrections(id, violation_id, agent_id, issue_id, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (c.id, c.violation_id, c.agent_id, c.issue_id, c.note, c.created_at),
        )
        conn.commit()
    return c


def list_corrections(
    db_path: str | Path,
    *,
    agent_id: str | None = None,
    issue_id: str | None = None,
) -> list[Correction]:
    clauses, params = [], []
    if agent_id is not None:
        clauses.append("agent_id = ?")
        params.append(agent_id)
    if issue_id is not None:
        clauses.append("issue_id = ?")
        params.append(issue_id)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    query = f"SELECT id, violation_id, agent_id, issue_id, note, created_at FROM corrections {where} ORDER BY created_at ASC"

    with connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [Correction(id=r[0], violation_id=r[1], agent_id=r[2], issue_id=r[3], note=r[4], created_at=r[5]) for r in rows]
