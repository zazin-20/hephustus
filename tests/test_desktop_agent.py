from __future__ import annotations

import asyncio
import threading
import time

import pytest


def test_desktop_streams_agent_events_via_bridge():
    """start_agent runs on the core loop and pushes events to the window (echo, no live calls)."""
    pytest.importorskip("webview")
    from hephaestus.desktop import DesktopApp
    from hephaestus.integration import EchoRunner, Tool

    app = DesktopApp("sample")
    app._agents.runners = {Tool.CLAUDE: EchoRunner(Tool.CLAUDE), Tool.CODEX: EchoRunner(Tool.CODEX)}

    pushed: list[str] = []

    class FakeWindow:
        def evaluate_js(self, js):
            pushed.append(js)

    app._window = FakeWindow()

    loop = asyncio.new_event_loop()
    app._loop = loop
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    try:
        res = app.start_agent("architect", "do the thing", None, None, None)
        assert res["tool"] == "claude"
        run_id = res["run_id"]

        deadline = time.time() + 3
        while time.time() < deadline:
            if any('"kind": "done"' in p for p in pushed):
                break
            time.sleep(0.02)
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=2)

    blob = "\n".join(pushed)
    assert run_id in blob
    assert '"kind": "done"' in blob       # stream terminated cleanly
    assert "do the thing" in blob         # prompt streamed back as a text event
