from __future__ import annotations

import asyncio

from hephaestus.integration.runners import AgentEvent
from hephaestus.integration.routing import Tool
from hephaestus.integration.service import AgentService
from hephaestus.store.nodes import create_node
from hephaestus.store.runs import get_run
from hephaestus.workflow_runtime import AdvanceMode, NodeInteractivity, WorkflowRuntime, WorkflowStatus
from hephaestus.workflows import Edge, Placement, Workflow


class _WritingRunner:
    def __init__(self, root, writes: dict[str, tuple[str, str]] | None = None) -> None:
        self._root = root
        self._writes = writes or {}
        self.calls: list[str] = []

    async def run(self, contract, ctx):
        self.calls.append(contract.node_id)
        target = self._writes.get(contract.node_id)
        if target is not None:
            relative_path, body = target
            path = self._root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        yield AgentEvent("text", f"ran {contract.node_id}")
        yield AgentEvent("result", "ok", raw={"actual_model": contract.model})


def test_workflow_runtime_advances_two_node_workflow_on_green(tmp_path):
    _write_context_files(tmp_path)
    runner = _WritingRunner(
        tmp_path,
        {
            "node-001": (
                "agents/artifacts/draft-output.md",
                "---\n"
                "title: Draft Output\n"
                "---\n\n"
                "## Summary\n"
                "Ready for review.\n",
            )
        },
    )
    service = AgentService(
        tmp_path,
        runners={Tool.CLAUDE: runner, Tool.CODEX: runner},
    )
    draft = create_node(
        service.state_db_path,
        tmp_path,
        name="Draft",
        provider="codex",
        tags=["worker"],
        rules=[],
        model="gpt-5.4",
        inputs=["agents/artifacts/issue-023.md"],
        outputs=["agents/specs/draft-spec.md"],
    )
    review = create_node(
        service.state_db_path,
        tmp_path,
        name="Review",
        provider="codex",
        tags=["worker"],
        rules=[],
        model="gpt-5.4",
        inputs=["agents/artifacts/draft-output.md"],
        outputs=[],
    )
    workflow = Workflow(
        workflow_id="issue-023",
        placements=[
            Placement(placement_id="draft", node_id=draft.node_id, x=0, y=0, interactivity=NodeInteractivity.AFK),
            Placement(placement_id="review", node_id=review.node_id, x=1, y=0, interactivity=NodeInteractivity.AFK),
        ],
        edges=[
            Edge(
                from_placement_id="draft",
                from_output="agents/artifacts/draft-output.md",
                to_placement_id="review",
                to_input="agents/artifacts/draft-output.md",
                advance=AdvanceMode.ALLOW,
            )
        ],
    )

    result = asyncio.run(
        WorkflowRuntime(tmp_path, service=service).run(
            workflow,
            prompts={"draft": "draft the artifact", "review": "review the artifact"},
        )
    )

    assert result.status == WorkflowStatus.DONE
    assert [step.status for step in result.steps] == [WorkflowStatus.DONE, WorkflowStatus.DONE]
    assert [step.contract.placement_id for step in result.steps] == ["draft", "review"]
    assert get_run(service.state_db_path, result.steps[0].run_id).contract["workflow_id"] == "issue-023"
    assert get_run(service.state_db_path, result.steps[1].run_id).contract["workflow_id"] == "issue-023"


def test_workflow_runtime_blocks_on_failing_exit_gate(tmp_path):
    _write_context_files(tmp_path)
    runner = _WritingRunner(
        tmp_path,
        {
            "node-001": (
                "agents/artifacts/draft-output.md",
                "---\n"
                "title: Draft Output\n"
                "---\n\n"
                "## Details\n"
                "Missing the required summary section.\n",
            )
        },
    )
    service = AgentService(tmp_path, runners={Tool.CLAUDE: runner, Tool.CODEX: runner})
    workflow = _workflow_fixture(tmp_path, service, advance=AdvanceMode.ALLOW)

    result = asyncio.run(
        WorkflowRuntime(tmp_path, service=service).run(
            workflow,
            prompts={"draft": "draft the artifact", "review": "review the artifact"},
        )
    )

    assert result.status == WorkflowStatus.BLOCKED
    assert len(result.steps) == 1
    assert result.steps[0].status == WorkflowStatus.BLOCKED
    assert result.steps[0].override_available is True
    assert result.steps[0].spawn_card is not None
    assert result.steps[0].spawn_card.gating.value == "amber"
    assert any(failure.rule_id == "A-002" for failure in result.steps[0].failures)
    assert runner.calls == ["node-001"]


def test_workflow_runtime_ask_before_advancing_on_green_gate(tmp_path):
    _write_context_files(tmp_path)
    runner = _WritingRunner(
        tmp_path,
        {
            "node-001": (
                "agents/artifacts/draft-output.md",
                "---\n"
                "title: Draft Output\n"
                "---\n\n"
                "## Summary\n"
                "Ready for review.\n",
            )
        },
    )
    service = AgentService(tmp_path, runners={Tool.CLAUDE: runner, Tool.CODEX: runner})
    workflow = _workflow_fixture(tmp_path, service, advance=AdvanceMode.ASK)

    result = asyncio.run(
        WorkflowRuntime(tmp_path, service=service).run(
            workflow,
            prompts={"draft": "draft the artifact", "review": "review the artifact"},
        )
    )

    assert result.status == WorkflowStatus.AWAITING_CONFIRM
    assert len(result.steps) == 1
    assert result.steps[0].status == WorkflowStatus.AWAITING_CONFIRM
    assert result.steps[0].spawn_card is not None
    assert result.steps[0].spawn_card.gating.value == "green"
    assert runner.calls == ["node-001"]


def test_workflow_runtime_pauses_hitl_nodes_until_human_input(tmp_path):
    _write_context_files(tmp_path)
    runner = _WritingRunner(tmp_path)
    service = AgentService(tmp_path, runners={Tool.CLAUDE: runner, Tool.CODEX: runner})
    workflow = _workflow_fixture(
        tmp_path,
        service,
        advance=AdvanceMode.ALLOW,
        draft_interactivity=NodeInteractivity.HITL,
    )

    result = asyncio.run(
        WorkflowRuntime(tmp_path, service=service).run(
            workflow,
            prompts={"draft": "draft the artifact", "review": "review the artifact"},
        )
    )

    assert result.status == WorkflowStatus.WAITING_HUMAN
    assert len(result.steps) == 1
    assert result.steps[0].status == WorkflowStatus.WAITING_HUMAN
    assert result.steps[0].run_id is None
    assert runner.calls == []


def test_workflow_runtime_emits_live_state_updates(tmp_path):
    _write_context_files(tmp_path)
    runner = _WritingRunner(
        tmp_path,
        {
            "node-001": (
                "agents/artifacts/draft-output.md",
                "---\n"
                "title: Draft Output\n"
                "---\n\n"
                "## Summary\n"
                "Ready for review.\n",
            )
        },
    )
    service = AgentService(tmp_path, runners={Tool.CLAUDE: runner, Tool.CODEX: runner})
    workflow = _workflow_fixture(tmp_path, service, advance=AdvanceMode.ASK)
    updates = []

    result = asyncio.run(
        WorkflowRuntime(tmp_path, service=service).run(
            workflow,
            prompts={"draft": "draft the artifact", "review": "review the artifact"},
            on_update=updates.append,
        )
    )

    assert result.status == WorkflowStatus.AWAITING_CONFIRM
    assert [update["status"] for update in updates] == ["running", "awaiting_confirm"]
    assert updates[0]["nodes"]["draft"]["status"] == "running"
    assert updates[-1]["nodes"]["draft"]["status"] == "awaiting_confirm"
    assert updates[-1]["notifications"][-1]["kind"] == "node_done_green"


def _write_context_files(root):
    agents = root / "agents"
    (agents / "worker").mkdir(parents=True)
    (agents / "worker" / "claude.md").write_text("WORKER DIRECTIVE", encoding="utf-8")
    (agents / "worker" / "tdd.md").write_text("TDD PLAYBOOK", encoding="utf-8")
    (agents / "artifacts").mkdir(parents=True)
    (agents / "artifacts" / "issue-023.md").write_text("# Input\n", encoding="utf-8")
    (agents / "specs").mkdir(parents=True)
    (agents / "specs" / "draft-spec.md").write_text(
        "---\n"
        "title: Draft Spec\n"
        "---\n\n"
        "## Predicates\n"
        "- has_title()\n"
        "- has_summary()\n\n"
        "## Good Looks Like\n"
        "A complete draft.\n",
        encoding="utf-8",
    )


def _workflow_fixture(tmp_path, service, *, advance, draft_interactivity=NodeInteractivity.AFK):
    draft = create_node(
        service.state_db_path,
        tmp_path,
        name="Draft",
        provider="codex",
        tags=["worker"],
        rules=[],
        model="gpt-5.4",
        inputs=["agents/artifacts/issue-023.md"],
        outputs=["agents/specs/draft-spec.md"],
    )
    review = create_node(
        service.state_db_path,
        tmp_path,
        name="Review",
        provider="codex",
        tags=["worker"],
        rules=[],
        model="gpt-5.4",
        inputs=["agents/artifacts/draft-output.md"],
        outputs=[],
    )
    return Workflow(
        workflow_id="issue-023",
        placements=[
            Placement(
                placement_id="draft",
                node_id=draft.node_id,
                x=0,
                y=0,
                interactivity=draft_interactivity,
            ),
            Placement(
                placement_id="review",
                node_id=review.node_id,
                x=1,
                y=0,
                interactivity=NodeInteractivity.AFK,
            ),
        ],
        edges=[
            Edge(
                from_placement_id="draft",
                from_output="agents/artifacts/draft-output.md",
                to_placement_id="review",
                to_input="agents/artifacts/draft-output.md",
                advance=advance,
            )
        ],
    )
