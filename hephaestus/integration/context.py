"""OKF context assembly for a session (spec/architecture.md §5.1 / §5.2).

Given a role (and optionally an issue), determine which OKF documents to inject
and concatenate them into a system prompt. Pure and filesystem-only — no agent
calls — so it is fully unit-testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hephaestus.integration.routing import ROLE_DIRECTIVE, Role

# Roles that operate against a specific issue spec.
_ISSUE_CONSUMERS = {Role.WORKER, Role.QA, Role.ARCHITECT}


@dataclass(frozen=True)
class SessionContext:
    role: Role
    issue_id: str | None
    files: list[Path]      # existing files injected
    missing: list[Path]    # referenced but absent (surfaced, not fatal)
    system_prompt: str


def _candidate_paths(agents: Path, role: Role, issue_id: str | None) -> list[Path]:
    paths = [agents / ROLE_DIRECTIVE[role]]
    if issue_id and role in _ISSUE_CONSUMERS:
        paths.append(agents / "architect" / "issues" / f"{issue_id}.md")
    if role is Role.WORKER:
        paths.append(agents / "worker" / "tdd.md")
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


def build_session_context(root: str | Path, role: Role | str, issue_id: str | None = None) -> SessionContext:
    root = Path(root)
    agents = root / "agents" if (root / "agents").is_dir() else root
    role = Role(role)

    candidates = _candidate_paths(agents, role, issue_id)
    files = [p for p in candidates if p.is_file()]
    missing = [p for p in candidates if not p.is_file()]

    return SessionContext(
        role=role,
        issue_id=issue_id,
        files=files,
        missing=missing,
        system_prompt=_render(root, files),
    )
