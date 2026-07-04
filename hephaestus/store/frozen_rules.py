"""Typed DAL for frozen rules keyed by scope address."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import uuid

from hephaestus.store.db import connect


@dataclass(frozen=True, slots=True)
class ScopeAddress:
    machine: str
    workflow_id: str | None
    workflow_run_id: str | None
    placement_id: str | None
    node_id: str
    tags: list[str]

    def node_scope_key(self) -> str:
        if self.workflow_id and self.placement_id:
            return f"{self.workflow_id}:{self.placement_id}"
        return self.node_id


@dataclass(slots=True)
class FrozenRule:
    id: str
    scope: str
    scope_key: str
    topic_key: str
    kind: str
    body: str
    node_id: str | None
    workflow_id: str | None
    placement_id: str | None
    tag: str | None
    source_correction_id: str | None
    source_trace_event_id: str | None
    source_run_id: str | None
    source_node_id: str | None
    confirmer: str | None
    confirmed_at: str | None
    disabled_at: str | None
    superseded_by_rule_id: str | None
    created_at: str
    updated_at: str


def upsert_frozen_rule(
    db_path: str | Path,
    *,
    scope: str,
    topic_key: str,
    body: str,
    kind: str = "directive",
    machine: str | None = None,
    workflow_id: str | None = None,
    placement_id: str | None = None,
    node_id: str | None = None,
    tag: str | None = None,
) -> FrozenRule:
    now = _utc_now()
    scope_key = _scope_key(
        scope,
        machine=machine,
        workflow_id=workflow_id,
        placement_id=placement_id,
        node_id=node_id,
        tag=tag,
    )
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, created_at
            FROM frozen_rules
            WHERE scope = ? AND scope_key = ? AND topic_key = ? AND disabled_at IS NULL
            """,
            (scope, scope_key, topic_key),
        ).fetchone()
        if row is not None:
            rule_id = row[0]
            created_at = row[1]
            conn.execute(
                """
                UPDATE frozen_rules
                SET
                    kind = ?,
                    body = ?,
                    node_id = ?,
                    workflow_id = ?,
                    placement_id = ?,
                    tag = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    kind,
                    body,
                    node_id,
                    workflow_id,
                    placement_id,
                    tag,
                    now,
                    rule_id,
                ),
            )
        else:
            rule_id = uuid.uuid4().hex
            created_at = now
            conn.execute(
                """
                INSERT INTO frozen_rules(
                    id, scope, scope_key, topic_key, kind, body, node_id, workflow_id,
                    placement_id, tag, source_correction_id, source_trace_event_id,
                    source_run_id, source_node_id, confirmer, confirmed_at,
                    disabled_at, superseded_by_rule_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule_id,
                    scope,
                    scope_key,
                    topic_key,
                    kind,
                    body,
                    node_id,
                    workflow_id,
                    placement_id,
                    tag,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    created_at,
                    now,
                ),
            )
        conn.commit()
    return FrozenRule(
        id=rule_id,
        scope=scope,
        scope_key=scope_key,
        topic_key=topic_key,
        kind=kind,
        body=body,
        node_id=node_id,
        workflow_id=workflow_id,
        placement_id=placement_id,
        tag=tag,
        source_correction_id=None,
        source_trace_event_id=None,
        source_run_id=None,
        source_node_id=None,
        confirmer=None,
        confirmed_at=None,
        disabled_at=None,
        superseded_by_rule_id=None,
        created_at=created_at,
        updated_at=now,
    )


def promote_frozen_rule(
    db_path: str | Path,
    *,
    scope: str,
    topic_key: str,
    body: str,
    confirmer: str,
    kind: str = "directive",
    machine: str | None = None,
    workflow_id: str | None = None,
    placement_id: str | None = None,
    node_id: str | None = None,
    tag: str | None = None,
    source_correction_id: str | None = None,
    source_trace_event_id: str | None = None,
    source_run_id: str | None = None,
    source_node_id: str | None = None,
) -> FrozenRule:
    now = _utc_now()
    scope_key = _scope_key(
        scope,
        machine=machine,
        workflow_id=workflow_id,
        placement_id=placement_id,
        node_id=node_id,
        tag=tag,
    )
    rule_id = uuid.uuid4().hex

    with connect(db_path) as conn:
        prior = conn.execute(
            """
            SELECT id
            FROM frozen_rules
            WHERE scope = ? AND scope_key = ? AND topic_key = ? AND disabled_at IS NULL
            """,
            (scope, scope_key, topic_key),
        ).fetchone()
        if prior is not None:
            conn.execute(
                """
                UPDATE frozen_rules
                SET disabled_at = ?, superseded_by_rule_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, rule_id, now, prior[0]),
            )

        conn.execute(
            """
            INSERT INTO frozen_rules(
                id, scope, scope_key, topic_key, kind, body, node_id, workflow_id,
                placement_id, tag, source_correction_id, source_trace_event_id,
                source_run_id, source_node_id, confirmer, confirmed_at,
                disabled_at, superseded_by_rule_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rule_id,
                scope,
                scope_key,
                topic_key,
                kind,
                body,
                node_id,
                workflow_id,
                placement_id,
                tag,
                source_correction_id,
                source_trace_event_id,
                source_run_id,
                source_node_id,
                confirmer,
                now,
                None,
                None,
                now,
                now,
            ),
        )
        conn.commit()

    return FrozenRule(
        id=rule_id,
        scope=scope,
        scope_key=scope_key,
        topic_key=topic_key,
        kind=kind,
        body=body,
        node_id=node_id,
        workflow_id=workflow_id,
        placement_id=placement_id,
        tag=tag,
        source_correction_id=source_correction_id,
        source_trace_event_id=source_trace_event_id,
        source_run_id=source_run_id,
        source_node_id=source_node_id,
        confirmer=confirmer,
        confirmed_at=now,
        disabled_at=None,
        superseded_by_rule_id=None,
        created_at=now,
        updated_at=now,
    )


def list_frozen_rules_for_address(
    db_path: str | Path,
    address: ScopeAddress,
) -> list[FrozenRule]:
    pairs: list[tuple[str, str]] = [
        ("global", ""),
        ("machine", address.machine),
    ]
    if address.workflow_id:
        pairs.append(("workflow", address.workflow_id))
    for tag in address.tags:
        pairs.append(("tag", tag))
    pairs.append(("node", address.node_scope_key()))

    clauses = ["(scope = ? AND scope_key = ?)" for _ in pairs]
    params = [value for pair in pairs for value in pair]
    query = f"""
        SELECT
            id, scope, scope_key, topic_key, kind, body, node_id, workflow_id,
            placement_id, tag, source_correction_id, source_trace_event_id,
            source_run_id, source_node_id, confirmer, confirmed_at,
            disabled_at, superseded_by_rule_id, created_at, updated_at
        FROM frozen_rules
        WHERE disabled_at IS NULL AND ({" OR ".join(clauses)})
        ORDER BY
            CASE scope
                WHEN 'global' THEN 0
                WHEN 'machine' THEN 1
                WHEN 'workflow' THEN 2
                WHEN 'tag' THEN 3
                WHEN 'node' THEN 4
                ELSE 5
            END,
            created_at ASC,
            topic_key ASC
    """
    with connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_rule(row) for row in rows]


def _scope_key(
    scope: str,
    *,
    machine: str | None,
    workflow_id: str | None,
    placement_id: str | None,
    node_id: str | None,
    tag: str | None,
) -> str:
    if scope == "global":
        return ""
    if scope == "machine":
        if not machine:
            raise ValueError("machine scope requires machine")
        return machine
    if scope == "workflow":
        if not workflow_id:
            raise ValueError("workflow scope requires workflow_id")
        return workflow_id
    if scope == "tag":
        if not tag:
            raise ValueError("tag scope requires tag")
        return tag
    if scope == "node":
        if workflow_id and placement_id:
            return f"{workflow_id}:{placement_id}"
        if not node_id:
            raise ValueError("standalone node scope requires node_id")
        return node_id
    raise ValueError(f"unknown scope: {scope}")


def _row_to_rule(row) -> FrozenRule:
    return FrozenRule(
        id=row[0],
        scope=row[1],
        scope_key=row[2],
        topic_key=row[3],
        kind=row[4],
        body=row[5],
        node_id=row[6],
        workflow_id=row[7],
        placement_id=row[8],
        tag=row[9],
        source_correction_id=row[10],
        source_trace_event_id=row[11],
        source_run_id=row[12],
        source_node_id=row[13],
        confirmer=row[14],
        confirmed_at=row[15],
        disabled_at=row[16],
        superseded_by_rule_id=row[17],
        created_at=row[18],
        updated_at=row[19],
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
