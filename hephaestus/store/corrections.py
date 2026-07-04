"""Typed DAL for the corrections feedback queue."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from hephaestus.handoff import DistillationCandidateMarker, iter_trace_markers
from hephaestus.store.frozen_rules import FrozenRule, promote_frozen_rule
from hephaestus.store.trace import list_trace_events
from hephaestus.store.db import connect


@dataclass(slots=True)
class Correction:
    id: str
    violation_id: str | None
    node_id: str | None
    issue_id: str | None
    note: str
    source_kind: str
    topic_key: str | None
    candidate_scope: str | None
    candidate_shape: str | None
    trace_event_id: str | None
    source_run_id: str | None
    source_node_id: str | None
    status: str
    confirmer: str | None
    confirmed_at: str | None
    promotion_scope: str | None
    promotion_kind: str | None
    frozen_rule_id: str | None
    created_at: str


def append_correction(
    db_path: str | Path,
    *,
    violation_id: str | None = None,
    node_id: str | None = None,
    issue_id: str | None = None,
    note: str,
    source_kind: str = "human_note",
    topic_key: str | None = None,
    candidate_scope: str | None = None,
    candidate_shape: str | None = None,
    trace_event_id: str | None = None,
    source_run_id: str | None = None,
    source_node_id: str | None = None,
    status: str = "candidate",
    confirmer: str | None = None,
    confirmed_at: str | None = None,
    promotion_scope: str | None = None,
    promotion_kind: str | None = None,
    frozen_rule_id: str | None = None,
) -> Correction:
    c = Correction(
        id=uuid.uuid4().hex,
        violation_id=violation_id,
        node_id=node_id,
        issue_id=issue_id,
        note=note,
        source_kind=source_kind,
        topic_key=topic_key,
        candidate_scope=candidate_scope,
        candidate_shape=candidate_shape,
        trace_event_id=trace_event_id,
        source_run_id=source_run_id,
        source_node_id=source_node_id,
        status=status,
        confirmer=confirmer,
        confirmed_at=confirmed_at,
        promotion_scope=promotion_scope,
        promotion_kind=promotion_kind,
        frozen_rule_id=frozen_rule_id,
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO corrections(
                id, violation_id, node_id, issue_id, note, source_kind, topic_key,
                candidate_scope, candidate_shape, trace_event_id, source_run_id,
                source_node_id, status, confirmer, confirmed_at, promotion_scope,
                promotion_kind, frozen_rule_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                c.id,
                c.violation_id,
                c.node_id,
                c.issue_id,
                c.note,
                c.source_kind,
                c.topic_key,
                c.candidate_scope,
                c.candidate_shape,
                c.trace_event_id,
                c.source_run_id,
                c.source_node_id,
                c.status,
                c.confirmer,
                c.confirmed_at,
                c.promotion_scope,
                c.promotion_kind,
                c.frozen_rule_id,
                c.created_at,
            ),
        )
        conn.commit()
    return c


def list_corrections(
    db_path: str | Path,
    *,
    node_id: str | None = None,
    issue_id: str | None = None,
) -> list[Correction]:
    clauses, params = [], []
    if node_id is not None:
        clauses.append("node_id = ?")
        params.append(node_id)
    if issue_id is not None:
        clauses.append("issue_id = ?")
        params.append(issue_id)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    query = f"""
        SELECT
            id, violation_id, node_id, issue_id, note, source_kind, topic_key,
            candidate_scope, candidate_shape, trace_event_id, source_run_id,
            source_node_id, status, confirmer, confirmed_at, promotion_scope,
            promotion_kind, frozen_rule_id, created_at
        FROM corrections
        {where}
        ORDER BY created_at ASC
    """

    with connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [
        Correction(
            id=row[0],
            violation_id=row[1],
            node_id=row[2],
            issue_id=row[3],
            note=row[4],
            source_kind=row[5],
            topic_key=row[6],
            candidate_scope=row[7],
            candidate_shape=row[8],
            trace_event_id=row[9],
            source_run_id=row[10],
            source_node_id=row[11],
            status=row[12],
            confirmer=row[13],
            confirmed_at=row[14],
            promotion_scope=row[15],
            promotion_kind=row[16],
            frozen_rule_id=row[17],
            created_at=row[18],
        )
        for row in rows
    ]


def capture_distillation_candidates(
    db_path: str | Path,
    *,
    run_id: str,
    issue_id: str | None = None,
) -> list[Correction]:
    trace = list_trace_events(db_path, run_id=run_id)
    captured: list[Correction] = []
    for event, marker in iter_trace_markers(trace):
        if not isinstance(marker, DistillationCandidateMarker):
            continue
        with connect(db_path) as conn:
            existing = conn.execute(
                """
                SELECT id
                FROM corrections
                WHERE trace_event_id = ? AND topic_key = ? AND source_kind = 'distillation_candidate'
                """,
                (event.id, marker.topic_key),
            ).fetchone()
        if existing is not None:
            continue

        correction = append_correction(
            db_path,
            node_id=event.node_id,
            issue_id=issue_id,
            note=marker.directive,
            source_kind="distillation_candidate",
            topic_key=marker.topic_key,
            candidate_scope=marker.scope,
            candidate_shape="directive",
            trace_event_id=event.id,
            source_run_id=event.run_id,
            source_node_id=event.node_id,
        )
        captured.append(correction)
    return captured


def promote_correction(
    db_path: str | Path,
    correction_id: str,
    *,
    confirmer: str,
    scope: str | None = None,
    kind: str = "directive",
    machine: str | None = None,
    workflow_id: str | None = None,
    placement_id: str | None = None,
    node_id: str | None = None,
    tag: str | None = None,
) -> FrozenRule:
    corrections = {correction.id: correction for correction in list_corrections(db_path)}
    correction = corrections.get(correction_id)
    if correction is None:
        raise ValueError(f"unknown correction: {correction_id}")
    if not correction.topic_key:
        raise ValueError("correction topic_key is required for promotion")

    promotion_scope = scope or correction.candidate_scope
    if not promotion_scope:
        raise ValueError("promotion scope is required")

    rule = promote_frozen_rule(
        db_path,
        scope=promotion_scope,
        topic_key=correction.topic_key,
        body=correction.note,
        kind=kind,
        machine=machine,
        workflow_id=workflow_id,
        placement_id=placement_id,
        node_id=node_id or correction.node_id,
        tag=tag,
        source_correction_id=correction.id,
        source_trace_event_id=correction.trace_event_id,
        source_run_id=correction.source_run_id,
        source_node_id=correction.source_node_id,
        confirmer=confirmer,
    )

    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE corrections
            SET
                status = 'promoted',
                confirmer = ?,
                confirmed_at = ?,
                promotion_scope = ?,
                promotion_kind = ?,
                frozen_rule_id = ?
            WHERE id = ?
            """,
            (
                confirmer,
                rule.confirmed_at,
                promotion_scope,
                kind,
                rule.id,
                correction_id,
            ),
        )
        conn.commit()

    return rule
