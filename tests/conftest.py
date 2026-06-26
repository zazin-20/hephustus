"""Fixture OKF trees built in tmp_path.

Built programmatically so the expected state sits next to the test. The hardcoded
issue-lifecycle fixtures were replaced when governance moved to user-authored
specs; what remains are generic trees: a clean one and one with a malformed
document (a Tier-1 schema load error).
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


def write_broken(path: Path) -> Path:
    """Write a document with an unterminated frontmatter fence (a schema error)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nid: broken\nunterminated", encoding="utf-8")
    return path


@pytest.fixture
def write_okf():
    """Expose the doc writer to tests that mutate a tree after building it."""
    return write_doc


@pytest.fixture
def clean_tree(tmp_path: Path) -> Path:
    """A well-formed tree: documents parse, no load errors."""
    a = tmp_path / "clean" / "agents"
    write_doc(a / "architect" / "issues" / "doc-001.md",
              {"id": "doc-001", "title": "A document"}, "Body text.")
    return a.parent  # the repo root containing agents/


@pytest.fixture
def schema_error_tree(tmp_path: Path) -> Path:
    """A tree with one malformed document -> one Tier-1 schema load error."""
    a = tmp_path / "bad" / "agents"
    write_broken(a / "architect" / "issues" / "broken.md")
    return a.parent
