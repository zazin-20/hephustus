"""Canonical OKF filesystem layout helpers.

REUSABLE — the single home for the OKF tree shape. Adding a new location (e.g.
agents/workflows/ for user-authored workflows) is a one-place edit here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class OKFLayout:
    workspace_root: Path
    agents_root: Path

    @classmethod
    def for_workspace(cls, root: str | Path) -> "OKFLayout":
        return cls._from_root(root, prefer_existing=False)

    @classmethod
    def for_existing_root(cls, root: str | Path) -> "OKFLayout":
        return cls._from_root(root, prefer_existing=True)

    @classmethod
    def _from_root(cls, root: str | Path, *, prefer_existing: bool) -> "OKFLayout":
        root_path = Path(root)
        if root_path.name == "agents":
            return cls(workspace_root=root_path.parent, agents_root=root_path)
        agents_root = root_path / "agents"
        if prefer_existing and agents_root.is_dir():
            return cls(workspace_root=root_path, agents_root=agents_root)
        return cls(workspace_root=root_path, agents_root=agents_root)

    @property
    def architect_dir(self) -> Path:
        return self.agents_root / "architect"

    @property
    def issues_dir(self) -> Path:
        return self.architect_dir / "issues"

    @property
    def handoffs_dir(self) -> Path:
        return self.architect_dir / "handoffs"

    @property
    def qa_evidence_dir(self) -> Path:
        return self.agents_root / "qa" / "evidence"

    @property
    def log_dir(self) -> Path:
        return self.agents_root / "log"

    @property
    def identities_dir(self) -> Path:
        return self.agents_root / "identities"

    @property
    def archive_dir(self) -> Path:
        return self.agents_root / "archive"

    @property
    def worker_dir(self) -> Path:
        return self.agents_root / "worker"

    def required_directories(self) -> tuple[Path, ...]:
        return (
            self.issues_dir,
            self.handoffs_dir,
            self.qa_evidence_dir,
            self.log_dir,
            self.identities_dir,
            self.archive_dir,
        )

    def resolve(self, relative: str | Path) -> Path:
        return self.agents_root / Path(relative)

    def issues_index_path(self) -> Path:
        return self.issues_dir / "index.md"

    def issue_path(self, issue_id: str) -> Path:
        return self.issues_dir / f"{issue_id}.md"

    def handoff_path(self, issue_id: str) -> Path:
        return self.handoffs_dir / f"{issue_id}.md"

    def qa_evidence_path(self, issue_id: str) -> Path:
        return self.qa_evidence_dir / f"{issue_id}.md"

    def log_entry_path(self, issue_id: str) -> Path:
        return self.log_dir / f"{issue_id}.md"

    def identity_card_path(self, node_id: str) -> Path:
        return self.identities_dir / f"{node_id}.json"

    def worker_tdd_path(self) -> Path:
        return self.worker_dir / "tdd.md"
