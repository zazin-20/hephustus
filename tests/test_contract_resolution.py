from __future__ import annotations

from pathlib import Path

from hephaestus.contract import ExecutionContract
from hephaestus.integration.context import build_session_context
from hephaestus.integration.contract_resolution import resolve
from hephaestus.integration.providers import provider_registry
from hephaestus.integration.runners import AgentTask, EchoRunner
from hephaestus.integration.service import AgentService
from hephaestus.store.nodes import create_node


def test_resolve_derives_execution_contract_from_node_and_context(tmp_path):
    _write_context_files(tmp_path)
    state_db = tmp_path / ".hephaestus" / "state.db"
    node = create_node(
        state_db,
        tmp_path,
        name="Worker",
        provider="claude",
        tags=["worker"],
        rules=[],
        model="opus",
        effort="medium",
        working_dir=str(tmp_path / "repo"),
        inputs=["artifacts/issue-021.md"],
        outputs=["specs/handoff.md"],
        allowed_paths=["agents/worker", "src"],
        allowed_tools=["write_file", "bash"],
    )
    task = AgentTask(
        node_id=node.node_id,
        provider=node.provider,
        tags=list(node.tags),
        prompt="implement the fix",
        issue_id="issue-021",
        cwd=tmp_path / "override",
        model="gpt-5.4",
        effort="high",
        workflow_id="wf-021",
        workflow_run_id="run-021",
        placement_id="implement",
    )
    session_context = build_session_context(
        tmp_path,
        node_id=node.node_id,
        tags=node.tags,
        issue_id=task.issue_id,
        inputs=node.inputs,
        outputs=node.outputs,
        workflow_id=task.workflow_id,
        workflow_run_id=task.workflow_run_id,
        placement_id=task.placement_id,
        thread_id="thread-021",
        machine=str(tmp_path.resolve()),
    )

    contract = resolve(
        node=node,
        task=task,
        session_context=session_context,
        context_id="thread-021",
        registry=provider_registry(),
    )

    assert contract == ExecutionContract(
        actor=node.node_id,
        node_id=node.node_id,
        provider="codex",
        tags=["worker"],
        context="thread-021",
        scope="workflow:wf-021/placement:implement",
        model="gpt-5.4",
        effort="high",
        tools=["write_file", "bash"],
        prompt="implement the fix",
        tool="codex",
        issue_id="issue-021",
        cwd=str(tmp_path / "override"),
        workflow_id="wf-021",
        workflow_run_id="run-021",
        placement_id="implement",
        allowed_paths=["agents/worker", "src"],
    )


def test_service_begin_uses_public_contract_resolution(tmp_path):
    _write_context_files(tmp_path)
    runners = {"claude": EchoRunner("claude"), "codex": EchoRunner("codex")}
    service = AgentService(tmp_path, runners=runners)
    node = create_node(
        service.state_db_path,
        tmp_path,
        name="Worker",
        provider="codex",
        tags=["worker"],
        rules=[],
        model="gpt-5.4",
        effort="medium",
        working_dir=str(tmp_path / "repo"),
        inputs=["artifacts/issue-021.md"],
        outputs=["specs/handoff.md"],
        allowed_paths=["agents/worker"],
        allowed_tools=["write_file"],
    )

    prepared = service.begin_node_run(
        node_id=node.node_id,
        prompt="implement the fix",
        issue_id="issue-021",
        workflow_id="wf-021",
        workflow_run_id="run-021",
        placement_id="implement",
    )

    expected = resolve(
        node=node,
        task=prepared.task,
        session_context=prepared.ctx,
        context_id=prepared.thread_id,
        workflow_id="wf-021",
        workflow_run_id="run-021",
        placement_id="implement",
        registry=service.provider_registry,
    )

    assert prepared.contract == expected


def _write_context_files(root: Path) -> None:
    agents = root / "agents"
    (agents / "worker").mkdir(parents=True)
    (agents / "worker" / "claude.md").write_text("WORKER DIRECTIVE", encoding="utf-8")
    (agents / "worker" / "tdd.md").write_text("TDD PLAYBOOK", encoding="utf-8")
    (agents / "artifacts").mkdir(parents=True)
    (agents / "artifacts" / "issue-021.md").write_text("ISSUE INPUT", encoding="utf-8")
    (agents / "specs").mkdir(parents=True)
    (agents / "specs" / "handoff.md").write_text("HANDOFF SPEC", encoding="utf-8")
