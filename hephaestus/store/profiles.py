"""Typed CRUD DAL for the profiles table."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from hephaestus.identity import IdentityCard, default_capabilities, write_card
from hephaestus.store.db import connect, dumps_json, loads_json


@dataclass(slots=True)
class Profile:
    agent_id: str
    name: str
    role: str
    rules: list[str]
    model: str | None
    effort: str | None
    working_dir: str | None
    created_at: str


def create_profile(
    db_path: Path,
    okf_root: Path,
    name: str,
    role: str,
    rules: list[str],
    *,
    model: str | None = None,
    effort: str | None = None,
    working_dir: str | None = None,
) -> Profile:
    with connect(db_path) as conn:
        agent_id = _next_agent_id(conn, role)
        created_at = _utc_now()
        conn.execute(
            """
            INSERT INTO profiles(agent_id, name, role, rules, model, effort, working_dir, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                name,
                role,
                dumps_json(rules),
                model,
                effort,
                working_dir,
                created_at,
            ),
        )
        conn.commit()

    profile = Profile(
        agent_id=agent_id,
        name=name,
        role=role,
        rules=list(rules),
        model=model,
        effort=effort,
        working_dir=working_dir,
        created_at=created_at,
    )
    write_card(
        okf_root,
        IdentityCard(
            agent_id=profile.agent_id,
            name=profile.name,
            role=profile.role,
            created_at=profile.created_at,
            capabilities=default_capabilities(profile.role),
            sessions=[],
        ),
    )
    return profile


def list_profiles(db_path: Path) -> list[Profile]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT agent_id, name, role, rules, model, effort, working_dir, created_at
            FROM profiles
            ORDER BY created_at ASC, agent_id ASC
            """
        ).fetchall()
    return [_row_to_profile(row) for row in rows]


def get_profile(db_path: Path, agent_id: str) -> Profile:
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT agent_id, name, role, rules, model, effort, working_dir, created_at
            FROM profiles
            WHERE agent_id = ?
            """,
            (agent_id,),
        ).fetchone()
    if row is None:
        raise KeyError(agent_id)
    return _row_to_profile(row)


def delete_profile(db_path: Path, agent_id: str, okf_root: Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            DELETE FROM trace_events
            WHERE agent_id = ?
               OR run_id IN (SELECT id FROM runs WHERE agent_id = ?)
            """,
            (agent_id, agent_id),
        )
        conn.execute(
            """
            DELETE FROM turns
            WHERE thread_id IN (SELECT id FROM threads WHERE agent_id = ?)
            """,
            (agent_id,),
        )
        conn.execute("DELETE FROM runs WHERE agent_id = ?", (agent_id,))
        conn.execute("DELETE FROM threads WHERE agent_id = ?", (agent_id,))
        conn.execute("DELETE FROM profiles WHERE agent_id = ?", (agent_id,))
        conn.commit()
    if okf_root is not None:
        card_path = Path(okf_root) / "agents" / "identities" / f"{agent_id}.json"
        card_path.unlink(missing_ok=True)


def _next_agent_id(conn, role: str) -> str:
    prefix = role.lower()[:4] or "agent"
    row = conn.execute(
        """
        SELECT agent_id
        FROM profiles
        WHERE agent_id LIKE ?
        ORDER BY agent_id DESC
        LIMIT 1
        """,
        (f"{prefix}-%",),
    ).fetchone()
    next_counter = 1
    if row is not None:
        _, _, suffix = row[0].rpartition("-")
        next_counter = int(suffix) + 1
    return f"{prefix}-{next_counter:03d}"


def _row_to_profile(row) -> Profile:
    return Profile(
        agent_id=row[0],
        name=row[1],
        role=row[2],
        rules=loads_json(row[3]),
        model=row[4],
        effort=row[5],
        working_dir=row[6],
        created_at=row[7],
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
