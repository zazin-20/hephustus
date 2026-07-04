"""Gatekeeper workflow runtime for node-by-node execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4

from hephaestus.artifact_spec import check_artifact, load_artifact_spec
from hephaestus.contract import ExecutionContract
from hephaestus.core import Severity, Violation, ViolationResult
from hephaestus.eval_context import EvaluationContext
from hephaestus.handoff import HandoffMarker, SpawnCard, SpawnGating, evaluate_spawn_gate, has_skill_completion
from hephaestus.index import build_context
from hephaestus.integration.service import AgentService
from hephaestus.okf_layout import OKFLayout
from hephaestus.rules.base import HephaestusRule
from hephaestus.skills import resolve_skill_ref
from hephaestus.store.nodes import Node, get_node
from hephaestus.store.runs import get_run
from hephaestus.store.threads import list_turns
from hephaestus.store.trace import list_trace_events
from hephaestus.workflows import AdvanceMode, Edge, NodeInteractivity, Placement, Workflow


class WorkflowStatus(str, Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    BLOCKED = "blocked"
    AWAITING_CONFIRM = "awaiting_confirm"
    DONE = "done"


@dataclass(slots=True)
class WorkflowStepResult:
    placement_id: str
    node_id: str
    status: WorkflowStatus
    run_id: str | None = None
    thread_id: str | None = None
    contract: ExecutionContract | None = None
    failures: list[Violation] = field(default_factory=list)
    spawn_card: SpawnCard | None = None
    override_available: bool = False


@dataclass(slots=True)
class WorkflowRunResult:
    workflow_id: str
    workflow_run_id: str
    status: WorkflowStatus
    steps: list[WorkflowStepResult]


class _ArtifactExitRule(HephaestusRule):
    layer = "exit"
    scope = "workflow"

    def __init__(self, *, spec_path: Path, artifact_path: Path, index: int) -> None:
        self.id = f"WF-OUT-{index:03d}"
        self.name = f"artifact gate: {spec_path.name}"
        self._spec = load_artifact_spec(spec_path)
        self._artifact_path = artifact_path

    def check(self, ctx) -> ViolationResult:
        if not self._artifact_path.is_file():
            return ViolationResult.of(
                [
                    Violation(
                        rule_id=self.id,
                        severity=Severity.ERROR,
                        message=f"Required output artifact is missing: {self._artifact_path}",
                        artifact=str(self._artifact_path),
                        fix_hint="Produce the required artifact before advancing.",
                    )
                ]
            )
        return ViolationResult.of(check_artifact(self._spec, self._artifact_path))


class _SkillExitRule(HephaestusRule):
    layer = "exit"
    scope = "workflow"

    def __init__(self, *, layout: OKFLayout, ref: str, index: int) -> None:
        skill = resolve_skill_ref(layout, ref)
        self.id = f"WF-SKILL-{index:03d}"
        self.name = f"skill gate: {skill.skill_id}"
        self._skill_id = skill.skill_id

    def check(self, ctx) -> ViolationResult:
        if has_skill_completion(self._skill_id, turns=ctx.turns, trace=ctx.trace):
            return ViolationResult.of([])
        return ViolationResult.of(
            [
                Violation(
                    rule_id=self.id,
                    severity=Severity.ERROR,
                    message=f"Required skill marker was not emitted for {self._skill_id!r}.",
                    artifact=self._skill_id,
                    fix_hint="Emit a @@HEPHAESTUS@@ skill_complete marker with ok=true.",
                )
            ]
        )


class WorkflowRuntime:
    def __init__(self, root: str | Path, *, service: AgentService | None = None) -> None:
        self.root = Path(root).resolve()
        self.service = service or AgentService(self.root)
        self.layout = OKFLayout.for_existing_root(self.root)

    async def run(
        self,
        workflow: Workflow,
        *,
        prompts: dict[str, str],
        issue_id: str | None = None,
        confirm_edges: set[tuple[str, str]] | None = None,
        override_placements: set[str] | None = None,
        human_inputs: dict[str, str] | None = None,
    ) -> WorkflowRunResult:
        placements = {placement.placement_id: placement for placement in workflow.placements}
        outgoing = self._outgoing_edges(workflow.edges)
        confirm_edges = set(confirm_edges or set())
        override_placements = set(override_placements or set())
        human_inputs = dict(human_inputs or {})
        queue = self._start_placements(workflow)
        steps: list[WorkflowStepResult] = []
        workflow_run_id = uuid4().hex

        while queue:
            placement_id = queue.pop(0)
            placement = placements[placement_id]
            node = get_node(self.service.state_db_path, placement.node_id)

            if placement.interactivity == NodeInteractivity.HITL and placement_id not in human_inputs:
                step = WorkflowStepResult(
                    placement_id=placement_id,
                    node_id=node.node_id,
                    status=WorkflowStatus.WAITING_HUMAN,
                )
                steps.append(step)
                return WorkflowRunResult(
                    workflow_id=workflow.workflow_id,
                    workflow_run_id=workflow_run_id,
                    status=WorkflowStatus.WAITING_HUMAN,
                    steps=steps,
                )

            entry_failures = self._entry_failures(node)
            if entry_failures:
                step = WorkflowStepResult(
                    placement_id=placement_id,
                    node_id=node.node_id,
                    status=WorkflowStatus.BLOCKED,
                    failures=entry_failures,
                    override_available=True,
                )
                steps.append(step)
                if placement_id not in override_placements:
                    return WorkflowRunResult(
                        workflow_id=workflow.workflow_id,
                        workflow_run_id=workflow_run_id,
                        status=WorkflowStatus.BLOCKED,
                        steps=steps,
                    )

            prompt = prompts[placement_id]
            if placement_id in human_inputs:
                prompt = f"{prompt}\n\nHuman input:\n{human_inputs[placement_id]}"

            prepared = self.service.begin_node_run(
                node_id=node.node_id,
                prompt=prompt,
                issue_id=issue_id or workflow.workflow_id,
                workflow_id=workflow.workflow_id,
                workflow_run_id=workflow_run_id,
                placement_id=placement_id,
            )
            async for _ in self.service.run(prepared):
                pass

            run = get_run(self.service.state_db_path, prepared.run_id)
            contract = prepared.contract.with_updates(actual_model=run.contract.get("actual_model"))
            ctx = EvaluationContext(
                okf=build_context(self.root),
                turns=list_turns(self.service.state_db_path, prepared.thread_id),
                trace=list_trace_events(self.service.state_db_path, thread_id=prepared.thread_id),
                contract=run.contract,
                actor=node.node_id,
                scope=prepared.contract.scope,
            )
            next_edges = outgoing.get(placement_id, [])
            marker = self._spawn_marker(workflow, placement_id, next_edges)
            card = evaluate_spawn_gate(
                marker,
                ctx,
                exit_rules=self._exit_rules(node, next_edges),
            )
            if card.gating == SpawnGating.AMBER and placement_id not in override_placements:
                step = WorkflowStepResult(
                    placement_id=placement_id,
                    node_id=node.node_id,
                    status=WorkflowStatus.BLOCKED,
                    run_id=prepared.run_id,
                    thread_id=prepared.thread_id,
                    contract=contract,
                    failures=list(card.failures),
                    spawn_card=card,
                    override_available=True,
                )
                steps.append(step)
                return WorkflowRunResult(
                    workflow_id=workflow.workflow_id,
                    workflow_run_id=workflow_run_id,
                    status=WorkflowStatus.BLOCKED,
                    steps=steps,
                )

            ask_edge = next((edge for edge in next_edges if edge.advance == AdvanceMode.ASK), None)
            if ask_edge is not None and (ask_edge.from_placement_id, ask_edge.to_placement_id) not in confirm_edges:
                step = WorkflowStepResult(
                    placement_id=placement_id,
                    node_id=node.node_id,
                    status=WorkflowStatus.AWAITING_CONFIRM,
                    run_id=prepared.run_id,
                    thread_id=prepared.thread_id,
                    contract=contract,
                    spawn_card=card,
                )
                steps.append(step)
                return WorkflowRunResult(
                    workflow_id=workflow.workflow_id,
                    workflow_run_id=workflow_run_id,
                    status=WorkflowStatus.AWAITING_CONFIRM,
                    steps=steps,
                )

            steps.append(
                WorkflowStepResult(
                    placement_id=placement_id,
                    node_id=node.node_id,
                    status=WorkflowStatus.DONE,
                    run_id=prepared.run_id,
                    thread_id=prepared.thread_id,
                    contract=contract,
                    spawn_card=card if next_edges else None,
                )
            )
            for edge in next_edges:
                if edge.advance == AdvanceMode.ALLOW or (
                    edge.from_placement_id,
                    edge.to_placement_id,
                ) in confirm_edges:
                    if edge.to_placement_id not in queue and edge.to_placement_id not in {
                        step.placement_id for step in steps
                    }:
                        queue.append(edge.to_placement_id)

        return WorkflowRunResult(
            workflow_id=workflow.workflow_id,
            workflow_run_id=workflow_run_id,
            status=WorkflowStatus.DONE,
            steps=steps,
        )

    def _entry_failures(self, node: Node) -> list[Violation]:
        failures: list[Violation] = []
        for declared in node.inputs:
            path = self._resolve_path(declared)
            if path.is_file():
                continue
            failures.append(
                Violation(
                    rule_id="WF-ENTRY-001",
                    severity=Severity.ERROR,
                    message=f"Required input artifact is missing: {path}",
                    artifact=str(path),
                    fix_hint="Provide the declared input artifact before running the node.",
                )
            )
        return failures

    def _exit_rules(self, node: Node, edges: list[Edge]) -> list[HephaestusRule]:
        rules: list[HephaestusRule] = []
        for index, (spec_path, artifact_path) in enumerate(self._output_bindings(node, edges), start=1):
            rules.append(_ArtifactExitRule(spec_path=spec_path, artifact_path=artifact_path, index=index))
        for index, ref in enumerate(node.skill_obligations, start=1):
            rules.append(_SkillExitRule(layout=self.layout, ref=ref, index=index))
        return rules

    def _output_bindings(self, node: Node, edges: list[Edge]) -> list[tuple[Path, Path]]:
        if not node.outputs:
            return []
        artifact_paths = []
        seen: set[str] = set()
        for edge in edges:
            if edge.from_output not in seen:
                artifact_paths.append(edge.from_output)
                seen.add(edge.from_output)
        if not artifact_paths:
            return []
        if len(node.outputs) == 1:
            spec_path = self._resolve_path(node.outputs[0])
            return [(spec_path, self._resolve_path(path)) for path in artifact_paths]
        if len(node.outputs) != len(artifact_paths):
            raise ValueError(
                f"Node {node.node_id} declares {len(node.outputs)} outputs but routes {len(artifact_paths)} artifacts."
            )
        return [
            (self._resolve_path(spec_path), self._resolve_path(artifact_path))
            for spec_path, artifact_path in zip(node.outputs, artifact_paths, strict=True)
        ]

    def _spawn_marker(
        self,
        workflow: Workflow,
        placement_id: str,
        edges: list[Edge],
    ) -> HandoffMarker:
        if edges:
            edge = edges[0]
            return HandoffMarker(
                role=edge.to_placement_id,
                task=edge.to_input,
                issue_id=workflow.workflow_id,
            )
        return HandoffMarker(
            role=placement_id,
            task="workflow-complete",
            issue_id=workflow.workflow_id,
        )

    def _resolve_path(self, declared: str) -> Path:
        path = Path(declared)
        if path.is_absolute():
            return path
        return self.root / path

    @staticmethod
    def _outgoing_edges(edges: list[Edge]) -> dict[str, list[Edge]]:
        out: dict[str, list[Edge]] = {}
        for edge in edges:
            out.setdefault(edge.from_placement_id, []).append(edge)
        return out

    @staticmethod
    def _start_placements(workflow: Workflow) -> list[str]:
        incoming = {placement.placement_id: 0 for placement in workflow.placements}
        for edge in workflow.edges:
            incoming[edge.to_placement_id] += 1
        ordered = [placement.placement_id for placement in workflow.placements if incoming[placement.placement_id] == 0]
        return ordered
