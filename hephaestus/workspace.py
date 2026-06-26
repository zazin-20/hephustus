"""Workspace bootstrap and service-root discovery."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from hephaestus.okf_layout import OKFLayout
from hephaestus.store.db import connect

_EXCLUDED_SERVICE_ROOTS = {"agents", "archive", "node_modules"}

_ISSUES_INDEX_TEMPLATE = textwrap.dedent("""\
    ---
    title: Issues
    updated: {today}
    open_issues: []
    ---
    """)


def scaffold_okf(root: Path) -> bool:
    """Create the OKF tree under *root* if it does not already exist.

    Returns True when the scaffold was written (first boot), False when the
    tree already existed and nothing was changed.
    """
    layout = OKFLayout.for_workspace(root)
    workspace_root = layout.workspace_root
    first_boot = not layout.agents_root.exists()

    for directory in layout.required_directories():
        directory.mkdir(parents=True, exist_ok=True)

    index_path = layout.issues_index_path()
    if not index_path.exists():
        index_path.write_text(
            _ISSUES_INDEX_TEMPLATE.format(today=date.today().isoformat()),
            encoding="utf-8",
        )

    gitignore = workspace_root / ".gitignore"
    marker = ".hephaestus/"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
        if marker not in text:
            gitignore.write_text(
                text.rstrip("\n") + f"\n{marker}\n", encoding="utf-8"
            )
    else:
        gitignore.write_text(f"{marker}\n", encoding="utf-8")

    return first_boot


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
        workspace_root.mkdir(parents=True, exist_ok=True)
        scaffold_okf(workspace_root)
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
        for candidate in roots:
            if candidate not in seen:
                seen.add(candidate)
                deduped.append(candidate)
        return deduped
