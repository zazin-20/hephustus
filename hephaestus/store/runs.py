"""Typed CRUD DAL for run lifecycle records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from hephaestus.store.db import connect, dumps_json, loads_json


@dataclass(slots=True)
class Run:
    id: str
    thread_id: str
    agent_id: str
    contract: dict
    status: str
    usage: dict | None
    outcome: dict | None
    started_at: str
    ended_at: str | None


def create_run(db_path, *, thread_id: str, agent_id: str, contract: dict) -> Run:
    run = Run(
        id=_new_id(),
        thread_id=thread_id,
        agent_id=agent_id,
        contract=dict(contract),
        status="running",
        usage=None,
        outcome=None,
        started_at=_utc_now(),
        ended_at=None,
    )
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO runs(id, thread_id, agent_id, contract, status, usage, outcome, started_at, ended_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.id,
                run.thread_id,
                run.agent_id,
                dumps_json(run.contract),
                run.status,
                None,
                None,
                run.started_at,
                run.ended_at,
            ),
        )
        conn.commit()
    return run


def finish_run(
    db_path,
    run_id: str,
    *,
    status: str,
    usage: dict | None = None,
    outcome: dict | None = None,
    contract: dict | None = None,
) -> None:
    ended_at = _utc_now()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE runs
            SET status = ?, usage = ?, outcome = ?, contract = COALESCE(?, contract), ended_at = ?
            WHERE id = ?
            """,
            (
                status,
                dumps_json(usage) if usage is not None else None,
                dumps_json(outcome) if outcome is not None else None,
                dumps_json(contract) if contract is not None else None,
                ended_at,
                run_id,
            ),
        )
        conn.commit()


def interrupt_running_runs(db_path) -> int:
    ended_at = _utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """
            UPDATE runs
            SET status = 'interrupted', ended_at = COALESCE(ended_at, ?)
            WHERE status = 'running'
            """,
            (ended_at,),
        )
        conn.commit()
    return cur.rowcount


def get_run(db_path, run_id: str) -> Run:
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, thread_id, agent_id, contract, status, usage, outcome, started_at, ended_at
            FROM runs
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
    if row is None:
        raise KeyError(run_id)
    return _row_to_run(row)


def _row_to_run(row) -> Run:
    return Run(
        id=row[0],
        thread_id=row[1],
        agent_id=row[2],
        contract=loads_json(row[3]),
        status=row[4],
        usage=loads_json(row[5]),
        outcome=loads_json(row[6]),
        started_at=row[7],
        ended_at=row[8],
    )


def _new_id() -> str:
    return uuid.uuid4().hex


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


RunRecord = Run
