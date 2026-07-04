"""Resolve a governed ExecutionContract from node state and assembled context."""

from __future__ import annotations

from hephaestus.contract import ExecutionContract
from hephaestus.integration.context import SessionContext
from hephaestus.integration.providers import ProviderRegistry, provider_key, provider_registry
from hephaestus.integration.runners import AgentTask
from hephaestus.store.nodes import Node


def resolve(
    *,
    node: Node,
    task: AgentTask,
    session_context: SessionContext,
    context_id: str,
    workflow_id: str | None = None,
    workflow_run_id: str | None = None,
    placement_id: str | None = None,
    registry: ProviderRegistry | None = None,
) -> ExecutionContract:
    if session_context.node_id != node.node_id:
        raise ValueError(
            f"session_context.node_id={session_context.node_id!r} does not match node.node_id={node.node_id!r}"
        )

    resolved_workflow_id = workflow_id if workflow_id is not None else (task.workflow_id or task.issue_id or None)
    resolved_workflow_run_id = workflow_run_id if workflow_run_id is not None else task.workflow_run_id
    resolved_placement_id = placement_id
    if resolved_placement_id is None:
        resolved_placement_id = task.placement_id or (node.node_id if resolved_workflow_id else None)

    model = task.model or node.model
    effort = task.effort or node.effort
    resolved_provider = (registry or provider_registry()).provider_for_model(model) or task.provider or node.provider
    if resolved_workflow_id and resolved_placement_id:
        scope = f"workflow:{resolved_workflow_id}/placement:{resolved_placement_id}"
    else:
        scope = f"node:{node.node_id}"

    return ExecutionContract(
        actor=node.node_id,
        node_id=node.node_id,
        provider=resolved_provider,
        tags=list(node.tags),
        context=context_id,
        scope=scope,
        model=model,
        effort=effort,
        tools=list(node.allowed_tools),
        prompt=task.prompt,
        tool=provider_key(resolved_provider),
        issue_id=task.issue_id,
        cwd=str(task.cwd) if task.cwd else node.working_dir,
        workflow_id=resolved_workflow_id,
        workflow_run_id=resolved_workflow_run_id,
        placement_id=resolved_placement_id,
        allowed_paths=list(node.allowed_paths),
        skill_obligations=list(node.skill_obligations),
    )
