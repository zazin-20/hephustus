from __future__ import annotations

from pathlib import Path

from hephaestus.desktop import DesktopApp, PROJECT_ROOT
from hephaestus.workspace import Workspace, discover_service_roots


def _make_workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / "agents").mkdir(parents=True)
    (root / "service-a" / ".git").mkdir(parents=True)
    (root / "service-b" / ".git").mkdir(parents=True)
    (root / "archive" / ".git").mkdir(parents=True)
    (root / "node_modules" / ".git").mkdir(parents=True)
    (root / "notes").mkdir()
    return root


def test_discover_service_roots_filters_top_level_git_dirs(tmp_path):
    root = _make_workspace(tmp_path)

    discovered = discover_service_roots(root)

    assert [path.name for path in discovered] == ["service-a", "service-b"]


def test_workspace_open_creates_operational_store(tmp_path):
    root = _make_workspace(tmp_path)

    workspace = Workspace.open(root)

    assert workspace.root == root.resolve()
    assert workspace.state_db_path == root.resolve() / ".hephaestus" / "state.db"
    assert workspace.state_db_path.exists()
    assert [path.name for path in workspace.service_roots] == ["service-a", "service-b"]


def test_workspace_open_accepts_explicit_service_roots(tmp_path):
    root = _make_workspace(tmp_path)
    explicit = [root / "service-b"]

    workspace = Workspace.open(root, service_roots=explicit)

    assert list(workspace.service_roots) == [explicit[0].resolve()]


def test_desktop_app_uses_workspace_code_roots_by_default(tmp_path):
    root = _make_workspace(tmp_path)

    app = DesktopApp(root)
    repo_names = [repo["name"] for repo in app._bridge.list_repos()]

    assert repo_names == ["service-a", "service-b", "workspace"]
    assert PROJECT_ROOT.name not in repo_names


def test_operational_store_directory_is_gitignored():
    content = Path(".gitignore").read_text(encoding="utf-8")

    assert ".hephaestus/" in content
