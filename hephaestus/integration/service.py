"""Agent service: route a node run to the right runner and persist the lifecycle."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

from hephaestus.contract import ExecutionContract
from hephaestus.core import Severity, Violation
from hephaestus.eval_context import EvaluationContext
from hephaestus.index import build_context
from hephaestus.integration.context import SessionContext, build_session_context
from hephaestus.integration.providers import ProviderRegistry, provider_key, provider_registry
from hephaestus.integration.routing import Tool
from hephaestus.integration.runners import (
    AgentEvent,
    AgentRunner,
    AgentTask,
    ClaudeRunner,
    CodexRunner,
    EchoRunner,
)
from hephaestus.integration.runners import _extract_target_path
from hephaestus.rules.governance import ALL_GOVERNANCE_RULES
from hephaestus.rules.registry import run_layer
from hephaestus.store.db import connect
from hephaestus.store.nodes import Node, create_node, get_node
from hephaestus.store.runs import create_run, finish_run, interrupt_running_runs
from hephaestus.store.threads import append_turn, get_or_create_thread, list_turns
from hephaestus.store.trace import append_trace_event, list_trace_events
from hephaestus.store.violations import append_violation


@dataclass(frozen=True)
class PreparedRun:
    task: AgentTask
    contract: ExecutionContract
    node_id: str
    thread_id: str
    run_id: str
    tool: Tool | str
    ctx: SessionContext


class GovernanceViolationError(RuntimeError):
    def __init__(self, violations: list[Violation]):
        self.violations = list(violations)
        super().__init__(self._message())

    def _message(self) -> str:
        if not self.violations:
            return "Governance violation"
        return "; ".join(f"{v.rule_id}: {v.message}" for v in self.violations)


def _display_tool(provider: str) -> Tool | str:
    try:
        return Tool(provider)
    except ValueError:
        return provider


def _normalize_runners(runners: dict[Tool | str, AgentRunner]) -> dict[str, AgentRunner]:
    return {provider_key(key): runner for key, runner in runners.items()}


def default_runners(registry: ProviderRegistry | None = None) -> dict[str, AgentRunner]:
    return (registry or provider_registry()).runners()


class AgentService:
    def __init__(
        self,
        root: str | Path,
        runners: dict[Tool | str, AgentRunner] | None = None,
        registry: ProviderRegistry | None = None,
    ):
        self.root = Path(root).resolve()
        self.state_db_path = self.root / ".hephaestus" / "state.db"
        self.provider_registry = registry or provider_registry()
        self.runners = _normalize_runners(runners) if runners is not None else default_runners(self.provider_registry)
        self._locks: dict[str, asyncio.Lock] = {}
        interrupt_running_runs(self.state_db_path)

    def _session_context(
        self,
        *,
        node: Node,
        task: AgentTask,
        workflow_id: str | None,
        workflow_run_id: str | None,
        placement_id: str | None,
        thread_id: str | None = None,
    ) -> SessionContext:
        return build_session_context(
            self.root,
            node_id=node.node_id,
            tags=node.tags,
            issue_id=task.issue_id,
            skills=node.skills,
            inputs=node.inputs,
            outputs=node.outputs,
            db_path=self.state_db_path,
            workflow_id=workflow_id,
            workflow_run_id=workflow_run_id,
            placement_id=placement_id,
            thread_id=thread_id,
            machine=str(self.root),
        )

    def resolve(self, task: AgentTask, node: Node | None = None) -> tuple[Tool | str, SessionContext]:
        resolved = node or self._resolve_node(task)
        provider = self.provider_registry.provider_for_model(task.model) or task.provider or resolved.provider
        tool = _display_tool(provider)
        workflow_id = task.workflow_id or task.issue_id or None
        placement_id = task.placement_id or (resolved.node_id if workflow_id else None)
        ctx = self._session_context(
            node=resolved,
            task=task,
            workflow_id=workflow_id,
            workflow_run_id=task.workflow_run_id or None,
            placement_id=placement_id,
        )
        return tool, ctx

    def task_for_node(
        self,
        *,
        node_id: str,
        prompt: str,
        issue_id: str | None = None,
        cwd: str | Path | None = None,
        model: str | None = None,
        effort: str | None = None,
        workflow_id: str | None = None,
        workflow_run_id: str | None = None,
        placement_id: str | None = None,
    ) -> AgentTask:
        node = get_node(self.state_db_path, node_id)
        return AgentTask(
            node_id=node_id,
            provider=node.provider,
            tags=node.tags,
            prompt=prompt,
            issue_id=issue_id or None,
            cwd=Path(cwd) if cwd else (Path(node.working_dir) if node.working_dir else None),
            model=model or node.model,
            effort=effort or node.effort,
            workflow_id=workflow_id or None,
            workflow_run_id=workflow_run_id or None,
            placement_id=placement_id or None,
        )

    def task_for_ad_hoc(
        self,
        *,
        provider: str,
        tags: list[str],
        prompt: str,
        issue_id: str | None = None,
        cwd: str | Path | None = None,
        model: str | None = None,
        effort: str | None = None,
        workflow_id: str | None = None,
        workflow_run_id: str | None = None,
        placement_id: str | None = None,
    ) -> AgentTask:
        return AgentTask(
            node_id=None,
            provider=provider,
            tags=list(tags),
            prompt=prompt,
            issue_id=issue_id or None,
            cwd=Path(cwd) if cwd else None,
            model=model or None,
            effort=effort or None,
            workflow_id=workflow_id or None,
            workflow_run_id=workflow_run_id or None,
            placement_id=placement_id or None,
        )

    def begin_node_run(
        self,
        *,
        node_id: str,
        prompt: str,
        issue_id: str | None = None,
        cwd: str | Path | None = None,
        model: str | None = None,
        effort: str | None = None,
        workflow_id: str | None = None,
        workflow_run_id: str | None = None,
        placement_id: str | None = None,
    ) -> PreparedRun:
        return self.begin(
            self.task_for_node(
                node_id=node_id,
                prompt=prompt,
                issue_id=issue_id,
                cwd=cwd,
                model=model,
                effort=effort,
                workflow_id=workflow_id,
                workflow_run_id=workflow_run_id,
                placement_id=placement_id,
            )
        )

    def begin_ad_hoc_run(
        self,
        *,
        provider: str,
        tags: list[str],
        prompt: str,
        issue_id: str | None = None,
        cwd: str | Path | None = None,
        model: str | None = None,
        effort: str | None = None,
        workflow_id: str | None = None,
        workflow_run_id: str | None = None,
        placement_id: str | None = None,
    ) -> PreparedRun:
        return self.begin(
            self.task_for_ad_hoc(
                provider=provider,
                tags=tags,
                prompt=prompt,
                issue_id=issue_id,
                cwd=cwd,
                model=model,
                effort=effort,
                workflow_id=workflow_id,
                workflow_run_id=workflow_run_id,
                placement_id=placement_id,
            )
        )

    def begin(self, task: AgentTask) -> PreparedRun:
        node = self._resolve_node(task)
        provider = self.provider_registry.provider_for_model(task.model) or task.provider or node.provider
        tool = _display_tool(provider)
        workflow_id = task.workflow_id or task.issue_id or None
        workflow_run_id = task.workflow_run_id or uuid4().hex
        placement_id = task.placement_id or (node.node_id if workflow_id else None)
        thread = get_or_create_thread(
            self.state_db_path,
            node_id=node.node_id,
            name=task.issue_id or node.name,
            workflow_id=workflow_id,
            workflow_run_id=workflow_run_id,
            placement_id=placement_id,
            issue_id=task.issue_id,
        )
        ctx = self._session_context(
            node=node,
            task=task,
            workflow_id=workflow_id,
            workflow_run_id=workflow_run_id,
            placement_id=placement_id,
            thread_id=thread.id,
        )
        contract = self._contract(
            node,
            task,
            tool,
            context=thread.id,
            workflow_id=workflow_id,
            workflow_run_id=workflow_run_id,
            placement_id=placement_id,
        )
        run = create_run(
            self.state_db_path,
            thread_id=thread.id,
            node_id=node.node_id,
            contract=contract.as_dict(),
        )
        append_turn(
            self.state_db_path,
            thread.id,
            run_id=run.id,
            role="user",
            kind="text",
            text=task.prompt,
        )
        return PreparedRun(
            task=task,
            contract=contract,
            node_id=node.node_id,
            thread_id=thread.id,
            run_id=run.id,
            tool=tool,
            ctx=ctx,
        )

    async def run(self, work: AgentTask | PreparedRun) -> AsyncIterator[AgentEvent]:
        prepared = work if isinstance(work, PreparedRun) else self.begin(work)
        contract = prepared.contract
        runner = self.runners[provider_key(prepared.tool)]
        lock = self._locks.setdefault(prepared.node_id, asyncio.Lock())
        usage = None
        actual_model = contract.actual_model

        async with lock:
            try:
                async for event in runner.run(contract, prepared.ctx):
                    if event.kind == "result" and event.raw:
                        usage = event.raw.get("usage")
                        actual_model = event.raw.get("actual_model", actual_model)

                    if event.persist:
                        append_turn(
                            self.state_db_path,
                            prepared.thread_id,
                            run_id=prepared.run_id,
                            role=event.transcript_role or "assistant",
                            kind=event.kind,
                            text=event.text,
                        )
                    if event.category == "tool" and event.raw:
                        append_trace_event(
                            self.state_db_path,
                            run_id=prepared.run_id,
                            node_id=prepared.node_id,
                            action=event.raw.get("action", "unknown"),
                            target_path=_extract_target_path(event.raw.get("input") or {}),
                            raw=event.raw,
                        )
                    yield event
            except Exception as exc:
                final_contract = contract.with_updates(actual_model=actual_model or contract.model)
                append_turn(
                    self.state_db_path,
                    prepared.thread_id,
                    run_id=prepared.run_id,
                    role="assistant",
                    kind="error",
                    text=str(exc),
                )
                finish_run(
                    self.state_db_path,
                    prepared.run_id,
                    status="error",
                    contract=final_contract.as_dict(),
                )
                raise
            else:
                final_contract = contract.with_updates(actual_model=actual_model or contract.model)
                violations = self._evaluate_governance(prepared, final_contract)
                error_violations = [v for v in violations if v.severity == Severity.ERROR]
                finish_run(
                    self.state_db_path,
                    prepared.run_id,
                    status="error" if error_violations else "done",
                    usage=usage,
                    contract=final_contract.as_dict(),
                )
                if error_violations:
                    raise GovernanceViolationError(error_violations)

    def _resolve_node(self, task: AgentTask) -> Node:
        if task.node_id:
            return get_node(self.state_db_path, task.node_id)

        provider = self.provider_registry.provider_for_model(task.model) or task.provider
        if not provider:
            raise ValueError("provider is required when no node_id is supplied")
        name = " ".join(part.title() for part in (task.tags or [provider]))
        return create_node(
            self.state_db_path,
            self.root,
            name=name or provider.title(),
            provider=provider,
            tags=task.tags,
            rules=[],
            model=task.model,
            effort=task.effort,
            working_dir=str(task.cwd) if task.cwd else None,
        )

    def _contract(
        self,
        node: Node,
        task: AgentTask,
        tool: Tool | str,
        *,
        context: str,
        workflow_id: str | None,
        workflow_run_id: str,
        placement_id: str | None,
    ) -> ExecutionContract:
        model = task.model or node.model
        effort = task.effort or node.effort
        if workflow_id and placement_id:
            scope = f"workflow:{workflow_id}/placement:{placement_id}"
        else:
            scope = f"node:{node.node_id}"
        provider = self.provider_registry.provider_for_model(model) or task.provider or node.provider
        return ExecutionContract(
            actor=node.node_id,
            node_id=node.node_id,
            provider=provider,
            tags=node.tags,
            context=context,
            scope=scope,
            model=model,
            effort=effort,
            tools=list(node.allowed_tools),
            prompt=task.prompt,
            tool=provider_key(tool),
            issue_id=task.issue_id,
            cwd=str(task.cwd) if task.cwd else node.working_dir,
            workflow_id=workflow_id,
            workflow_run_id=workflow_run_id,
            placement_id=placement_id,
            allowed_paths=list(node.allowed_paths),
            skill_obligations=list(node.skill_obligations),
        )

    def _evaluate_governance(self, prepared: PreparedRun, contract: ExecutionContract) -> list[Violation]:
        trace = list_trace_events(self.state_db_path, run_id=prepared.run_id)
        turns = [turn for turn in list_turns(self.state_db_path, prepared.thread_id) if turn.run_id == prepared.run_id]
        ctx = EvaluationContext(
            okf=build_context(self.root),
            turns=turns,
            trace=trace,
            contract=contract.as_dict(),
            actor=prepared.node_id,
            scope=contract.scope,
        )
        violations = run_layer(ALL_GOVERNANCE_RULES, ctx, layer="governance")
        if violations:
            with connect(self.state_db_path) as db:
                for violation in violations:
                    append_violation(
                        db,
                        violation,
                        run_id=prepared.run_id,
                        node_id=prepared.node_id,
                        issue_id=contract.issue_id,
                    )
        return violations


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="hephaestus.integration", description="Run a node-task.")
    p.add_argument("provider", choices=[tool.value for tool in Tool])
    p.add_argument("prompt")
    p.add_argument("--tags", default="", help="comma-separated tags")
    p.add_argument("--issue", help="issue id to inject the spec for")
    p.add_argument("--root", default=".", help="OKF root (containing agents/)")
    p.add_argument("--cwd", help="working directory for the agent")
    p.add_argument("--model", help="override model")
    p.add_argument("--effort", help="reasoning effort (low|medium|high|xhigh|max)")
    p.add_argument("--echo", action="store_true", help="dry-run: print routing + context, no live call")
    args = p.parse_args(argv)

    runners = None
    if args.echo:
        runners = {Tool.CLAUDE: EchoRunner(Tool.CLAUDE), Tool.CODEX: EchoRunner(Tool.CODEX)}

    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    service = AgentService(args.root, runners=runners)
    task = AgentTask(
        node_id=None,
        provider=args.provider,
        tags=tags,
        prompt=args.prompt,
        issue_id=args.issue,
        cwd=Path(args.cwd) if args.cwd else None,
        model=args.model,
        effort=args.effort,
    )
    tool, ctx = service.resolve(task)
    print(f"-> provider={task.provider}  tool={getattr(tool, 'value', tool)}  context={[p.name for p in ctx.files]}")
    if ctx.missing:
        print(f"  (missing OKF files: {[p.name for p in ctx.missing]})")

    async def go() -> None:
        async for ev in service.run(task):
            print(f"[{ev.kind}] {ev.text}")

    asyncio.run(go())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
