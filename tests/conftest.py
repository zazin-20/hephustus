"""Fixture OKF trees built in tmp_path.

Building trees programmatically (rather than committing fixture files) keeps the
expected violations next to the rule they exercise and makes the trees easy to
tweak. See spec/architecture.md §8 (testing) and §6.3.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def write_doc(path: Path, frontmatter: dict, body: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = yaml.safe_dump(frontmatter, sort_keys=False).strip()
    path.write_text(f"---\n{fm}\n---\n{body}\n", encoding="utf-8")
    return path


@pytest.fixture
def write_okf():
    """Expose the doc writer to tests that mutate a tree after building it."""
    return write_doc


@pytest.fixture
def clean_tree(tmp_path: Path) -> Path:
    """A tree that satisfies every structural rule."""
    a = tmp_path / "clean" / "agents"

    # issue-001: a fully completed, well-formed pipeline loop
    write_doc(a / "architect" / "issues" / "issue-001.md",
              {"id": "issue-001", "status": "done", "role": "worker",
               "sprint": "sprint-01", "created": "2026-06-01", "title": "Auth module"})
    write_doc(a / "architect" / "handoffs" / "issue-001.md",
              {"issue_id": "issue-001", "worker": "codex", "status": "complete",
               "created": "2026-06-02", "reviewed_by": "architect"})
    write_doc(a / "qa" / "evidence" / "issue-001.md",
              {"issue_id": "issue-001", "result": "pass", "created": "2026-06-03"})
    write_doc(a / "log" / "issue-001.md",
              {"issue_id": "issue-001", "sprint": "sprint-01", "date": "2026-06-03",
               "worker": "codex", "qa": "passed", "sprint_closed": True})

    # issue-002: legitimately open in an open sprint
    write_doc(a / "architect" / "issues" / "issue-002.md",
              {"id": "issue-002", "status": "open", "role": "worker",
               "sprint": "sprint-02", "created": "2026-06-10"})
    write_doc(a / "architect" / "issues" / "index.md",
              {"title": "Issues", "updated": "2026-06-10",
               "open_issues": [{"id": "issue-002", "sprint": "sprint-02"}]})

    return a.parent  # the repo root containing agents/


@pytest.fixture
def violations_tree(tmp_path: Path) -> Path:
    """A tree crafted to trigger each of S-001 .. S-006 at least once."""
    a = tmp_path / "bad" / "agents"

    # S-001: handoff referencing an issue with no spec
    write_doc(a / "architect" / "handoffs" / "issue-777.md",
              {"issue_id": "issue-777", "worker": "codex", "status": "complete",
               "created": "2026-06-02", "reviewed_by": "architect"})

    # S-002: done issue with no handoff
    write_doc(a / "architect" / "issues" / "issue-010.md",
              {"id": "issue-010", "status": "done", "role": "worker",
               "sprint": "sprint-03", "created": "2026-06-01"})

    # S-003: logged but no QA evidence
    write_doc(a / "architect" / "issues" / "issue-011.md",
              {"id": "issue-011", "status": "done", "role": "worker",
               "sprint": "sprint-03", "created": "2026-06-01"})
    write_doc(a / "architect" / "handoffs" / "issue-011.md",
              {"issue_id": "issue-011", "worker": "codex", "status": "complete",
               "created": "2026-06-02", "reviewed_by": "architect"})
    write_doc(a / "log" / "issue-011.md",
              {"issue_id": "issue-011", "sprint": "sprint-03", "date": "2026-06-03",
               "sprint_closed": False})

    # S-005: QA evidence but handoff not architect-reviewed
    write_doc(a / "architect" / "issues" / "issue-012.md",
              {"id": "issue-012", "status": "done", "role": "worker",
               "sprint": "sprint-03", "created": "2026-06-01"})
    write_doc(a / "architect" / "handoffs" / "issue-012.md",
              {"issue_id": "issue-012", "worker": "codex", "status": "complete",
               "created": "2026-06-02"})
    write_doc(a / "qa" / "evidence" / "issue-012.md",
              {"issue_id": "issue-012", "result": "pass", "created": "2026-06-03"})

    # S-004: done + QA evidence + reviewed handoff but no log entry
    write_doc(a / "architect" / "issues" / "issue-013.md",
              {"id": "issue-013", "status": "done", "role": "worker",
               "sprint": "sprint-03", "created": "2026-06-01"})
    write_doc(a / "architect" / "handoffs" / "issue-013.md",
              {"issue_id": "issue-013", "worker": "codex", "status": "complete",
               "created": "2026-06-02", "reviewed_by": "architect"})
    write_doc(a / "qa" / "evidence" / "issue-013.md",
              {"issue_id": "issue-013", "result": "pass", "created": "2026-06-03"})

    # S-006: index lists an open issue whose sprint the log marks closed
    write_doc(a / "architect" / "issues" / "issue-014.md",
              {"id": "issue-014", "status": "open", "role": "worker",
               "sprint": "sprint-09", "created": "2026-06-01"})
    write_doc(a / "log" / "issue-099.md",
              {"issue_id": "issue-099", "sprint": "sprint-09", "date": "2026-06-05",
               "sprint_closed": True})
    write_doc(a / "architect" / "issues" / "index.md",
              {"title": "Issues", "updated": "2026-06-10",
               "open_issues": [{"id": "issue-014", "sprint": "sprint-09"}]})

    return a.parent
