"""Read-only multi-repo code viewer (spec/architecture.md §3.4).

Filesystem reads are constrained to configured repo roots — no writes, and no
traversal outside a root. Returns JSON-serializable data for the UI. OQ-4 is
resolved for the MVP in favour of explicit path config (not git auto-discovery).
"""
from __future__ import annotations

from pathlib import Path

_IGNORE = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".pytest_tmp",
    ".ruff_cache", ".mypy_cache", "dist", "build", ".venv", "venv",
    ".idea", ".vscode", ".egg-info",
}
_MAX_BYTES = 1_000_000

_LANG = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".json": "json",
    ".md": "markdown", ".css": "css", ".html": "html", ".htm": "html",
    ".toml": "ini", ".yaml": "yaml", ".yml": "yaml", ".sh": "bash",
    ".bash": "bash", ".cfg": "ini", ".ini": "ini",
}


class CodeViewer:
    def __init__(self, roots):
        self._roots: dict[str, Path] = {}
        for r in roots:
            p = Path(r).resolve()
            if p.is_dir():
                self._roots[p.name] = p

    def list_repos(self) -> list[dict]:
        return [{"name": n, "path": str(p)} for n, p in sorted(self._roots.items())]

    def _root(self, repo: str) -> Path:
        root = self._roots.get(repo)
        if root is None:
            raise ValueError(f"unknown repo: {repo}")
        return root

    def _safe(self, repo: str, rel: str) -> Path:
        root = self._root(repo)
        target = (root / rel).resolve()
        if target != root and root not in target.parents:
            raise ValueError("path escapes repo root")
        return target

    def tree(self, repo: str, subpath: str = "") -> list[dict]:
        base = self._safe(repo, subpath)
        if not base.is_dir():
            raise ValueError("not a directory")
        root = self._root(repo)
        entries = []
        for child in sorted(base.iterdir(), key=lambda c: (c.is_file(), c.name.lower())):
            if child.name in _IGNORE:
                continue
            entries.append({
                "name": child.name,
                "type": "dir" if child.is_dir() else "file",
                "path": child.relative_to(root).as_posix(),
            })
        return entries

    def read_file(self, repo: str, relpath: str) -> dict:
        target = self._safe(repo, relpath)
        if not target.is_file():
            raise ValueError("not a file")
        size = target.stat().st_size
        lang = _LANG.get(target.suffix.lower(), "plaintext")
        base = {"repo": repo, "path": relpath, "language": lang, "size": size}
        if size > _MAX_BYTES:
            return {**base, "binary": False, "truncated": True, "content": ""}
        data = target.read_bytes()
        if b"\x00" in data[:4096]:
            return {**base, "binary": True, "truncated": False, "content": ""}
        return {**base, "binary": False, "truncated": False, "content": data.decode("utf-8", "replace")}
