from __future__ import annotations

import asyncio
from pathlib import Path
import threading
import time

import pytest

from hephaestus.contract import ExecutionContract
from hephaestus.integration.context import SessionContext
from hephaestus.integration.runners import AgentTask
from hephaestus.integration.service import PreparedRun
from hephaestus.store.nodes import create_node
from hephaestus.store.threads import append_turn, get_or_create_thread
from hephaestus.workflows import load_workflow


def test_desktop_streams_agent_events_via_bridge():
    """start_agent runs on the core loop and pushes events to the window (echo, no live calls)."""
    pytest.importorskip("webview")
    from hephaestus.desktop import DesktopApp
    from hephaestus.integration import EchoRunner

    app = DesktopApp("sample")
    app._agents.runners = {"claude": EchoRunner("claude"), "codex": EchoRunner("codex")}

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
        res = app.start_agent("claude", ["architect"], "do the thing", None, None, None)
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
    assert '"category": "content"' in blob
    assert '"category": "transport"' in blob
    assert "do the thing" in blob         # prompt streamed back as a text event


def test_bridge_get_transcript_enriches_turn_metadata(tmp_path):
    from hephaestus.desktop import DesktopApp

    app = DesktopApp(tmp_path)
    node = create_node(app._workspace.state_db_path, tmp_path, "Architect", "claude", ["architect"], [])
    thread = get_or_create_thread(
        app._workspace.state_db_path,
        node_id=node.node_id,
        name="issue-011",
        workflow_id="issue-011",
        workflow_run_id="run-011",
        placement_id=node.node_id,
        issue_id="issue-011",
    )
    append_turn(app._workspace.state_db_path, thread.id, role="user", kind="text", text="hello")
    append_turn(app._workspace.state_db_path, thread.id, role="assistant", kind="thinking", text="reasoning")
    append_turn(app._workspace.state_db_path, thread.id, role="tool", kind="tool_call", text="shell")

    turns = app._bridge.get_transcript(thread.id)

    assert [(turn["label"], turn["category"]) for turn in turns] == [
        ("user", "user"),
        ("think", "thinking"),
        ("tool", "tool"),
    ]
    assert [turn["conversation"] for turn in turns] == [True, True, False]
    assert [turn["transcript_role"] for turn in turns] == ["user", "assistant", "tool"]


def test_desktop_forwards_run_construction_to_agent_service(tmp_path):
    from hephaestus.desktop import DesktopApp

    app = DesktopApp(tmp_path)

    class FakeService:
        def __init__(self):
            self.ad_hoc_calls = []
            self.node_calls = []

        def begin_ad_hoc_run(self, **kwargs):
            self.ad_hoc_calls.append(kwargs)
            return PreparedRun(
                task=AgentTask(node_id=None, provider=kwargs["provider"], tags=kwargs["tags"], prompt=kwargs["prompt"], issue_id=kwargs["issue_id"]),
                contract=ExecutionContract(
                    actor="node-001",
                    node_id="node-001",
                    provider=kwargs["provider"],
                    tags=kwargs["tags"],
                    context="thread-001",
                    scope="workflow:issue-012/placement:node-001",
                    model=kwargs["model"],
                    effort=kwargs["effort"],
                    tools=[],
                    prompt=kwargs["prompt"],
                    tool="claude",
                    issue_id=kwargs["issue_id"],
                    cwd=kwargs["cwd"],
                ),
                node_id="node-001",
                thread_id="thread-001",
                run_id="run-001",
                tool="claude",
                ctx=SessionContext(node_id="node-001", tags=kwargs["tags"], issue_id=kwargs["issue_id"], files=[], missing=[], system_prompt=""),
            )

        def begin_node_run(self, **kwargs):
            self.node_calls.append(kwargs)
            return PreparedRun(
                task=AgentTask(node_id=kwargs["node_id"], provider="codex", tags=["worker"], prompt=kwargs["prompt"], issue_id=kwargs["issue_id"]),
                contract=ExecutionContract(
                    actor=kwargs["node_id"],
                    node_id=kwargs["node_id"],
                    provider="codex",
                    tags=["worker"],
                    context="thread-002",
                    scope="workflow:issue-012/placement:node-002",
                    model=kwargs["model"],
                    effort=None,
                    tools=[],
                    prompt=kwargs["prompt"],
                    tool="codex",
                    issue_id=kwargs["issue_id"],
                ),
                node_id=kwargs["node_id"],
                thread_id="thread-002",
                run_id="run-002",
                tool="codex",
                ctx=SessionContext(node_id=kwargs["node_id"], tags=["worker"], issue_id=kwargs["issue_id"], files=[], missing=[], system_prompt=""),
            )

    app._agents = FakeService()
    app._loop = asyncio.new_event_loop()

    class _DummyFuture:
        def result(self, timeout=None):
            return None

    def _capture_and_close(coro, loop):
        coro.close()
        return _DummyFuture()

    original = asyncio.run_coroutine_threadsafe
    asyncio.run_coroutine_threadsafe = _capture_and_close
    try:
        role_run = app.start_agent(
            "claude",
            ["architect"],
            "plan it",
            issue_id="issue-012",
            cwd=str(tmp_path / "repo"),
            model="gpt-5.4",
            effort="high",
        )
        profile_run = app.start_node_agent("node-002", "ship it", issue_id="issue-012", model="gpt-5.5")
    finally:
        asyncio.run_coroutine_threadsafe = original

    assert app._agents.ad_hoc_calls == [{
        "provider": "claude",
        "tags": ["architect"],
        "prompt": "plan it",
        "issue_id": "issue-012",
        "cwd": str(tmp_path / "repo"),
        "model": "gpt-5.4",
        "effort": "high",
    }]
    assert app._agents.node_calls == [{
        "node_id": "node-002",
        "prompt": "ship it",
        "issue_id": "issue-012",
        "model": "gpt-5.5",
    }]
    assert role_run["run_id"] == "run-001"
    assert profile_run["run_id"] == "run-002"


def test_bridge_save_workflow_persists_canvas_payload(tmp_path):
    from hephaestus.desktop import Bridge

    app_root = tmp_path
    bridge = Bridge(app_root, [])

    saved = bridge.save_workflow(
        {
            "workflow_id": "issue-025",
            "placements": [
                {
                    "placement_id": "draft",
                    "node_id": "node-001",
                    "x": 120,
                    "y": 80,
                    "interactivity": "hitl",
                }
            ],
            "edges": [],
        },
        ".json",
    )

    assert Path(saved["path"]).as_posix().endswith("agents/workflows/issue-025.json")
    assert load_workflow(app_root / "agents" / "workflows" / "issue-025.json").placements[0].interactivity.value == "hitl"


def test_bridge_run_workflow_forwards_to_app():
    from hephaestus.desktop import Bridge

    class FakeApp:
        def __init__(self):
            self.calls = []

        def start_workflow(self, workflow_id, prompts):
            self.calls.append((workflow_id, prompts))
            return {"workflow_id": workflow_id, "status": "running"}

    app = FakeApp()
    bridge = Bridge("sample", [], app=app)

    result = bridge.run_workflow("issue-025", {"draft": "ship it"})

    assert app.calls == [("issue-025", {"draft": "ship it"})]
    assert result == {"workflow_id": "issue-025", "status": "running"}
