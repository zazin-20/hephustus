"""Typed DAL for trace_events — observed agent actions per run."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hephaestus.store.db import connect, dumps_json, loads_json


@dataclass(slots=True)
class TraceEvent:
    id: str
    run_id: str
    agent_id: str
    ts: str
    action: str
    target_path: str | None
    raw: dict | None


def append_trace_event(
    db_path: str | Path,
    *,
    run_id: str,
    agent_id: str,
    action: str,
    target_path: str | None = None,
    raw: dict | None = None,
) -> TraceEvent:
    event = TraceEvent(
        id=uuid.uuid4().hex,
        run_id=run_id,
        agent_id=agent_id,
        ts=_utc_now(),
        action=action,
        target_path=target_path,
        raw=raw,
    )
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO trace_events(id, run_id, agent_id, ts, action, target_path, raw)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.run_id,
                event.agent_id,
                event.ts,
                event.action,
                event.target_path,
                dumps_json(event.raw) if event.raw is not None else None,
            ),
        )
        conn.commit()
    return event


def list_trace_events(
    db_path: str | Path,
    *,
    run_id: str | None = None,
    agent_id: str | None = None,
) -> list[TraceEvent]:
    clauses: list[str] = []
    params: list[Any] = []

    if run_id is not None:
        clauses.append("run_id = ?")
        params.append(run_id)
    if agent_id is not None:
        clauses.append("agent_id = ?")
        params.append(agent_id)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT id, run_id, agent_id, ts, action, target_path, raw
        FROM trace_events
        {where}
        ORDER BY ts ASC
    """

    with connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()

    return [
        TraceEvent(
            id=row[0],
            run_id=row[1],
            agent_id=row[2],
            ts=row[3],
            action=row[4],
            target_path=row[5],
            raw=loads_json(row[6]),
        )
        for row in rows
    ]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
