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
            WHERE scope = ? AND scope_key = ? AND topic_key = ?
            """,
            (scope, scope_key, topic_key),
        ).fetchone()
        rule_id = row[0] if row is not None else uuid.uuid4().hex
        created_at = row[1] if row is not None else now
        conn.execute(
            """
            INSERT INTO frozen_rules(
                id, scope, scope_key, topic_key, kind, body, node_id, workflow_id,
                placement_id, tag, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(scope, scope_key, topic_key) DO UPDATE SET
                id = excluded.id,
                kind = excluded.kind,
                body = excluded.body,
                node_id = excluded.node_id,
                workflow_id = excluded.workflow_id,
                placement_id = excluded.placement_id,
                tag = excluded.tag,
                updated_at = excluded.updated_at
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
        created_at=created_at,
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
            placement_id, tag, created_at, updated_at
        FROM frozen_rules
        WHERE {" OR ".join(clauses)}
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
        created_at=row[10],
        updated_at=row[11],
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
