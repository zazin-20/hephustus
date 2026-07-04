"""Typed CRUD DAL for the nodes table."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from hephaestus.identity import IdentityCard, default_capabilities, write_card
from hephaestus.okf_layout import OKFLayout
from hephaestus.store.db import connect, dumps_json, loads_json


@dataclass(slots=True)
class Node:
    node_id: str
    name: str
    provider: str
    tags: list[str]
    rules: list[str]
    model: str | None
    effort: str | None
    working_dir: str | None
    inputs: list[str]
    outputs: list[str]
    skills: list[str]
    skill_obligations: list[str]
    allowed_paths: list[str]
    allowed_tools: list[str]
    context_policy: str | None
    created_at: str


def create_node(
    db_path: Path,
    okf_root: Path,
    name: str,
    provider: str,
    tags: list[str],
    rules: list[str],
    *,
    model: str | None = None,
    effort: str | None = None,
    working_dir: str | None = None,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    skills: list[str] | None = None,
    skill_obligations: list[str] | None = None,
    allowed_paths: list[str] | None = None,
    allowed_tools: list[str] | None = None,
    context_policy: str | None = None,
) -> Node:
    with connect(db_path) as conn:
        node_id = _next_node_id(conn)
        created_at = _utc_now()
        conn.execute(
            """
            INSERT INTO nodes(
                node_id, name, provider, tags, rules, model, effort, working_dir,
                inputs, outputs, skills, skill_obligations, allowed_paths, allowed_tools,
                context_policy, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                name,
                provider,
                dumps_json(tags),
                dumps_json(rules),
                model,
                effort,
                working_dir,
                dumps_json(inputs or []),
                dumps_json(outputs or []),
                dumps_json(skills or []),
                dumps_json(skill_obligations or []),
                dumps_json(allowed_paths or []),
                dumps_json(allowed_tools or []),
                context_policy,
                created_at,
            ),
        )
        conn.commit()

    node = Node(
        node_id=node_id,
        name=name,
        provider=provider,
        tags=list(tags),
        rules=list(rules),
        model=model,
        effort=effort,
        working_dir=working_dir,
        inputs=list(inputs or []),
        outputs=list(outputs or []),
        skills=list(skills or []),
        skill_obligations=list(skill_obligations or []),
        allowed_paths=list(allowed_paths or []),
        allowed_tools=list(allowed_tools or []),
        context_policy=context_policy,
        created_at=created_at,
    )
    write_card(
        okf_root,
        IdentityCard(
            node_id=node.node_id,
            name=node.name,
            tags=node.tags,
            created_at=node.created_at,
            capabilities=default_capabilities(node.tags),
            sessions=[],
        ),
    )
    return node


def list_nodes(db_path: Path) -> list[Node]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                node_id, name, provider, tags, rules, model, effort, working_dir,
                inputs, outputs, skills, skill_obligations, allowed_paths, allowed_tools,
                context_policy, created_at
            FROM nodes
            ORDER BY created_at ASC, node_id ASC
            """
        ).fetchall()
    return [_row_to_node(row) for row in rows]


def get_node(db_path: Path, node_id: str) -> Node:
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                node_id, name, provider, tags, rules, model, effort, working_dir,
                inputs, outputs, skills, skill_obligations, allowed_paths, allowed_tools,
                context_policy, created_at
            FROM nodes
            WHERE node_id = ?
            """,
            (node_id,),
        ).fetchone()
    if row is None:
        raise KeyError(node_id)
    return _row_to_node(row)


def delete_node(db_path: Path, node_id: str, okf_root: Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            DELETE FROM trace_events
            WHERE node_id = ?
               OR run_id IN (SELECT id FROM runs WHERE node_id = ?)
            """,
            (node_id, node_id),
        )
        conn.execute(
            """
            DELETE FROM turns
            WHERE thread_id IN (SELECT id FROM threads WHERE node_id = ?)
            """,
            (node_id,),
        )
        conn.execute("DELETE FROM runs WHERE node_id = ?", (node_id,))
        conn.execute("DELETE FROM threads WHERE node_id = ?", (node_id,))
        conn.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
        conn.commit()
    if okf_root is not None:
        card_path = OKFLayout.for_existing_root(okf_root).identity_card_path(node_id)
        card_path.unlink(missing_ok=True)


def _next_node_id(conn) -> str:
    row = conn.execute(
        """
        SELECT node_id
        FROM nodes
        WHERE node_id LIKE 'node-%'
        ORDER BY node_id DESC
        LIMIT 1
        """
    ).fetchone()
    next_counter = 1
    if row is not None:
        _, _, suffix = row[0].rpartition("-")
        next_counter = int(suffix) + 1
    return f"node-{next_counter:03d}"


def _row_to_node(row) -> Node:
    return Node(
        node_id=row[0],
        name=row[1],
        provider=row[2],
        tags=loads_json(row[3]),
        rules=loads_json(row[4]),
        model=row[5],
        effort=row[6],
        working_dir=row[7],
        inputs=loads_json(row[8]),
        outputs=loads_json(row[9]),
        skills=loads_json(row[10]),
        skill_obligations=loads_json(row[11]),
        allowed_paths=loads_json(row[12]),
        allowed_tools=loads_json(row[13]),
        context_policy=row[14],
        created_at=row[15],
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
