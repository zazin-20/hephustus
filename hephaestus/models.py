"""Pydantic models for OKF document types (the Tier-1 schema layer).

Each model validates the frontmatter of one artifact kind. `extra="allow"` lets
documents carry additional human-facing fields without failing validation, while
required fields are still enforced. See spec/architecture.md §3.1 and §6.3.
"""
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in-progress"
    HANDOFF_PENDING = "handoff-pending"
    DONE = "done"


class OKFModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class IssueSpec(OKFModel):
    """agents/architect/issues/<id>.md"""

    id: str
    status: IssueStatus
    role: str
    sprint: str
    created: date
    title: str | None = None


class Handoff(OKFModel):
    """agents/architect/handoffs/<issue_id>.md"""

    issue_id: str
    worker: str
    status: str
    created: date
    reviewed_by: list[str] = Field(default_factory=list)

    @field_validator("reviewed_by", mode="before")
    @classmethod
    def _coerce_reviewers(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return v


class QAEvidence(OKFModel):
    """agents/qa/evidence/<issue_id>.md"""

    issue_id: str
    result: str | None = None
    created: date | None = None


class LogEntry(OKFModel):
    """agents/log/<issue_id>.md — structured completion record.

    (The prose agents/log.md remains a human-readable rollup.)
    """

    issue_id: str
    sprint: str
    date: date
    worker: str | None = None
    qa: str | None = None
    summary: str | None = None
    sprint_closed: bool = False


class OpenIssueRef(BaseModel):
    id: str
    sprint: str


class IssuesIndex(OKFModel):
    """agents/architect/issues/index.md — independently-maintained rollup.

    Modeled separately so it can drift from reality (that drift is exactly what
    S-006 detects).
    """

    title: str | None = None
    updated: date | None = None
    open_issues: list[OpenIssueRef] = Field(default_factory=list)
