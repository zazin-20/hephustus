"""Typed CRUD DAL for thread and turn records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from hephaestus.store.db import connect


@dataclass(slots=True)
class Thread:
    id: str
    node_id: str
    name: str
    workflow_id: str | None
    workflow_run_id: str | None
    placement_id: str | None
    issue_id: str | None
    created_at: str
    updated_at: str


@dataclass(slots=True)
class Turn:
    id: str
    thread_id: str
    run_id: str | None
    seq: int
    role: str
    kind: str | None
    text: str
    included: bool
    created_at: str


def get_or_create_thread(
    db_path,
    *,
    node_id: str,
    name: str,
    workflow_id: str | None = None,
    workflow_run_id: str | None = None,
    placement_id: str | None = None,
    issue_id: str | None = None,
) -> Thread:
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, node_id, name, workflow_id, workflow_run_id, placement_id, issue_id, created_at, updated_at
            FROM threads
            WHERE node_id = ?
              AND COALESCE(workflow_id, '') = COALESCE(?, '')
              AND COALESCE(workflow_run_id, '') = COALESCE(?, '')
              AND COALESCE(placement_id, '') = COALESCE(?, '')
              AND ((issue_id IS NULL AND ? IS NULL AND name = ?) OR issue_id = ?)
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (node_id, workflow_id, workflow_run_id, placement_id, issue_id, name, issue_id),
        ).fetchone()
        if row is not None:
            updated_at = _utc_now()
            conn.execute(
                "UPDATE threads SET updated_at = ? WHERE id = ?",
                (updated_at, row[0]),
            )
            conn.commit()
            return Thread(
                id=row[0],
                node_id=row[1],
                name=row[2],
                workflow_id=row[3],
                workflow_run_id=row[4],
                placement_id=row[5],
                issue_id=row[6],
                created_at=row[7],
                updated_at=updated_at,
            )

        thread = Thread(
            id=_new_id(),
            node_id=node_id,
            name=name,
            workflow_id=workflow_id,
            workflow_run_id=workflow_run_id,
            placement_id=placement_id,
            issue_id=issue_id,
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        conn.execute(
            """
            INSERT INTO threads(
                id, node_id, name, workflow_id, workflow_run_id, placement_id, issue_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                thread.id,
                thread.node_id,
                thread.name,
                thread.workflow_id,
                thread.workflow_run_id,
                thread.placement_id,
                thread.issue_id,
                thread.created_at,
                thread.updated_at,
            ),
        )
        conn.commit()
        return thread


def append_turn(
    db_path,
    thread_id: str,
    *,
    role: str,
    text: str,
    kind: str | None = None,
    run_id: str | None = None,
    included: bool = True,
) -> Turn:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(seq), 0) FROM turns WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()
        seq = int(row[0]) + 1
        turn = Turn(
            id=_new_id(),
            thread_id=thread_id,
            run_id=run_id,
            seq=seq,
            role=role,
            kind=kind,
            text=text,
            included=included,
            created_at=_utc_now(),
        )
        conn.execute(
            """
            INSERT INTO turns(id, thread_id, run_id, seq, role, kind, text, included, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                turn.id,
                turn.thread_id,
                turn.run_id,
                turn.seq,
                turn.role,
                turn.kind,
                turn.text,
                1 if turn.included else 0,
                turn.created_at,
            ),
        )
        conn.execute(
            "UPDATE threads SET updated_at = ? WHERE id = ?",
            (turn.created_at, thread_id),
        )
        conn.commit()
        return turn


def list_turns(db_path, thread_id: str) -> list[Turn]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, thread_id, run_id, seq, role, kind, text, included, created_at
            FROM turns
            WHERE thread_id = ?
            ORDER BY seq ASC, created_at ASC
            """,
            (thread_id,),
        ).fetchall()
    return [_row_to_turn(row) for row in rows]


def compile_context(db_path, thread_id: str) -> list[Turn]:
    """Return only included turns ordered by seq ASC — the client-owned context query."""
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, thread_id, run_id, seq, role, kind, text, included, created_at
            FROM turns
            WHERE thread_id = ? AND included = 1
            ORDER BY seq ASC
            """,
            (thread_id,),
        ).fetchall()
    return [_row_to_turn(row) for row in rows]


def set_included(db_path, turn_id: str, included: bool) -> None:
    """Toggle a turn's included flag — soft, reversible pruning."""
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE turns SET included = ? WHERE id = ?",
            (1 if included else 0, turn_id),
        )
        conn.commit()


def list_threads(db_path, node_id: str) -> list[Thread]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, node_id, name, workflow_id, workflow_run_id, placement_id, issue_id, created_at, updated_at
            FROM threads
            WHERE node_id = ?
            ORDER BY updated_at DESC, created_at DESC
            """,
            (node_id,),
        ).fetchall()
    return [
        Thread(
            id=row[0],
            node_id=row[1],
            name=row[2],
            workflow_id=row[3],
            workflow_run_id=row[4],
            placement_id=row[5],
            issue_id=row[6],
            created_at=row[7],
            updated_at=row[8],
        )
        for row in rows
    ]


def _row_to_thread(row) -> Thread:
    return Thread(
        id=row[0],
        node_id=row[1],
        name=row[2],
        workflow_id=row[3],
        workflow_run_id=row[4],
        placement_id=row[5],
        issue_id=row[6],
        created_at=row[7],
        updated_at=row[8],
    )


def _row_to_turn(row) -> Turn:
    return Turn(
        id=row[0],
        thread_id=row[1],
        run_id=row[2],
        seq=row[3],
        role=row[4],
        kind=row[5],
        text=row[6],
        included=bool(row[7]),
        created_at=row[8],
    )


def _new_id() -> str:
    return uuid.uuid4().hex


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


ThreadRecord = Thread
TurnRecord = Turn
