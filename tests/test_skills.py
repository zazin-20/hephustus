from __future__ import annotations

from hephaestus.okf_layout import OKFLayout
from hephaestus.skills import resolve_skill_ref, resolve_skill_refs


def test_resolve_skill_ref_uses_registry_path_for_prefixed_skill():
    layout = OKFLayout.for_workspace("/repo")

    ref = resolve_skill_ref(layout, "skill:grill-me")

    assert ref.skill_id == "grill-me"
    assert ref.path == layout.skill_path("grill-me")


def test_resolve_skill_ref_accepts_bare_registry_name():
    layout = OKFLayout.for_workspace("/repo")

    ref = resolve_skill_ref(layout, "grill-me")

    assert ref.skill_id == "grill-me"
    assert ref.path == layout.skill_path("grill-me")


def test_resolve_skill_ref_preserves_explicit_markdown_path(tmp_path):
    layout = OKFLayout.for_workspace(tmp_path)

    ref = resolve_skill_ref(layout, "skills/custom.md")

    assert ref.skill_id == "custom"
    assert ref.path == layout.resolve("skills/custom.md")


def test_resolve_skill_refs_keeps_reference_order():
    layout = OKFLayout.for_workspace("/repo")

    refs = resolve_skill_refs(layout, ["skill:grill-me", "skill:tdd"])

    assert [ref.skill_id for ref in refs] == ["grill-me", "tdd"]
