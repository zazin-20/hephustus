"""Workspace bootstrap and service-root discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hephaestus.store.db import connect

_EXCLUDED_SERVICE_ROOTS = {"agents", "archive", "node_modules"}


def discover_service_roots(root: str | Path) -> list[Path]:
    workspace_root = Path(root).resolve()
    if not workspace_root.exists():
        return []

    service_roots: list[Path] = []
    for child in sorted(workspace_root.iterdir(), key=lambda path: path.name.lower()):
        if not child.is_dir() or child.name in _EXCLUDED_SERVICE_ROOTS:
            continue
        if (child / ".git").exists():
            service_roots.append(child)
    return service_roots


@dataclass(frozen=True, slots=True)
class Workspace:
    root: Path
    service_roots: tuple[Path, ...]
    state_db_path: Path

    @classmethod
    def open(
        cls,
        root: str | Path,
        service_roots: list[Path] | tuple[Path, ...] | None = None,
    ) -> "Workspace":
        workspace_root = Path(root).resolve()
        state_db_path = workspace_root / ".hephaestus" / "state.db"
        conn = connect(state_db_path)
        conn.close()
        roots = service_roots
        if roots is None:
            roots = discover_service_roots(workspace_root)
        return cls(
            root=workspace_root,
            service_roots=tuple(Path(path).resolve() for path in roots),
            state_db_path=state_db_path,
        )

    @property
    def code_roots(self) -> list[Path]:
        roots = [self.root, *self.service_roots]
        seen: set[Path] = set()
        deduped: list[Path] = []
        for root in roots:
            if root not in seen:
                seen.add(root)
                deduped.append(root)
        return deduped
