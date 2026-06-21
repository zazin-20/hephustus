"""The OKF index — a derived read cache over the `agents/` tree.

`build_context` scans the tree once and produces an `OKFContext`, the view that
every rule reads from. Rules never touch the disk directly, so the backing store
can later become a SQLite cache (or a server store) without changing the rule
interface. See spec/architecture.md §6.1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ValidationError

from hephaestus.core import Severity, Violation
from hephaestus.frontmatter import FrontmatterError, load
from hephaestus.models import (
    Handoff,
    IssuesIndex,
    IssueSpec,
    LogEntry,
    QAEvidence,
)


@dataclass
class OKFContext:
    root: Path
    issues: list[IssueSpec] = field(default_factory=list)
    handoffs: list[Handoff] = field(default_factory=list)
    log_entries: list[LogEntry] = field(default_factory=list)
    qa_evidence: list[QAEvidence] = field(default_factory=list)
    issues_index: IssuesIndex = field(default_factory=IssuesIndex)
    load_errors: list[Violation] = field(default_factory=list)

    @property
    def issue_ids(self) -> set[str]:
        return {i.id for i in self.issues}


def _load_collection(
    directory: Path,
    model: type[BaseModel],
    errors: list[Violation],
    skip: set[str] = frozenset(),
) -> list:
    items: list = []
    if not directory.is_dir():
        return items
    for path in sorted(directory.glob("*.md")):
        if path.name in skip:
            continue
        try:
            doc = load(path)
            items.append(model.model_validate(doc.frontmatter))
        except (FrontmatterError, ValidationError) as exc:
            errors.append(
                Violation(
                    rule_id="schema",
                    severity=Severity.ERROR,
                    message=f"{model.__name__} failed validation: {exc}",
                    artifact=str(path),
                    fix_hint="Fix the frontmatter to match the required schema for this doc type.",
                )
            )
    return items


def build_context(root: str | Path) -> OKFContext:
    """Build an OKFContext from a repo root or an `agents/` directory directly."""
    root = Path(root)
    agents = root / "agents" if (root / "agents").is_dir() else root
    errors: list[Violation] = []

    issues_dir = agents / "architect" / "issues"
    handoffs_dir = agents / "architect" / "handoffs"
    qa_dir = agents / "qa" / "evidence"
    log_dir = agents / "log"

    issues = _load_collection(issues_dir, IssueSpec, errors, skip={"index.md"})
    handoffs = _load_collection(handoffs_dir, Handoff, errors)
    qa_evidence = _load_collection(qa_dir, QAEvidence, errors)
    log_entries = _load_collection(log_dir, LogEntry, errors)

    issues_index = IssuesIndex()
    index_path = issues_dir / "index.md"
    if index_path.is_file():
        try:
            issues_index = IssuesIndex.model_validate(load(index_path).frontmatter)
        except (FrontmatterError, ValidationError) as exc:
            errors.append(
                Violation(
                    rule_id="schema",
                    severity=Severity.ERROR,
                    message=f"IssuesIndex failed validation: {exc}",
                    artifact=str(index_path),
                    fix_hint="Fix the index frontmatter (title, updated, open_issues).",
                )
            )

    return OKFContext(
        root=root,
        issues=issues,
        handoffs=handoffs,
        log_entries=log_entries,
        qa_evidence=qa_evidence,
        issues_index=issues_index,
        load_errors=errors,
    )
