from __future__ import annotations

from hephaestus.okf_layout import OKFLayout


def test_for_existing_root_points_missing_agents_tree_at_canonical_location(tmp_path):
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    layout = OKFLayout.for_existing_root(workspace_root)

    assert layout.workspace_root == workspace_root
    assert layout.agents_root == workspace_root / "agents"
    assert layout.issue_path("issue-010") == workspace_root / "agents" / "architect" / "issues" / "issue-010.md"


def test_for_workspace_accepts_agents_directory_directly(tmp_path):
    agents_root = tmp_path / "workspace" / "agents"
    agents_root.mkdir(parents=True)

    layout = OKFLayout.for_workspace(agents_root)

    assert layout.workspace_root == agents_root.parent
    assert layout.agents_root == agents_root
    assert layout.identity_card_path("work-001") == agents_root / "identities" / "work-001.json"
