"""OKF context assembly for a node run."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hephaestus.integration.routing import TAG_DIRECTIVE
from hephaestus.okf_layout import OKFLayout

_ISSUE_CONSUMER_TAGS = {"worker", "qa", "architect"}


@dataclass(frozen=True)
class SessionContext:
    node_id: str
    tags: list[str]
    issue_id: str | None
    files: list[Path]      # existing files injected
    missing: list[Path]    # referenced but absent (surfaced, not fatal)
    system_prompt: str


def _candidate_paths(layout: OKFLayout, tags: list[str], issue_id: str | None) -> list[Path]:
    paths: list[Path] = []
    for tag in tags:
        relative = TAG_DIRECTIVE.get(tag)
        if relative is not None:
            paths.append(layout.resolve(relative))
    if issue_id and _ISSUE_CONSUMER_TAGS.intersection(tags):
        paths.append(layout.issue_path(issue_id))
    if "worker" in tags:
        paths.append(layout.worker_tdd_path())
    return paths


def _render(root: Path, files: list[Path]) -> str:
    parts = []
    for p in files:
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            rel = p.name
        parts.append(f"# ===== {rel} =====\n{p.read_text(encoding='utf-8').strip()}")
    return "\n\n".join(parts)


def build_session_context(
    root: str | Path,
    *,
    node_id: str,
    tags: list[str],
    issue_id: str | None = None,
) -> SessionContext:
    render_root = Path(root)
    layout = OKFLayout.for_existing_root(render_root)

    candidates = _candidate_paths(layout, tags, issue_id)
    files = [p for p in candidates if p.is_file()]
    missing = [p for p in candidates if not p.is_file()]

    return SessionContext(
        node_id=node_id,
        tags=list(tags),
        issue_id=issue_id,
        files=files,
        missing=missing,
        system_prompt=_render(render_root, files),
    )
