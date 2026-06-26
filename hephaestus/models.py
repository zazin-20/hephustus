"""Pydantic base for OKF documents.

REUSABLE — generic artifact-schema base. `OKFModel` is the frontmatter-validation
primitive for *user-authored* artifact specs (the predicate library checks a doc;
typed schemas like this one are the optional strict path). The hardcoded
issue-lifecycle document classes (IssueSpec, Handoff, QAEvidence, LogEntry,
IssuesIndex) were removed when governance moved to user-authored specs — only the
reusable base remains. See docs/design/governance-engine.md.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OKFModel(BaseModel):
    """Base for OKF artifact frontmatter. `extra="allow"` lets documents carry
    human-facing fields without failing validation, while required fields a
    subclass declares are still enforced."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)
