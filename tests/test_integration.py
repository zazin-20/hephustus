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
    provider_key,
)
from hephaestus.integration.runners import (
    AgentEvent,
    AgentTask,
    ClaudeRunner,
    CodexRunner,
    EchoRunner,
    build_codex_argv,
)
from hephaestus.integration.service import AgentService, GovernanceViolationError, PreparedRun
from hephaestus.store.corrections import list_corrections, promote_correction
from hephaestus.store.db import connect
from hephaestus.store.frozen_rules import upsert_frozen_rule
from hephaestus.store.nodes import create_node
from hephaestus.store.runs import get_run
from hephaestus.store.threads import list_turns
from hephaestus.store.violations import list_violations


def _contract(**kwargs) -> ExecutionContract:
    defaults = dict(
        actor="node-001",
        node_id="node-001",
        provider="codex",
        tags=["worker"],
        context="thread-001",
        scope="workflow:issue-001/placement:node-001",
        model="gpt-5.4",
        effort=None,
        tools=[],
        prompt="go",
    )
    defaults.update(kwargs)
    return ExecutionContract(**defaults)


def _task(
    *,
    node_id: str | None = None,
    provider: str = "claude",
    tags: list[str] | None = None,
    prompt: str = "go",
    **kwargs,
) -> AgentTask:
    return AgentTask(
        node_id=node_id,
        provider=provider,
        tags=list(tags or ["architect"]),
        prompt=prompt,
        **kwargs,
    )

def test_provider_keys_are_plain_strings():
    assert provider_key("codex") == "codex"
    assert provider_key("claude") == "claude"


def test_context_injects_directive_issue_and_tdd(tmp_path):
    a = tmp_path / "agents"
    (a / "worker").mkdir(parents=True)
    (a / "worker" / "claude.md").write_text("WORKER DIRECTIVE", encoding="utf-8")
    (a / "worker" / "tdd.md").write_text("TDD PLAYBOOK", encoding="utf-8")
    (a / "architect" / "issues").mkdir(parents=True)
    (a / "architect" / "issues" / "issue-009.md").write_text("ISSUE NINE SPEC", encoding="utf-8")

    ctx = build_session_context(tmp_path, node_id="node-001", tags=["worker"], issue_id="issue-009")
    assert {p.name for p in ctx.files} == {"claude.md", "tdd.md", "issue-009.md"}
    assert ctx.missing == []
    assert "WORKER DIRECTIVE" in ctx.system_prompt
    assert "ISSUE NINE SPEC" in ctx.system_prompt


def test_context_reports_missing_files(tmp_path):
    ctx = build_session_context(tmp_path, node_id="node-001", tags=["architect"], issue_id="issue-001")
    assert ctx.files == []
    assert any(p.name == "architect.md" for p in ctx.missing)
    assert any(p.name == "issue-001.md" for p in ctx.missing)


def test_context_injects_skill_playbooks(tmp_path):
    agents = tmp_path / "agents"
    (agents / "worker").mkdir(parents=True)
    (agents / "worker" / "claude.md").write_text("WORKER DIRECTIVE", encoding="utf-8")
    (agents / "worker" / "tdd.md").write_text("TDD PLAYBOOK", encoding="utf-8")
    (agents / "skills").mkdir(parents=True)
    (agents / "skills" / "grill-me.md").write_text("GRILL ME PLAYBOOK", encoding="utf-8")

    ctx = build_session_context(
        tmp_path,
        node_id="node-001",
        tags=["worker"],
        skills=["skill:grill-me"],
    )

    assert {p.name for p in ctx.files} == {"claude.md", "tdd.md", "grill-me.md"}
    assert ctx.missing == []
    assert "# Skills" in ctx.system_prompt
    assert "GRILL ME PLAYBOOK" in ctx.system_prompt


def test_context_reports_missing_skill_playbooks(tmp_path):
    agents = tmp_path / "agents"
    (agents / "architect").mkdir(parents=True)
    (agents / "architect" / "architect.md").write_text("ARCHITECT DIRECTIVE", encoding="utf-8")

    ctx = build_session_context(
        tmp_path,
        node_id="node-001",
        tags=["architect"],
        skills=["skill:grill-me"],
    )

    assert any(path.name == "grill-me.md" for path in ctx.missing)


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
    """The chosen model decides the runner, overriding the node's provider."""
    runners = {"claude": EchoRunner("claude"), "codex": EchoRunner("codex")}
    service = AgentService(tmp_path, runners=runners)

    tool, _ = service.resolve(_task(provider="claude", tags=["architect"], prompt="x", model="gpt-5.4"))
    assert tool == "codex"
    tool2, _ = service.resolve(_task(provider="codex", tags=["worker"], prompt="x", model="opus"))
    assert tool2 == "claude"
    assert service.resolve(_task(provider="claude", tags=["architect"], prompt="x"))[0] == "claude"
    assert service.resolve(_task(provider="codex", tags=["worker"], prompt="x"))[0] == "codex"


def test_provider_for_model_classifies():
    from hephaestus.catalog import provider_for_model

    assert provider_for_model("opus") == "claude"
    assert provider_for_model("claude-opus-4-8") == "claude"
    assert provider_for_model("gpt-5.4") == "codex"
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
        tool = "claude"

        async def run(self, contract, ctx):
            yield AgentEvent("system", "")       # lifecycle noise -> dropped
            yield AgentEvent("result", "")       # lifecycle noise -> dropped
            yield AgentEvent("thinking", "weighing it")
            yield AgentEvent("text", "the answer")

    async def go():
        runners = {"claude": _LifecycleRunner(), "codex": _LifecycleRunner()}
        service = AgentService(tmp_path, runners=runners)
        prepared = service.begin(_task(provider="claude", tags=["architect"], prompt="hi", issue_id="issue-001"))
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
        tool = "codex"

        async def run(self, contract, ctx):
            yield AgentEvent(
                "tool_call", "shell",
                raw={"action": "shell", "input": {"command": "echo hi"}, "output": "hi", "exit_code": 0},
            )
            yield AgentEvent("text", "done")

    async def go():
        runners = {"claude": _ToolRunner(), "codex": _ToolRunner()}
        svc = AgentService(tmp_path, runners=runners)
        prepared = svc.begin(_task(provider="codex", tags=["worker"], prompt="x", issue_id="issue-001", model="gpt-5.4"))
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
    ctx = SessionContext(node_id="node-001", tags=["architect"], issue_id=None, files=[], missing=[], system_prompt="")
    runner = ClaudeRunner(normalize_event=_claude_normalize_event, flag_resolver=_claude_flags)
    opts = runner.build_options(ctx, _contract(provider="claude", tags=["architect"], model=None, prompt="x", effort="xhigh"))
    assert getattr(opts, "effort", None) == "xhigh"


def test_service_routes_worker_through_codex_echo():
    async def run():
        runners = {"claude": EchoRunner("claude"), "codex": EchoRunner("codex")}
        service = AgentService("sample", runners=runners)
        task = _task(provider="codex", tags=["worker"], prompt="hello worker", issue_id="issue-003")
        return [ev async for ev in service.run(task)]

    events = asyncio.run(run())
    assert "result" in {e.kind for e in events}
    joined = " ".join(e.text for e in events)
    assert "echo:codex" in joined          # routed to the codex backend
    assert "issue-003" in joined           # issue context threaded through
    assert "hello worker" in joined


def test_begin_node_run_is_callable_without_desktop(tmp_path):
    runners = {"claude": EchoRunner("claude"), "codex": EchoRunner("codex")}
    service = AgentService(tmp_path, runners=runners)
    node = create_node(
        service.state_db_path,
        tmp_path,
        name="Architect One",
        provider="claude",
        tags=["architect"],
        rules=[],
        model="gpt-5.4",
        effort="high",
        working_dir=str(tmp_path / "repo"),
    )

    prepared = service.begin_node_run(
        node_id=node.node_id,
        prompt="design it",
        issue_id="issue-010",
        cwd=tmp_path / "repo",
        model="gpt-5.4",
        effort="high",
    )

    assert isinstance(prepared, PreparedRun)
    assert prepared.task.node_id == node.node_id
    assert prepared.task.prompt == "design it"
    assert prepared.task.issue_id == "issue-010"
    assert prepared.task.cwd == (tmp_path / "repo")
    assert prepared.task.model == "gpt-5.4"
    assert prepared.task.effort == "high"
    assert prepared.tool == "codex"


def test_begin_node_run_resolves_model_effort_and_cwd_from_node(tmp_path):
    runners = {"claude": EchoRunner("claude"), "codex": EchoRunner("codex")}
    service = AgentService(tmp_path, runners=runners)
    node = create_node(
        service.state_db_path,
        tmp_path,
        name="Worker One",
        provider="codex",
        tags=["worker"],
        rules=["G-001"],
        model="gpt-5.4",
        effort="xhigh",
        working_dir=str(tmp_path / "svc"),
    )

    prepared = service.begin_node_run(
        node_id=node.node_id,
        prompt="implement it",
        issue_id="issue-012",
    )

    assert isinstance(prepared, PreparedRun)
    assert prepared.node_id == node.node_id
    assert prepared.task.node_id == node.node_id
    assert prepared.task.model == "gpt-5.4"
    assert prepared.task.effort == "xhigh"
    assert prepared.task.cwd == (tmp_path / "svc")
    assert prepared.tool == "codex"


def test_service_injects_node_skill_playbooks(tmp_path):
    agents = tmp_path / "agents"
    (agents / "worker").mkdir(parents=True)
    (agents / "worker" / "claude.md").write_text("WORKER DIRECTIVE", encoding="utf-8")
    (agents / "worker" / "tdd.md").write_text("TDD PLAYBOOK", encoding="utf-8")
    (agents / "skills").mkdir(parents=True)
    (agents / "skills" / "grill-me.md").write_text("GRILL ME PLAYBOOK", encoding="utf-8")

    captured: list[str] = []

    class CapturingRunner:
        tool = "codex"

        async def run(self, contract, ctx):
            captured.append(ctx.system_prompt)
            yield AgentEvent("text", "done")
            yield AgentEvent("result", "ok")

    async def go():
        runners = {"claude": CapturingRunner(), "codex": CapturingRunner()}
        service = AgentService(tmp_path, runners=runners)
        worker = create_node(
            service.state_db_path,
            tmp_path,
            name="Worker",
            provider="codex",
            tags=["worker"],
            rules=[],
            skills=["skill:grill-me"],
        )
        async for _ in service.run(service.task_for_node(node_id=worker.node_id, prompt="use the skill")):
            pass

    asyncio.run(go())

    assert len(captured) == 1
    assert "# Skills" in captured[0]
    assert "GRILL ME PLAYBOOK" in captured[0]


def test_service_allows_enforced_skill_obligation_when_marker_present(tmp_path):
    class _SkillRunner:
        tool = "codex"

        async def run(self, contract, ctx):
            yield AgentEvent(
                "text",
                '@@HEPHAESTUS@@ {"v":1,"type":"skill_complete","skill":"grill-me","ok":true}',
            )
            yield AgentEvent("result", "ok")

    async def go():
        runners = {"claude": _SkillRunner(), "codex": _SkillRunner()}
        service = AgentService(tmp_path, runners=runners)
        worker = create_node(
            service.state_db_path,
            tmp_path,
            name="Worker",
            provider="codex",
            tags=["worker"],
            rules=[],
            skills=["skill:grill-me"],
            skill_obligations=["skill:grill-me"],
        )
        prepared = service.begin(service.task_for_node(node_id=worker.node_id, prompt="use the skill"))
        async for _ in service.run(prepared):
            pass
        return service, prepared

    service, prepared = asyncio.run(go())
    run = get_run(service.state_db_path, prepared.run_id)
    with connect(service.state_db_path) as db:
        violations = list_violations(db, run_id=prepared.run_id)
    assert run.status == "done"
    assert violations == []


def test_service_raises_and_records_violation_when_enforced_skill_marker_missing(tmp_path):
    class _SkillRunner:
        tool = "codex"

        async def run(self, contract, ctx):
            yield AgentEvent("text", "done")
            yield AgentEvent("result", "ok")

    async def go():
        runners = {"claude": _SkillRunner(), "codex": _SkillRunner()}
        service = AgentService(tmp_path, runners=runners)
        worker = create_node(
            service.state_db_path,
            tmp_path,
            name="Worker",
            provider="codex",
            tags=["worker"],
            rules=[],
            skills=["skill:grill-me"],
            skill_obligations=["skill:grill-me"],
        )
        prepared = service.begin(service.task_for_node(node_id=worker.node_id, prompt="use the skill"))
        with pytest.raises(GovernanceViolationError) as excinfo:
            async for _ in service.run(prepared):
                pass
        assert any(v.rule_id == "G-003" for v in excinfo.value.violations)
        return service, prepared

    service, prepared = asyncio.run(go())
    run = get_run(service.state_db_path, prepared.run_id)
    with connect(service.state_db_path) as db:
        violations = list_violations(db, run_id=prepared.run_id)
    assert any(v["rule_id"] == "G-003" for v in violations)
    assert run.status == "error"


def test_service_persists_actual_model_and_governance_violation(tmp_path):
    class _MismatchRunner:
        tool = "codex"

        async def run(self, contract, ctx):
            yield AgentEvent("text", "done")
            yield AgentEvent("result", "", raw={"actual_model": "gpt-5.5"})

    async def go():
        runners = {"claude": _MismatchRunner(), "codex": _MismatchRunner()}
        service = AgentService(tmp_path, runners=runners)
        prepared = service.begin(_task(provider="codex", tags=["worker"], prompt="go", issue_id="issue-013", model="gpt-5.4"))
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
        runners = {"claude": EchoRunner("claude"), "codex": EchoRunner("codex")}
        service = AgentService(tmp_path, runners=runners)
        prepared = service.begin(_task(provider="claude", tags=["architect"], prompt="design the fix", issue_id="issue-003"))

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
        "[echo:claude] node=node-001 tags=architect issue=issue-003",
        "context files: ['architect.md', 'issue-003.md']",
        "design the fix",
        "ok",
    ]
    assert [event.kind for event in events] == ["system", "system", "text", "result"]


def test_service_creates_new_thread_per_run(tmp_path):
    async def go():
        runners = {"claude": EchoRunner("claude"), "codex": EchoRunner("codex")}
        service = AgentService(tmp_path, runners=runners)

        first = service.begin(_task(provider="claude", tags=["architect"], prompt="first pass", issue_id="issue-003"))
        async for _ in service.run(first):
            pass

        second = service.begin(_task(provider="claude", tags=["architect"], prompt="follow up", issue_id="issue-003"))
        async for _ in service.run(second):
            pass

        return service, first, second

    service, first, second = asyncio.run(go())
    first_turns = list_turns(service.state_db_path, first.thread_id)
    second_turns = list_turns(service.state_db_path, second.thread_id)

    assert second.thread_id != first.thread_id
    assert [turn.text for turn in first_turns if turn.role == "user"] == ["first pass"]
    assert [turn.text for turn in second_turns if turn.role == "user"] == ["follow up"]


def test_runs_serialize_per_node_but_parallel_across_nodes(tmp_path):
    class CountingRunner:
        tool = "claude"

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
        service = AgentService(tmp_path / "same", runners={"claude": runner, "codex": runner})
        node = create_node(service.state_db_path, tmp_path / "same", "Architect", "claude", ["architect"], [])
        await asyncio.gather(
            drain(service, _task(node_id=node.node_id, provider="claude", tags=["architect"], prompt="one", issue_id="issue-003")),
            drain(service, _task(node_id=node.node_id, provider="claude", tags=["architect"], prompt="two", issue_id="issue-003")),
        )
        return runner.max_active

    async def different_nodes():
        runner = CountingRunner()
        service = AgentService(tmp_path / "different", runners={"claude": runner, "codex": runner})
        architect = create_node(service.state_db_path, tmp_path / "different", "Architect", "claude", ["architect"], [])
        qa = create_node(service.state_db_path, tmp_path / "different", "QA", "claude", ["qa"], [])
        await asyncio.gather(
            drain(service, _task(node_id=architect.node_id, provider="claude", tags=["architect"], prompt="architect", issue_id="issue-003")),
            drain(service, _task(node_id=qa.node_id, provider="claude", tags=["qa"], prompt="qa", issue_id="issue-003")),
        )
        return runner.max_active

    assert asyncio.run(same_actor()) == 1
    assert asyncio.run(different_nodes()) == 2


def test_service_marks_incomplete_runs_interrupted_on_next_open(tmp_path):
    service = AgentService(tmp_path, runners={"claude": EchoRunner("claude"), "codex": EchoRunner("codex")})
    prepared = service.begin(_task(provider="claude", tags=["architect"], prompt="recover me", issue_id="issue-003"))

    interrupted_service = AgentService(
        tmp_path,
        runners={"claude": EchoRunner("claude"), "codex": EchoRunner("codex")},
    )
    interrupted = get_run(interrupted_service.state_db_path, prepared.run_id)
    turns = list_turns(interrupted_service.state_db_path, prepared.thread_id)

    assert interrupted.status == "interrupted"
    assert interrupted.ended_at is not None
    assert [turn.text for turn in turns] == ["recover me"]


def test_claude_options_actually_inject_context():
    """Guards the silent-drop bug: OKF context must reach ClaudeAgentOptions."""
    pytest.importorskip("claude_agent_sdk")
    ctx = SessionContext(node_id="node-001", tags=["architect"], issue_id=None, files=[], missing=[],
                         system_prompt="OKF DIRECTIVE CONTENT")
    runner = ClaudeRunner(normalize_event=_claude_normalize_event, flag_resolver=_claude_flags)
    opts = runner.build_options(ctx, _contract(provider="claude", tags=["architect"], model=None, prompt="x"))
    assert "OKF DIRECTIVE CONTENT" in str(opts.system_prompt)


def test_second_run_starts_with_clean_context(tmp_path):
    """Per-run threads mean the second run should not inherit prior transcript history."""
    captured_prompts: list[str] = []

    class CapturingRunner:
        tool = "claude"

        async def run(self, contract, ctx):
            captured_prompts.append(ctx.system_prompt)
            yield AgentEvent("text", contract.prompt)
            yield AgentEvent("result", "done")

    async def go():
        runners = {"claude": CapturingRunner(), "codex": CapturingRunner()}
        service = AgentService(tmp_path, runners=runners)
        task = _task(provider="claude", tags=["architect"], prompt="first message", issue_id="issue-001")
        async for _ in service.run(task):
            pass
        task2 = _task(provider="claude", tags=["architect"], prompt="second message", issue_id="issue-001")
        async for _ in service.run(task2):
            pass

    asyncio.run(go())
    assert len(captured_prompts) == 2
    assert "Prior context" not in captured_prompts[0]
    assert "Prior context" not in captured_prompts[1]


def test_node_context_is_clean_slate_with_layered_directives_and_same_node_replay(tmp_path):
    agents = tmp_path / "agents"
    (agents / "worker").mkdir(parents=True)
    (agents / "worker" / "claude.md").write_text("WORKER DIRECTIVE", encoding="utf-8")
    (agents / "worker" / "tdd.md").write_text("TDD PLAYBOOK", encoding="utf-8")
    (agents / "artifacts").mkdir(parents=True)
    (agents / "artifacts" / "issue-019.md").write_text("ISSUE ARTIFACT", encoding="utf-8")
    (agents / "specs").mkdir(parents=True)
    (agents / "specs" / "handoff.md").write_text("HANDOFF SPEC", encoding="utf-8")

    captured: list[tuple[str, str]] = []

    class CapturingRunner:
        tool = "codex"

        async def run(self, contract, ctx):
            captured.append((contract.node_id, ctx.system_prompt))
            yield AgentEvent("text", f"assistant: {contract.prompt}")
            yield AgentEvent("result", "done")

    async def go():
        runners = {"claude": CapturingRunner(), "codex": CapturingRunner()}
        service = AgentService(tmp_path, runners=runners)
        worker = create_node(
            service.state_db_path,
            tmp_path,
            name="Worker",
            provider="codex",
            tags=["worker"],
            rules=[],
            inputs=["artifacts/issue-019.md"],
            outputs=["specs/handoff.md"],
        )
        qa = create_node(
            service.state_db_path,
            tmp_path,
            name="QA",
            provider="codex",
            tags=["qa"],
            rules=[],
            inputs=["artifacts/issue-019.md"],
            outputs=["specs/handoff.md"],
        )
        machine = str(tmp_path.resolve())
        upsert_frozen_rule(service.state_db_path, scope="global", topic_key="tone", body="GLOBAL DIRECTIVE")
        upsert_frozen_rule(
            service.state_db_path,
            scope="machine",
            topic_key="python",
            body="MACHINE DIRECTIVE",
            machine=machine,
        )
        upsert_frozen_rule(
            service.state_db_path,
            scope="workflow",
            topic_key="artifact",
            body="WORKFLOW DIRECTIVE",
            workflow_id="wf-019",
        )
        upsert_frozen_rule(
            service.state_db_path,
            scope="tag",
            topic_key="worker",
            body="TAG DIRECTIVE",
            tag="worker",
        )
        upsert_frozen_rule(
            service.state_db_path,
            scope="node",
            topic_key="handoff",
            body="NODE DIRECTIVE",
            workflow_id="wf-019",
            placement_id="implement",
            node_id=worker.node_id,
        )

        async for _ in service.run(
            service.task_for_node(
                node_id=worker.node_id,
                prompt="implement step one",
                workflow_id="wf-019",
                workflow_run_id="run-019",
                placement_id="implement",
            )
        ):
            pass
        async for _ in service.run(
            service.task_for_node(
                node_id=worker.node_id,
                prompt="implement step two",
                workflow_id="wf-019",
                workflow_run_id="run-019",
                placement_id="implement",
            )
        ):
            pass
        async for _ in service.run(
            service.task_for_node(
                node_id=qa.node_id,
                prompt="verify output",
                workflow_id="wf-019",
                workflow_run_id="run-019",
                placement_id="review",
            )
        ):
            pass

    asyncio.run(go())

    first = captured[0][1]
    second = captured[1][1]
    third = captured[2][1]

    for expected in (
        "GLOBAL DIRECTIVE",
        "MACHINE DIRECTIVE",
        "WORKFLOW DIRECTIVE",
        "WORKER DIRECTIVE",
        "TAG DIRECTIVE",
        "NODE DIRECTIVE",
        "TDD PLAYBOOK",
        "ISSUE ARTIFACT",
        "HANDOFF SPEC",
    ):
        assert expected in first

    assert "Prior context" not in first
    assert "Prior context" in second
    assert "user: implement step one" in second
    assert "assistant: assistant: implement step one" in second
    assert "implement step one" not in third
    assert "assistant: assistant: implement step one" not in third


def test_distillation_candidate_promotes_into_later_run_context(tmp_path):
    agents = tmp_path / "agents"
    (agents / "worker").mkdir(parents=True)
    (agents / "worker" / "claude.md").write_text("WORKER DIRECTIVE", encoding="utf-8")
    (agents / "worker" / "tdd.md").write_text("TDD PLAYBOOK", encoding="utf-8")
    (agents / "architect" / "issues").mkdir(parents=True)
    (agents / "architect" / "issues" / "issue-024.md").write_text("ISSUE TWENTY FOUR", encoding="utf-8")

    captured: list[str] = []

    class DistillingRunner:
        tool = "codex"

        async def run(self, contract, ctx):
            captured.append(ctx.system_prompt)
            if contract.prompt == "discover":
                yield AgentEvent(
                    "tool_call",
                    "emit distillation marker",
                    raw={
                        "action": "shell",
                        "input": {
                            "command": '\n@@HEPHAESTUS@@ {"v":1,"type":"distillation_candidate","topic_key":"python-invocation","scope":"machine","directive":"Use the workspace venv interpreter for python invocations."}\n',
                        },
                    },
                )
            yield AgentEvent("text", f"assistant: {contract.prompt}")
            yield AgentEvent("result", "done", raw={"actual_model": contract.model})

    async def go():
        runners = {"claude": DistillingRunner(), "codex": DistillingRunner()}
        service = AgentService(tmp_path, runners=runners)
        worker = create_node(
            service.state_db_path,
            tmp_path,
            name="Worker",
            provider="codex",
            tags=["worker"],
            rules=[],
        )

        async for _ in service.run(
            service.task_for_node(node_id=worker.node_id, prompt="discover", issue_id="issue-024")
        ):
            pass

        candidates = list_corrections(service.state_db_path, node_id=worker.node_id, issue_id="issue-024")
        assert len(candidates) == 1
        assert candidates[0].source_kind == "distillation_candidate"
        assert candidates[0].topic_key == "python-invocation"
        assert candidates[0].candidate_scope == "machine"
        assert candidates[0].trace_event_id is not None
        assert candidates[0].source_run_id is not None
        assert candidates[0].source_node_id == worker.node_id

        promote_correction(
            service.state_db_path,
            candidates[0].id,
            confirmer="architect",
            machine=str(tmp_path.resolve()),
        )

        async for _ in service.run(
            service.task_for_node(node_id=worker.node_id, prompt="follow-up", issue_id="issue-024")
        ):
            pass

    asyncio.run(go())

    assert "Use the workspace venv interpreter for python invocations." not in captured[0]
    assert "Use the workspace venv interpreter for python invocations." in captured[1]
    assert "## machine:python-invocation" in captured[1]
