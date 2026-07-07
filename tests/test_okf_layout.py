from __future__ import annotations

from hephaestus.okf_layout import OKFLayout


def test_layout_for_workspace_builds_canonical_paths(tmp_path):
    layout = OKFLayout.for_workspace(tmp_path)

    assert layout.workspace_root == tmp_path
    assert layout.agents_root == tmp_path / "agents"
    assert layout.issues_index_path() == tmp_path / "agents" / "architect" / "issues" / "index.md"
    assert layout.issue_path("issue-010") == tmp_path / "agents" / "architect" / "issues" / "issue-010.md"
    assert layout.handoff_path("issue-010") == tmp_path / "agents" / "architect" / "handoffs" / "issue-010.md"
    assert layout.qa_evidence_path("issue-010") == tmp_path / "agents" / "qa" / "evidence" / "issue-010.md"
    assert layout.log_entry_path("issue-010") == tmp_path / "agents" / "log" / "issue-010.md"
    assert layout.identity_card_path("work-001") == tmp_path / "agents" / "identities" / "work-001.json"
    assert layout.workflow_path("issue-020") == tmp_path / "agents" / "workflows" / "issue-020.yaml"
    assert layout.skill_path("grill-me") == tmp_path / "agents" / "skills" / "grill-me.md"
    assert layout.artifacts_dir == tmp_path / "agents" / "artifacts"
    assert layout.worker_tdd_path() == tmp_path / "agents" / "worker" / "tdd.md"


def test_layout_for_existing_root_accepts_agents_directory(tmp_path):
    agents_root = tmp_path / "agents"
    agents_root.mkdir()

    layout = OKFLayout.for_existing_root(agents_root)

    assert layout.workspace_root == tmp_path
    assert layout.agents_root == agents_root
    assert layout.resolve("worker/claude.md") == agents_root / "worker" / "claude.md"
