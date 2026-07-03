from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from hephaestus.contract import ExecutionContract
from hephaestus.integration.context import SessionContext, build_session_context
from hephaestus.integration.providers import (
    _claude_flags,
    _claude_normalize_event,
    _codex_normalize_event,
)
from hephaestus.integration.routing import Role, Tool, tool_for
from hephaestus.integration.runners import (
    AgentEvent,
    AgentTask,
    ClaudeRunner,
    CodexRunner,
    EchoRunner,
    build_codex_argv,
)
from hephaestus.integration.service import AgentService, PreparedRun, SessionRegistry
from hephaestus.store.db import connect
from hephaestus.store.profiles import create_profile
from hephaestus.store.runs import get_run
from hephaestus.store.threads import list_turns
from hephaestus.store.violations import list_violations


def _contract(**kwargs) -> ExecutionContract:
    defaults = dict(
        actor="work-001",
        role="worker",
        context="thread-001",
        scope="issue:001",
        model="gpt-5.4",
        effort=None,
        tools=[],
        prompt="go",
    )
    defaults.update(kwargs)
    return ExecutionContract(**defaults)


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
    msg = _codex_normalize_event(
        {"type": "item.completed", "item": {"id": "item_0", "type": "agent_message", "text": "HELLO"}}
    )
    assert msg.kind == "text"
    assert msg.text == "HELLO"

    done = _codex_normalize_event({"type": "turn.completed", "usage": {"output_tokens": 3}})
    assert done.kind == "result"
    assert done.raw["usage"]["output_tokens"] == 3


def test_build_codex_argv():
    argv = build_codex_argv(
        _contract(prompt="implement it", cwd=str(Path("/repo")), model="gpt-5"),
        output_file="out.txt",
    )
    assert argv[0] == "exec"
    assert "--json" in argv and "--skip-git-repo-check" in argv
    assert argv[argv.index("-C") + 1] == str(Path("/repo"))
    assert argv[argv.index("-m") + 1] == "gpt-5"
    assert argv[argv.index("-o") + 1] == "out.txt"
    assert argv[-1] == "implement it"


def test_build_codex_argv_passes_effort_via_config():
    argv = build_codex_argv(_contract(effort="high"))
    assert 'model_reasoning_effort="high"' in argv
    assert 'sandbox_mode="danger-full-access"' in argv
    assert 'approval_policy="manual"' in argv


def test_build_codex_argv_omits_effort_when_unset():
    argv = build_codex_argv(_contract(effort=None))
    assert 'model_reasoning_effort="high"' not in argv
    assert 'approval_policy="auto"' in argv


def test_resolve_routes_by_model_provider(tmp_path):
    """The chosen model decides the runner, overriding role-based routing."""
    runners = {Tool.CLAUDE: EchoRunner(Tool.CLAUDE), Tool.CODEX: EchoRunner(Tool.CODEX)}
    service = AgentService(tmp_path, runners=runners)

    # architect normally -> Claude, but a Codex model forces Codex
    tool, _ = service.resolve(AgentTask(role=Role.ARCHITECT, prompt="x", model="gpt-5.4"))
    assert tool == Tool.CODEX
    # worker normally -> Codex, but a Claude alias forces Claude
    tool2, _ = service.resolve(AgentTask(role=Role.WORKER, prompt="x", model="opus"))
    assert tool2 == Tool.CLAUDE
    # no model -> role default
    assert service.resolve(AgentTask(role=Role.ARCHITECT, prompt="x"))[0] == Tool.CLAUDE
    assert service.resolve(AgentTask(role=Role.WORKER, prompt="x"))[0] == Tool.CODEX


def test_provider_for_model_classifies():
    from hephaestus.catalog import provider_for_model

    assert provider_for_model("opus") == Tool.CLAUDE.value
    assert provider_for_model("claude-opus-4-8") == Tool.CLAUDE.value
    assert provider_for_model("gpt-5.4") == Tool.CODEX.value
    assert provider_for_model(None) is None
    assert provider_for_model("some-unknown-model") is None


def test_agent_event_carries_normalized_turn_metadata():
    tool = AgentEvent("tool_call", "shell")
    assert tool.category == "tool"
    assert tool.persist is True
    assert tool.transcript_role == "tool"
    assert tool.label == "tool"
    assert tool.conversation is False

    thinking = AgentEvent("thinking", "plan")
    assert thinking.category == "thinking"
    assert thinking.persist is True
    assert thinking.transcript_role == "assistant"
    assert thinking.label == "think"
    assert thinking.conversation is True

    system = AgentEvent("system", "")
    assert system.category == "lifecycle"
    assert system.persist is False
    assert system.conversation is False


def test_service_skips_empty_lifecycle_turns(tmp_path):
    """Empty system/result envelopes must not be persisted — only real content."""
    from hephaestus.store.threads import list_turns

    class _LifecycleRunner:
        tool = Tool.CLAUDE

        async def run(self, contract, ctx):
            yield AgentEvent("system", "")       # lifecycle noise -> dropped
            yield AgentEvent("result", "")       # lifecycle noise -> dropped
            yield AgentEvent("thinking", "weighing it")
            yield AgentEvent("text", "the answer")

    async def go():
        runners = {Tool.CLAUDE: _LifecycleRunner(), Tool.CODEX: _LifecycleRunner()}
        service = AgentService(tmp_path, runners=runners)
        prepared = service.begin(AgentTask(role=Role.ARCHITECT, prompt="hi", issue_id="issue-001"))
        async for _ in service.run(prepared):
            pass
        return list_turns(service.state_db_path, prepared.thread_id)

    turns = asyncio.run(go())
    kinds = {(t.role, t.kind, t.text) for t in turns}
    assert ("user", "text", "hi") in kinds
    assert ("assistant", "thinking", "weighing it") in kinds
    assert ("assistant", "text", "the answer") in kinds
    assert all(t.text.strip() for t in turns)  # no empty lifecycle rows


def test_claude_event_captures_thinking_and_text():
    """Agent reasoning (thinking blocks) must not be dropped — it's surfaced as a
    'thinking' event alongside the spoken text."""
    class _Blk:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class AssistantMessage:  # name drives kind mapping
        pass

    msg = AssistantMessage()
    msg.content = [
        _Blk(type="thinking", thinking="weighing the options"),
        _Blk(type="text", text="here is my answer"),
    ]
    result = _claude_normalize_event(msg)
    by_kind = {e.kind: e.text for e in (result if isinstance(result, list) else [result])}
    assert by_kind.get("thinking") == "weighing the options"
    assert by_kind.get("text") == "here is my answer"


def test_decode_codex_line_handles_oversized_line():
    """A JSONL line far larger than asyncio's 64KB readline cap must decode fine."""
    runner = CodexRunner(normalize_event=_codex_normalize_event)
    big = "x" * (200_000)
    line = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": big}})
    ev = runner.decode_event_line(line.encode("utf-8"))
    assert ev.kind == "text"
    assert ev.text == big


def test_decode_codex_line_blank_is_none():
    runner = CodexRunner(normalize_event=_codex_normalize_event)
    assert runner.decode_event_line(b"   ") is None


def test_codex_event_maps_reasoning_to_thinking():
    ev = _codex_normalize_event({"type": "item.completed", "item": {"type": "reasoning", "text": "let me think"}})
    assert ev.kind == "thinking"
    assert ev.text == "let me think"


def test_codex_event_captures_command_execution_as_tool_call():
    """Real codex exec --json reports shell tool calls as command_execution items."""
    from hephaestus.integration.runners import _extract_target_path

    raw = {
        "type": "item.completed",
        "item": {"type": "command_execution", "command": "echo hi", "exit_code": 0},
    }
    raw["item"]["aggregated_output"] = "hi\n"
    ev = _codex_normalize_event(raw)
    assert ev.kind == "tool_call"
    assert ev.raw["action"] == "shell"
    assert _extract_target_path(ev.raw["input"]) == "echo hi"
    assert ev.raw["output"] == "hi\n"
    assert ev.raw["exit_code"] == 0


def test_trace_persists_and_queryable_by_thread(tmp_path):
    """Tool-call traces persist and are retrievable by thread (survives reopen)."""
    from hephaestus.store.trace import list_trace_events

    class _ToolRunner:
        tool = Tool.CODEX

        async def run(self, contract, ctx):
            yield AgentEvent(
                "tool_call", "shell",
                raw={"action": "shell", "input": {"command": "echo hi"}, "output": "hi", "exit_code": 0},
            )
            yield AgentEvent("text", "done")

    async def go():
        runners = {Tool.CLAUDE: _ToolRunner(), Tool.CODEX: _ToolRunner()}
        svc = AgentService(tmp_path, runners=runners)
        prepared = svc.begin(AgentTask(role=Role.WORKER, prompt="x", issue_id="issue-001", model="gpt-5.4"))
        async for _ in svc.run(prepared):
            pass
        return svc.state_db_path, prepared.thread_id

    db, thread_id = asyncio.run(go())
    tr = list_trace_events(db, thread_id=thread_id)
    assert [(t.action, t.target_path) for t in tr] == [("shell", "echo hi")]
    assert tr[0].raw["output"] == "hi"


def test_codex_event_function_call_parses_string_arguments():
    raw = {
        "type": "item.completed",
        "item": {"type": "function_call", "name": "search", "arguments": '{"query": "x"}'},
    }
    ev = _codex_normalize_event(raw)
    assert ev.kind == "tool_call"
    assert ev.raw == {"action": "search", "input": {"query": "x"}}


def test_codex_event_ignores_item_started_to_avoid_duplicate_tool_calls():
    """item.started carries the same item; only item.completed should emit a tool_call."""
    raw = {
        "type": "item.started",
        "item": {"type": "command_execution", "command": "echo hi", "status": "in_progress"},
    }
    ev = _codex_normalize_event(raw)
    assert ev.kind != "tool_call"


def test_claude_options_pass_effort():
    pytest.importorskip("claude_agent_sdk")
    ctx = SessionContext(role=Role.ARCHITECT, issue_id=None, files=[], missing=[], system_prompt="")
    runner = ClaudeRunner(normalize_event=_claude_normalize_event, flag_resolver=_claude_flags)
    opts = runner.build_options(ctx, _contract(role="architect", model=None, prompt="x", effort="xhigh"))
    assert getattr(opts, "effort", None) == "xhigh"


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


def test_begin_role_run_is_callable_without_desktop(tmp_path):
    runners = {Tool.CLAUDE: EchoRunner(Tool.CLAUDE), Tool.CODEX: EchoRunner(Tool.CODEX)}
    service = AgentService(tmp_path, runners=runners)

    prepared = service.begin_role_run(
        role=Role.ARCHITECT,
        prompt="design it",
        issue_id="issue-010",
        cwd=tmp_path / "repo",
        model="gpt-5.4",
        effort="high",
    )

    assert isinstance(prepared, PreparedRun)
    assert prepared.task.role is Role.ARCHITECT
    assert prepared.task.prompt == "design it"
    assert prepared.task.issue_id == "issue-010"
    assert prepared.task.cwd == (tmp_path / "repo")
    assert prepared.task.model == "gpt-5.4"
    assert prepared.task.effort == "high"
    assert prepared.tool is Tool.CODEX


def test_begin_profile_run_resolves_model_effort_and_cwd_from_profile(tmp_path):
    runners = {Tool.CLAUDE: EchoRunner(Tool.CLAUDE), Tool.CODEX: EchoRunner(Tool.CODEX)}
    service = AgentService(tmp_path, runners=runners)
    profile = create_profile(
        service.state_db_path,
        tmp_path,
        name="Worker One",
        role="worker",
        rules=["G-001"],
        model="gpt-5.4",
        effort="xhigh",
        working_dir=str(tmp_path / "svc"),
    )

    prepared = service.begin_profile_run(
        agent_id=profile.agent_id,
        prompt="implement it",
        issue_id="issue-012",
    )

    assert isinstance(prepared, PreparedRun)
    assert prepared.agent_id == profile.agent_id
    assert prepared.task.role is Role.WORKER
    assert prepared.task.agent_id == profile.agent_id
    assert prepared.task.model == "gpt-5.4"
    assert prepared.task.effort == "xhigh"
    assert prepared.task.cwd == (tmp_path / "svc")
    assert prepared.tool is Tool.CODEX


def test_service_persists_actual_model_and_governance_violation(tmp_path):
    class _MismatchRunner:
        tool = Tool.CODEX

        async def run(self, contract, ctx):
            yield AgentEvent("text", "done")
            yield AgentEvent("result", "", raw={"actual_model": "gpt-5.5"})

    async def go():
        runners = {Tool.CLAUDE: _MismatchRunner(), Tool.CODEX: _MismatchRunner()}
        service = AgentService(tmp_path, runners=runners)
        prepared = service.begin(AgentTask(role=Role.WORKER, prompt="go", issue_id="issue-013", model="gpt-5.4"))
        async for _ in service.run(prepared):
            pass
        return service, prepared

    service, prepared = asyncio.run(go())
    run = get_run(service.state_db_path, prepared.run_id)
    assert run.contract["model"] == "gpt-5.4"
    assert run.contract["actual_model"] == "gpt-5.5"
    with connect(service.state_db_path) as db:
        violations = list_violations(db, run_id=prepared.run_id)
    assert any(v["rule_id"] == "G-002" for v in violations)


def test_service_persists_run_lifecycle_and_transcript(tmp_path):
    agents = tmp_path / "agents" / "architect"
    agents.mkdir(parents=True)
    (agents / "architect.md").write_text("ARCHITECT DIRECTIVE", encoding="utf-8")
    issues = tmp_path / "agents" / "architect" / "issues"
    issues.mkdir(parents=True)
    (issues / "issue-003.md").write_text("ISSUE 003", encoding="utf-8")

    async def go():
        runners = {Tool.CLAUDE: EchoRunner(Tool.CLAUDE), Tool.CODEX: EchoRunner(Tool.CODEX)}
        service = AgentService(tmp_path, runners=runners)
        prepared = service.begin(AgentTask(role=Role.ARCHITECT, prompt="design the fix", issue_id="issue-003"))

        running = get_run(service.state_db_path, prepared.run_id)
        assert running.status == "running"

        return service, prepared, [event async for event in service.run(prepared)]

    service, prepared, events = asyncio.run(go())
    finished = get_run(service.state_db_path, prepared.run_id)
    turns = list_turns(service.state_db_path, prepared.thread_id)

    assert finished.status == "done"
    assert [turn.role for turn in turns] == ["user", "assistant", "assistant", "assistant", "assistant"]
    assert [turn.kind for turn in turns] == ["text", "system", "system", "text", "result"]
    assert [turn.text for turn in turns] == [
        "design the fix",
        "[echo:claude] role=architect issue=issue-003",
        "context files: ['architect.md', 'issue-003.md']",
        "design the fix",
        "ok",
    ]
    assert [event.kind for event in events] == ["system", "system", "text", "result"]


def test_service_reuses_thread_for_same_actor_and_issue(tmp_path):
    async def go():
        runners = {Tool.CLAUDE: EchoRunner(Tool.CLAUDE), Tool.CODEX: EchoRunner(Tool.CODEX)}
        service = AgentService(tmp_path, runners=runners)

        first = service.begin(AgentTask(role=Role.ARCHITECT, prompt="first pass", issue_id="issue-003"))
        async for _ in service.run(first):
            pass

        second = service.begin(AgentTask(role=Role.ARCHITECT, prompt="follow up", issue_id="issue-003"))
        async for _ in service.run(second):
            pass

        return service, first, second

    service, first, second = asyncio.run(go())
    turns = list_turns(service.state_db_path, second.thread_id)

    assert second.thread_id == first.thread_id
    assert [turn.text for turn in turns if turn.role == "user"] == ["first pass", "follow up"]


def test_runs_serialize_per_actor_but_parallel_across_actors(tmp_path):
    class CountingRunner:
        tool = Tool.CLAUDE

        def __init__(self):
            self.active = 0
            self.max_active = 0

        async def run(self, contract, ctx):
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            await asyncio.sleep(0.05)
            yield AgentEvent("text", contract.prompt)
            await asyncio.sleep(0.05)
            self.active -= 1
            yield AgentEvent("result", "done")

    async def drain(service, task):
        return [event async for event in service.run(task)]

    async def same_actor():
        runner = CountingRunner()
        service = AgentService(tmp_path / "same", runners={Tool.CLAUDE: runner, Tool.CODEX: runner})
        await asyncio.gather(
            drain(service, AgentTask(role=Role.ARCHITECT, prompt="one", issue_id="issue-003")),
            drain(service, AgentTask(role=Role.ARCHITECT, prompt="two", issue_id="issue-003")),
        )
        return runner.max_active

    async def different_actors():
        runner = CountingRunner()
        service = AgentService(tmp_path / "different", runners={Tool.CLAUDE: runner, Tool.CODEX: runner})
        await asyncio.gather(
            drain(service, AgentTask(role=Role.ARCHITECT, prompt="architect", issue_id="issue-003")),
            drain(service, AgentTask(role=Role.QA, prompt="qa", issue_id="issue-003")),
        )
        return runner.max_active

    assert asyncio.run(same_actor()) == 1
    assert asyncio.run(different_actors()) == 2


def test_service_marks_incomplete_runs_interrupted_on_next_open(tmp_path):
    service = AgentService(tmp_path, runners={Tool.CLAUDE: EchoRunner(Tool.CLAUDE), Tool.CODEX: EchoRunner(Tool.CODEX)})
    prepared = service.begin(AgentTask(role=Role.ARCHITECT, prompt="recover me", issue_id="issue-003"))

    interrupted_service = AgentService(
        tmp_path,
        runners={Tool.CLAUDE: EchoRunner(Tool.CLAUDE), Tool.CODEX: EchoRunner(Tool.CODEX)},
    )
    interrupted = get_run(interrupted_service.state_db_path, prepared.run_id)
    turns = list_turns(interrupted_service.state_db_path, prepared.thread_id)

    assert interrupted.status == "interrupted"
    assert interrupted.ended_at is not None
    assert [turn.text for turn in turns] == ["recover me"]


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
    ctx = SessionContext(role=Role.ARCHITECT, issue_id=None, files=[], missing=[],
                         system_prompt="OKF DIRECTIVE CONTENT")
    runner = ClaudeRunner(normalize_event=_claude_normalize_event, flag_resolver=_claude_flags)
    opts = runner.build_options(ctx, _contract(role="architect", model=None, prompt="x"))
    assert "OKF DIRECTIVE CONTENT" in str(opts.system_prompt)


def test_service_resumes_captured_session():
    """A result event carrying a session id is stored and reused on the next run."""
    class _OneShot:
        tool = Tool.CLAUDE

        def __init__(self):
            self.seen_resume = []

        async def run(self, contract, ctx):
            self.seen_resume.append(contract.resume)
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


def test_compiled_history_injected_into_system_prompt(tmp_path):
    """Second run's context must contain prior-turn history block."""
    captured_prompts: list[str] = []

    class CapturingRunner:
        tool = Tool.CLAUDE

        async def run(self, contract, ctx):
            captured_prompts.append(ctx.system_prompt)
            yield AgentEvent("text", contract.prompt)
            yield AgentEvent("result", "done")

    async def go():
        runners = {Tool.CLAUDE: CapturingRunner(), Tool.CODEX: CapturingRunner()}
        service = AgentService(tmp_path, runners=runners)
        task = AgentTask(role=Role.ARCHITECT, prompt="first message", issue_id="issue-001")
        async for _ in service.run(task):
            pass
        task2 = AgentTask(role=Role.ARCHITECT, prompt="second message", issue_id="issue-001")
        async for _ in service.run(task2):
            pass

    asyncio.run(go())
    assert len(captured_prompts) == 2
    assert "Prior context" not in captured_prompts[0]  # first run has no history
    assert "Prior context" in captured_prompts[1]       # second run sees the first
