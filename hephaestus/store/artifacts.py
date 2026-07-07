"""Typed CRUD DAL for artifact-spec definitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from hephaestus.artifact_spec import HasSectionPredicate, MinItemsPredicate, NonEmptyPredicate, load_artifact_spec
from hephaestus.okf_layout import OKFLayout
from hephaestus.store.db import connect, dumps_json, loads_json

_SECTIONS_TO_SKIP = {"Predicates", "Good Looks Like", "Antipatterns", "Examples"}
_ARTIFACTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  path        TEXT NOT NULL,
  tags        TEXT NOT NULL,
  created_at  TEXT NOT NULL
)
"""


@dataclass(frozen=True, slots=True)
class ArtifactHeading:
    heading: str
    required: bool
    min_items: int | None


@dataclass(frozen=True, slots=True)
class Artifact:
    artifact_id: str
    name: str
    path: str
    tags: list[str]
    created_at: str
    headings: list[ArtifactHeading]
    good_looks_like: str
    antipatterns: str
    examples: str


def create_artifact(
    db_path: str | Path,
    *,
    name: str,
    tags: list[str] | None = None,
    headings: list[ArtifactHeading] | None = None,
    good_looks_like: str = "",
    antipatterns: str = "",
    examples: str = "",
) -> Artifact:
    artifact_tags = list(tags or [])
    artifact_headings = _normalize_headings(headings or [])
    created_at = _utc_now()
    layout = _layout_for_db(db_path)
    with connect(db_path) as conn:
        _ensure_table(conn)
        artifact_id = _next_artifact_id(conn)
        path = _artifact_relative_path(artifact_id)
        _write_markdown(
            layout,
            artifact_id=artifact_id,
            name=name,
            tags=artifact_tags,
            created_at=created_at,
            headings=artifact_headings,
            good_looks_like=good_looks_like,
            antipatterns=antipatterns,
            examples=examples,
        )
        conn.execute(
            """
            INSERT INTO artifacts(artifact_id, name, path, tags, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (artifact_id, name, path, dumps_json(artifact_tags), created_at),
        )
        conn.commit()
    return get_artifact(db_path, artifact_id)


def get_artifact(db_path: str | Path, artifact_id: str) -> Artifact:
    layout = _layout_for_db(db_path)
    with connect(db_path) as conn:
        _ensure_table(conn)
        row = conn.execute(
            """
            SELECT artifact_id, name, path, tags, created_at
            FROM artifacts
            WHERE artifact_id = ?
            """,
            (artifact_id,),
        ).fetchone()
    if row is None:
        raise KeyError(artifact_id)
    return _row_to_artifact(layout, row)


def list_artifacts(db_path: str | Path) -> list[Artifact]:
    layout = _layout_for_db(db_path)
    with connect(db_path) as conn:
        _ensure_table(conn)
        rows = conn.execute(
            """
            SELECT artifact_id, name, path, tags, created_at
            FROM artifacts
            ORDER BY created_at ASC, artifact_id ASC
            """
        ).fetchall()
    return [_row_to_artifact(layout, row) for row in rows]


def update_artifact(
    db_path: str | Path,
    artifact_id: str,
    *,
    name: str,
    tags: list[str] | None = None,
    headings: list[ArtifactHeading] | None = None,
    good_looks_like: str = "",
    antipatterns: str = "",
    examples: str = "",
) -> Artifact:
    current = get_artifact(db_path, artifact_id)
    artifact_tags = list(tags or [])
    artifact_headings = _normalize_headings(headings or [])
    layout = _layout_for_db(db_path)
    _write_markdown(
        layout,
        artifact_id=artifact_id,
        name=name,
        tags=artifact_tags,
        created_at=current.created_at,
        headings=artifact_headings,
        good_looks_like=good_looks_like,
        antipatterns=antipatterns,
        examples=examples,
    )
    with connect(db_path) as conn:
        _ensure_table(conn)
        conn.execute(
            """
            UPDATE artifacts
            SET name = ?, tags = ?
            WHERE artifact_id = ?
            """,
            (name, dumps_json(artifact_tags), artifact_id),
        )
        conn.commit()
    return get_artifact(db_path, artifact_id)


def delete_artifact(db_path: str | Path, artifact_id: str) -> Artifact:
    artifact = get_artifact(db_path, artifact_id)
    with connect(db_path) as conn:
        _ensure_table(conn)
        conn.execute("DELETE FROM artifacts WHERE artifact_id = ?", (artifact_id,))
        conn.commit()
    _layout_for_db(db_path).workspace_root.joinpath(artifact.path).unlink(missing_ok=True)
    return artifact


def _ensure_table(conn) -> None:
    conn.execute(_ARTIFACTS_SCHEMA)


def _layout_for_db(db_path: str | Path) -> OKFLayout:
    return OKFLayout.for_existing_root(Path(db_path).resolve().parent.parent)


def _artifact_relative_path(artifact_id: str) -> str:
    return f"agents/artifacts/{artifact_id}.md"


def _artifact_file_path(layout: OKFLayout, artifact_id: str) -> Path:
    return layout.artifacts_dir / f"{artifact_id}.md"


def _next_artifact_id(conn) -> str:
    row = conn.execute(
        """
        SELECT artifact_id
        FROM artifacts
        WHERE artifact_id LIKE 'artifact-%'
        ORDER BY artifact_id DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return "artifact-001"
    current = int(str(row[0]).split("-")[-1])
    return f"artifact-{current + 1:03d}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_markdown(
    layout: OKFLayout,
    *,
    artifact_id: str,
    name: str,
    tags: list[str],
    created_at: str,
    headings: list[ArtifactHeading],
    good_looks_like: str,
    antipatterns: str,
    examples: str,
) -> None:
    path = _artifact_file_path(layout, artifact_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _compose_markdown(
            artifact_id=artifact_id,
            name=name,
            tags=tags,
            created_at=created_at,
            headings=headings,
            good_looks_like=good_looks_like,
            antipatterns=antipatterns,
            examples=examples,
        ),
        encoding="utf-8",
    )
    load_artifact_spec(path)


def _compose_markdown(
    *,
    artifact_id: str,
    name: str,
    tags: list[str],
    created_at: str,
    headings: list[ArtifactHeading],
    good_looks_like: str,
    antipatterns: str,
    examples: str,
) -> str:
    frontmatter = yaml.safe_dump(
        {
            "artifact_id": artifact_id,
            "title": name,
            "tags": tags,
            "created_at": created_at,
        },
        sort_keys=False,
    ).strip()
    predicates: list[str] = []
    for heading in headings:
        if heading.required:
            predicates.append(f'- has_section("{heading.heading}")')
            predicates.append(f'- non_empty("{heading.heading}")')
        if heading.min_items is not None:
            predicates.append(f'- min_items("{heading.heading}", {heading.min_items})')
    sections = [
        "## Predicates",
        "\n".join(predicates).strip(),
    ]
    for heading in headings:
        sections.append(f"## {heading.heading}")
        sections.append("")
    sections.extend(
        [
            "## Good Looks Like",
            good_looks_like.strip(),
            "## Antipatterns",
            antipatterns.strip(),
            "## Examples",
            examples.strip(),
        ]
    )
    body = "\n\n".join(sections).rstrip()
    return f"---\n{frontmatter}\n---\n\n{body}\n"


def _row_to_artifact(layout: OKFLayout, row) -> Artifact:
    artifact_id, name, path, tags_json, created_at = row
    spec = load_artifact_spec(layout.workspace_root / path)
    section_names = [
        title for title in spec.document.sections.keys()
        if title not in _SECTIONS_TO_SKIP
    ]
    heading_requirements = {
        predicate.name if isinstance(predicate, HasSectionPredicate) else predicate.target
        for predicate in spec.predicates
        if isinstance(predicate, (HasSectionPredicate, NonEmptyPredicate))
    }
    heading_min_items: dict[str, int] = {
        predicate.target: predicate.minimum
        for predicate in spec.predicates
        if isinstance(predicate, MinItemsPredicate)
    }
    frontmatter = spec.document.parsed.frontmatter
    return Artifact(
        artifact_id=str(frontmatter.get("artifact_id", artifact_id)),
        name=str(frontmatter.get("title", name)),
        path=path,
        tags=list(frontmatter.get("tags", loads_json(tags_json)) or []),
        created_at=str(frontmatter.get("created_at", created_at)),
        headings=[
            ArtifactHeading(
                heading=heading,
                required=heading in heading_requirements,
                min_items=heading_min_items.get(heading),
            )
            for heading in section_names
        ],
        good_looks_like=spec.document.sections.get("Good Looks Like", ""),
        antipatterns=spec.document.sections.get("Antipatterns", ""),
        examples=spec.document.sections.get("Examples", ""),
    )


def _normalize_headings(headings: list[ArtifactHeading]) -> list[ArtifactHeading]:
    normalized: list[ArtifactHeading] = []
    seen: set[str] = set()
    for heading in headings:
        title = heading.heading.strip()
        if not title or title in seen or title in _SECTIONS_TO_SKIP:
            continue
        seen.add(title)
        minimum = heading.min_items
        if minimum is not None and minimum < 1:
            minimum = 1
        normalized.append(ArtifactHeading(heading=title, required=bool(heading.required), min_items=minimum))
    return normalized
