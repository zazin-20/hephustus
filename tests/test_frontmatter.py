from __future__ import annotations

import pytest

from hephaestus.frontmatter import FrontmatterError, parse


def test_parses_frontmatter_and_body():
    doc = parse("---\nid: issue-1\nstatus: open\n---\n# Title\nbody text")
    assert doc.frontmatter == {"id": "issue-1", "status": "open"}
    assert "body text" in doc.body


def test_no_fence_is_all_body():
    doc = parse("just markdown, no frontmatter")
    assert doc.frontmatter == {}
    assert doc.body == "just markdown, no frontmatter"


def test_unterminated_fence_raises():
    with pytest.raises(FrontmatterError):
        parse("---\nid: issue-1\nstill going...")


def test_non_mapping_frontmatter_raises():
    with pytest.raises(FrontmatterError):
        parse("---\n- a\n- b\n---\n")
