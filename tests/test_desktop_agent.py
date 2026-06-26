from __future__ import annotations

import asyncio
import threading
import time

import pytest

from hephaestus.contract import ExecutionContract
from hephaestus.integration.context import SessionContext
from hephaestus.integration.routing import Role, Tool
from hephaestus.integration.runners import AgentTask
from hephaestus.integration.service import PreparedRun
from hephaestus.store.threads import append_turn, get_or_create_thread


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
    assert '"category": "content"' in blob
    assert '"category": "transport"' in blob
    assert "do the thing" in blob         # prompt streamed back as a text event


def test_bridge_get_transcript_enriches_turn_metadata(tmp_path):
    from hephaestus.desktop import DesktopApp

    app = DesktopApp(tmp_path)
    profile = app._agents._resolve_profile(AgentTask(role=Role.ARCHITECT, prompt="hi"))
    thread = get_or_create_thread(
        app._workspace.state_db_path,
        agent_id=profile.agent_id,
        name="issue-011",
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
            self.role_calls = []
            self.profile_calls = []

        def begin_role_run(self, **kwargs):
            self.role_calls.append(kwargs)
            return PreparedRun(
                task=AgentTask(role=Role.ARCHITECT, prompt=kwargs["prompt"], issue_id=kwargs["issue_id"]),
                contract=ExecutionContract(
                    actor="arch-001",
                    role="architect",
                    context="thread-001",
                    scope="issue:012",
                    model=kwargs["model"],
                    effort=kwargs["effort"],
                    tools=[],
                    prompt=kwargs["prompt"],
                    tool=Tool.CLAUDE.value,
                    issue_id=kwargs["issue_id"],
                    cwd=kwargs["cwd"],
                ),
                agent_id="arch-001",
                thread_id="thread-001",
                run_id="run-001",
                tool=Tool.CLAUDE,
                ctx=SessionContext(role=Role.ARCHITECT, issue_id=kwargs["issue_id"], files=[], missing=[], system_prompt=""),
            )

        def begin_profile_run(self, **kwargs):
            self.profile_calls.append(kwargs)
            return PreparedRun(
                task=AgentTask(role=Role.WORKER, prompt=kwargs["prompt"], issue_id=kwargs["issue_id"], agent_id=kwargs["agent_id"]),
                contract=ExecutionContract(
                    actor=kwargs["agent_id"],
                    role="worker",
                    context="thread-002",
                    scope="issue:012",
                    model=kwargs["model"],
                    effort=None,
                    tools=[],
                    prompt=kwargs["prompt"],
                    tool=Tool.CODEX.value,
                    issue_id=kwargs["issue_id"],
                ),
                agent_id=kwargs["agent_id"],
                thread_id="thread-002",
                run_id="run-002",
                tool=Tool.CODEX,
                ctx=SessionContext(role=Role.WORKER, issue_id=kwargs["issue_id"], files=[], missing=[], system_prompt=""),
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
            "architect",
            "plan it",
            issue_id="issue-012",
            cwd=str(tmp_path / "repo"),
            model="gpt-5.4",
            effort="high",
        )
        profile_run = app.start_profile_agent("work-001", "ship it", issue_id="issue-012", model="gpt-5.5")
    finally:
        asyncio.run_coroutine_threadsafe = original

    assert app._agents.role_calls == [{
        "role": "architect",
        "prompt": "plan it",
        "issue_id": "issue-012",
        "cwd": str(tmp_path / "repo"),
        "model": "gpt-5.4",
        "effort": "high",
    }]
    assert app._agents.profile_calls == [{
        "agent_id": "work-001",
        "prompt": "ship it",
        "issue_id": "issue-012",
        "model": "gpt-5.5",
    }]
    assert role_run["run_id"] == "run-001"
    assert profile_run["run_id"] == "run-002"
