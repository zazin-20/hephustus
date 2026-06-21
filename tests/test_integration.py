from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from hephaestus.integration.context import SessionContext, build_session_context
from hephaestus.integration.routing import Role, Tool, tool_for
from hephaestus.integration.runners import AgentEvent, AgentTask, EchoRunner, build_codex_argv
from hephaestus.integration.service import AgentService, SessionRegistry


def test_routing_is_static_and_role_based():
    assert tool_for(Role.WORKER) is Tool.CODEX
    for role in (Role.ORCHESTRATOR, Role.PRODUCT_MANAGER, Role.ARCHITECT,
                 Role.QA, Role.DESIGNER, Role.DEVOPS):
        assert tool_for(role) is Tool.CLAUDE


def test_context_injects_directive_issue_and_tdd(tmp_path):
    a = tmp_path / "agents"
    (a / "worker").mkdir(parents=True)
    (a / "worker" / "claude.md").write_text("WORKER DIRECTIVE", encoding="utf-8")
    (a / "worker" / "tdd.md").write_text("TDD PLAYBOOK", encoding="utf-8")
    (a / "architect" / "issues").mkdir(parents=True)
    (a / "architect" / "issues" / "issue-009.md").write_text("ISSUE NINE SPEC", encoding="utf-8")

    ctx = build_session_context(tmp_path, Role.WORKER, "issue-009")
    assert {p.name for p in ctx.files} == {"claude.md", "tdd.md", "issue-009.md"}
    assert ctx.missing == []
    assert "WORKER DIRECTIVE" in ctx.system_prompt
    assert "ISSUE NINE SPEC" in ctx.system_prompt


def test_context_reports_missing_files(tmp_path):
    ctx = build_session_context(tmp_path, Role.ARCHITECT, "issue-001")
    assert ctx.files == []
    assert any(p.name == "architect.md" for p in ctx.missing)
    assert any(p.name == "issue-001.md" for p in ctx.missing)


def test_codex_event_parses_real_schema():
    """Locks in the codex-cli 0.130.0 JSONL schema observed in live testing."""
    from hephaestus.integration.runners import _codex_event

    msg = _codex_event({"type": "item.completed",
                        "item": {"id": "item_0", "type": "agent_message", "text": "HELLO"}})
    assert msg.kind == "text"
    assert msg.text == "HELLO"

    done = _codex_event({"type": "turn.completed", "usage": {"output_tokens": 3}})
    assert done.kind == "result"
    assert done.raw["usage"]["output_tokens"] == 3


def test_build_codex_argv():
    task = AgentTask(role=Role.WORKER, prompt="implement it", cwd=Path("/repo"), model="gpt-5")
    argv = build_codex_argv(task, output_file="out.txt")
    assert argv[0] == "exec"
    assert "--json" in argv and "--skip-git-repo-check" in argv
    assert argv[argv.index("-C") + 1] == str(Path("/repo"))
    assert argv[argv.index("-m") + 1] == "gpt-5"
    assert argv[argv.index("-o") + 1] == "out.txt"
    assert argv[-1] == "implement it"


def test_service_routes_worker_through_codex_echo():
    async def run():
        runners = {Tool.CLAUDE: EchoRunner(Tool.CLAUDE), Tool.CODEX: EchoRunner(Tool.CODEX)}
        service = AgentService("sample", runners=runners)
        task = AgentTask(role=Role.WORKER, prompt="hello worker", issue_id="issue-003")
        return [ev async for ev in service.run(task)]

    events = asyncio.run(run())
    assert "result" in {e.kind for e in events}
    joined = " ".join(e.text for e in events)
    assert "echo:codex" in joined          # routed to the codex backend
    assert "issue-003" in joined           # issue context threaded through
    assert "hello worker" in joined


def test_session_registry_keys():
    reg = SessionRegistry()
    reg.set(Role.ARCHITECT, "issue-003", "sess-abc")
    assert reg.get(Role.ARCHITECT, "issue-003") == "sess-abc"
    assert reg.key(Role.QA, None) == "qa"
    assert reg.key(Role.ARCHITECT, "issue-003") == "architect:issue-003"
    assert reg.all() == {"architect:issue-003": "sess-abc"}


def test_claude_options_actually_inject_context():
    """Guards the silent-drop bug: OKF context must reach ClaudeAgentOptions."""
    pytest.importorskip("claude_agent_sdk")
    from hephaestus.integration.runners import _claude_options

    ctx = SessionContext(role=Role.ARCHITECT, issue_id=None, files=[], missing=[],
                         system_prompt="OKF DIRECTIVE CONTENT")
    opts = _claude_options(ctx, AgentTask(role=Role.ARCHITECT, prompt="x"))
    assert "OKF DIRECTIVE CONTENT" in str(opts.system_prompt)


def test_service_resumes_captured_session():
    """A result event carrying a session id is stored and reused on the next run."""
    class _OneShot:
        tool = Tool.CLAUDE

        def __init__(self):
            self.seen_resume = []

        async def run(self, task, ctx):
            self.seen_resume.append(task.resume)
            yield AgentEvent("result", "done", raw={"session_id": "sess-xyz"})

    runner = _OneShot()
    service = AgentService("sample", runners={Tool.CLAUDE: runner, Tool.CODEX: runner})

    async def go():
        task = AgentTask(role=Role.ARCHITECT, prompt="first", issue_id="issue-001")
        async for _ in service.run(task):
            pass
        async for _ in service.run(AgentTask(role=Role.ARCHITECT, prompt="second", issue_id="issue-001")):
            pass

    asyncio.run(go())
    assert runner.seen_resume == [None, "sess-xyz"]  # second run resumed the captured session
