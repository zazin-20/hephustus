from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from hephaestus.models import Handoff, IssueSpec, IssueStatus


def test_issue_spec_parses_required_fields():
    spec = IssueSpec.model_validate(
        {"id": "issue-1", "status": "in-progress", "role": "worker",
         "sprint": "sprint-01", "created": "2026-06-01"}
    )
    assert spec.status is IssueStatus.IN_PROGRESS
    assert spec.created == date(2026, 6, 1)


def test_issue_spec_rejects_unknown_status():
    with pytest.raises(ValidationError):
        IssueSpec.model_validate(
            {"id": "x", "status": "bogus", "role": "worker",
             "sprint": "s", "created": "2026-06-01"}
        )


def test_issue_spec_requires_fields():
    with pytest.raises(ValidationError):
        IssueSpec.model_validate({"id": "x"})


def test_handoff_reviewed_by_coercion():
    as_str = Handoff.model_validate(
        {"issue_id": "i", "worker": "codex", "status": "done",
         "created": "2026-06-01", "reviewed_by": "architect"}
    )
    assert as_str.reviewed_by == ["architect"]

    missing = Handoff.model_validate(
        {"issue_id": "i", "worker": "codex", "status": "done", "created": "2026-06-01"}
    )
    assert missing.reviewed_by == []


def test_extra_fields_allowed():
    spec = IssueSpec.model_validate(
        {"id": "i", "status": "open", "role": "worker", "sprint": "s",
         "created": "2026-06-01", "owner": "alice", "priority": "high"}
    )
    assert spec.model_extra["owner"] == "alice"
