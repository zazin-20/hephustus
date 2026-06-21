from __future__ import annotations

import pytest

from hephaestus.codeview import CodeViewer


def _make_repo(tmp_path):
    repo = tmp_path / "myrepo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (repo / "README.md").write_text("# hi\n", encoding="utf-8")
    (repo / "node_modules").mkdir()
    (repo / "node_modules" / "x.js").write_text("x\n", encoding="utf-8")
    return repo


def test_list_repos_and_tree(tmp_path):
    cv = CodeViewer([_make_repo(tmp_path)])
    assert cv.list_repos()[0]["name"] == "myrepo"

    top = cv.tree("myrepo")
    by_name = {e["name"]: e["type"] for e in top}
    assert by_name["src"] == "dir"
    assert by_name["README.md"] == "file"
    assert "node_modules" not in by_name        # ignored
    assert top[0]["type"] == "dir"              # dirs sorted first

    sub = cv.tree("myrepo", "src")
    assert sub[0]["name"] == "main.py"


def test_read_file_detects_language(tmp_path):
    cv = CodeViewer([_make_repo(tmp_path)])
    f = cv.read_file("myrepo", "src/main.py")
    assert f["language"] == "python"
    assert "print" in f["content"]
    assert f["binary"] is False and f["truncated"] is False


def test_path_traversal_is_blocked(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    (tmp_path / "secret.txt").write_text("SECRET", encoding="utf-8")
    cv = CodeViewer([repo])
    with pytest.raises(ValueError):
        cv.read_file("r", "../secret.txt")
    with pytest.raises(ValueError):
        cv.tree("r", "../")


def test_binary_detection_and_unknown_repo(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    (repo / "b.bin").write_bytes(b"\x00\x01\x02BIN")
    cv = CodeViewer([repo])
    assert cv.read_file("r", "b.bin")["binary"] is True
    with pytest.raises(ValueError):
        cv.tree("nope")
