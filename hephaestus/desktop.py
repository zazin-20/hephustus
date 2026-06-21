"""PyWebView desktop shell (spec/architecture.md §5.4, §8).

Runs the Python core in-process behind a native OS webview (WebView2 on Windows,
WKWebView on macOS). The asyncio core loop — hosting the OKF watcher — runs on a
daemon thread; pywebview's GUI loop owns the main thread. File-change deltas are
pushed to the UI via `window.evaluate_js`; the UI pulls initial state through the
`js_api` bridge.

Launch:  py -m hephaestus.desktop [root]
(Requires the built frontend and pywebview: `pip install -e .[app]`.)
"""
from __future__ import annotations

import asyncio
import json
import threading
import uuid
from pathlib import Path

from hephaestus.codeview import CodeViewer
from hephaestus.dashboard import snapshot
from hephaestus.integration import AgentService, AgentTask, Role
from hephaestus.watch import OKFWatcher
from hephaestus.workspace import Workspace

try:
    import webview

    HAS_WEBVIEW = True
except ImportError:  # pragma: no cover - exercised only when extra is absent
    webview = None  # type: ignore[assignment]
    HAS_WEBVIEW = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist" / "index.html"


class Bridge:
    """Exposed to JS as `window.pywebview.api`."""

    def __init__(self, root: Path, code_roots: list[Path], app: DesktopApp | None = None):
        self._root = root
        self._code = CodeViewer(code_roots)
        self._app = app

    # Compliance / dashboard
    def get_state(self) -> dict:
        return snapshot(self._root)

    def rescan(self) -> dict:
        return snapshot(self._root)

    # Code viewer (read-only)
    def list_repos(self) -> list[dict]:
        return self._code.list_repos()

    def tree(self, repo: str, subpath: str = "") -> list[dict]:
        return self._code.tree(repo, subpath)

    def read_file(self, repo: str, relpath: str) -> dict:
        return self._code.read_file(repo, relpath)

    # Agents (§5) — returns run metadata; events stream via window.__hephaestus_agent__
    def run_agent(self, role: str, prompt: str, issue_id=None, cwd=None, model=None) -> dict:
        if self._app is None:
            raise RuntimeError("no app bound to bridge")
        return self._app.start_agent(role, prompt, issue_id, cwd, model)


class DesktopApp:
    def __init__(self, root: str | Path, code_roots: list[Path] | None = None):
        self._workspace = Workspace.open(root)
        self._root = self._workspace.root
        roots = code_roots or self._workspace.code_roots
        seen, deduped = set(), []
        for r in roots:
            rp = Path(r).resolve()
            if rp not in seen:
                seen.add(rp)
                deduped.append(rp)
        self._bridge = Bridge(self._root, deduped, app=self)
        self._agents = AgentService(self._root)
        self._window = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._watcher: OKFWatcher | None = None

    def _push(self, _delta) -> None:
        """Recompute the full snapshot and push it to the UI (guarded in JS)."""
        if self._window is None:
            return
        payload = json.dumps(snapshot(self._root))
        self._window.evaluate_js(
            f"window.__hephaestus_push__ && window.__hephaestus_push__({payload})"
        )

    def _start_core(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._watcher = OKFWatcher(self._root, self._push, delay=0.2)
        loop.run_until_complete(self._watcher.start())
        loop.run_forever()

    # --- Agents (§5): run on the core loop, stream events to the UI ---
    def start_agent(self, role, prompt, issue_id=None, cwd=None, model=None) -> dict:
        if self._loop is None:
            raise RuntimeError("core loop not started yet")
        task = AgentTask(
            role=Role(role),
            prompt=prompt,
            issue_id=issue_id or None,
            cwd=Path(cwd) if cwd else None,
            model=model or None,
        )
        tool, ctx = self._agents.resolve(task)
        run_id = uuid.uuid4().hex[:8]
        asyncio.run_coroutine_threadsafe(self._stream_agent(run_id, task), self._loop)
        return {
            "run_id": run_id,
            "role": task.role.value,
            "tool": tool.value,
            "context": [p.name for p in ctx.files],
            "missing": [p.name for p in ctx.missing],
        }

    async def _stream_agent(self, run_id: str, task: AgentTask) -> None:
        try:
            async for ev in self._agents.run(task):
                self._push_agent(run_id, ev.kind, ev.text)
        except Exception as exc:  # surface failures to the UI, don't die silently
            self._push_agent(run_id, "error", str(exc))
        finally:
            self._push_agent(run_id, "done", "")

    def _push_agent(self, run_id: str, kind: str, text: str) -> None:
        if self._window is None:
            return
        payload = json.dumps({"run_id": run_id, "kind": kind, "text": text})
        self._window.evaluate_js(
            f"window.__hephaestus_agent__ && window.__hephaestus_agent__({payload})"
        )

    def run(self) -> None:
        if not HAS_WEBVIEW:
            raise RuntimeError("pywebview not installed; run: pip install -e .[app]")
        if not FRONTEND_DIST.exists():
            raise RuntimeError(
                "frontend not built — run:\n"
                "  npm --prefix frontend install\n"
                "  npm --prefix frontend run build\n"
                f"(missing {FRONTEND_DIST})"
            )
        self._window = webview.create_window(
            "Hephaestus",
            url=str(FRONTEND_DIST),
            js_api=self._bridge,
            width=1280,
            height=820,
            min_size=(960, 600),
        )
        threading.Thread(target=self._start_core, daemon=True).start()
        webview.start()


def main(argv: list[str] | None = None) -> int:
    import sys

    args = argv if argv is not None else sys.argv[1:]
    root = args[0] if args else "."
    if not HAS_WEBVIEW:
        print("pywebview not installed. Install with: pip install -e .[app]")
        return 1
    DesktopApp(root).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
