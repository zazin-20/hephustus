"""Agent service: route a task to the right runner and persist the run lifecycle."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from pathlib import Path
from typing import AsyncIterator

from hephaestus.contract import ExecutionContract
from hephaestus.eval_context import EvaluationContext
from hephaestus.integration.context import SessionContext, build_session_context
from hephaestus.integration.providers import ProviderRegistry, provider_key, provider_registry
from hephaestus.integration.routing import Role, Tool, tool_for
from hephaestus.integration.runners import (
    AgentEvent,
    AgentRunner,
    AgentTask,
    ClaudeRunner,
    CodexRunner,
)
from hephaestus.index import build_context
from hephaestus.rules.governance import ALL_GOVERNANCE_RULES
from hephaestus.rules.registry import run_layer
from hephaestus.store.db import connect
from hephaestus.store.profiles import Profile, create_profile, get_profile, list_profiles
from hephaestus.store.runs import create_run, finish_run, interrupt_running_runs
from hephaestus.store.threads import append_turn, compile_context, get_or_create_thread
from hephaestus.store.trace import append_trace_event, list_trace_events
from hephaestus.store.violations import append_violation
from hephaestus.integration.runners import _extract_target_path


class SessionRegistry:
    """Sessions tagged by actor + issue id for resumability."""

    def __init__(self):
        self._sessions: dict[str, str] = {}

    @staticmethod
    def key(role: Role | str, issue_id: str | None, agent_id: str | None = None) -> str:
        actor = agent_id or (role.value if isinstance(role, Role) else str(role))
        return f"{actor}:{issue_id}" if issue_id else actor

    def get(
        self,
        role: Role | str,
        issue_id: str | None = None,
        agent_id: str | None = None,
    ) -> str | None:
        return self._sessions.get(self.key(role, issue_id, agent_id))

    def set(
        self,
        role: Role | str,
        issue_id: str | None,
        session_id: str,
        agent_id: str | None = None,
    ) -> None:
        self._sessions[self.key(role, issue_id, agent_id)] = session_id

    def all(self) -> dict[str, str]:
        return dict(self._sessions)


@dataclass(frozen=True)
class PreparedRun:
    task: AgentTask
    contract: ExecutionContract
    agent_id: str
    thread_id: str
    run_id: str
    tool: Tool | str
    ctx: SessionContext


def _display_tool(provider: str) -> Tool | str:
    try:
        return Tool(provider)
    except ValueError:
        return provider


def _normalize_runners(runners: dict[Tool | str, AgentRunner]) -> dict[str, AgentRunner]:
    return {provider_key(key): runner for key, runner in runners.items()}


def default_runners(registry: ProviderRegistry | None = None) -> dict[str, AgentRunner]:
    return (registry or provider_registry()).runners()


def _compile_history(db_path, thread_id: str, current_run_id: str) -> str:
    """Format included prior turns (excluding current run) as a context block."""
    turns = [t for t in compile_context(db_path, thread_id) if t.run_id != current_run_id]
    if not turns:
        return ""
    lines = ["--- Prior context ---"]
    for turn in turns:
        lines.append(f"[{turn.role}] {turn.text}")
    lines.append("--- End prior context ---")
    return "\n".join(lines)


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
        self.registry = SessionRegistry()
        self._locks: dict[str, asyncio.Lock] = {}
        interrupt_running_runs(self.state_db_path)

    def resolve(self, task: AgentTask) -> tuple[Tool | str, SessionContext]:
        provider = self.provider_registry.provider_for_model(task.model)
        tool = _display_tool(provider) if provider is not None else tool_for(task.role, registry=self.provider_registry)
        ctx = build_session_context(self.root, task.role, task.issue_id)
        return tool, ctx

    def task_for_role(
        self,
        *,
        role: Role | str,
        prompt: str,
        issue_id: str | None = None,
        cwd: str | Path | None = None,
        model: str | None = None,
        effort: str | None = None,
    ) -> AgentTask:
        return AgentTask(
            role=Role(role),
            prompt=prompt,
            issue_id=issue_id or None,
            cwd=Path(cwd) if cwd else None,
            model=model or None,
            effort=effort or None,
        )

    def task_for_profile(
        self,
        *,
        agent_id: str,
        prompt: str,
        issue_id: str | None = None,
        model: str | None = None,
    ) -> AgentTask:
        profile = get_profile(self.state_db_path, agent_id)
        return AgentTask(
            role=Role(profile.role),
            prompt=prompt,
            issue_id=issue_id or None,
            agent_id=agent_id,
            cwd=Path(profile.working_dir) if profile.working_dir else None,
            model=model or profile.model,
            effort=profile.effort,
        )

    def begin_role_run(
        self,
        *,
        role: Role | str,
        prompt: str,
        issue_id: str | None = None,
        cwd: str | Path | None = None,
        model: str | None = None,
        effort: str | None = None,
    ) -> PreparedRun:
        return self.begin(
            self.task_for_role(
                role=role,
                prompt=prompt,
                issue_id=issue_id,
                cwd=cwd,
                model=model,
                effort=effort,
            )
        )

    def begin_profile_run(
        self,
        *,
        agent_id: str,
        prompt: str,
        issue_id: str | None = None,
        model: str | None = None,
    ) -> PreparedRun:
        return self.begin(
            self.task_for_profile(
                agent_id=agent_id,
                prompt=prompt,
                issue_id=issue_id,
                model=model,
            )
        )

    def begin(self, task: AgentTask) -> PreparedRun:
        profile = self._resolve_profile(task)
        task = replace(task, agent_id=profile.agent_id)
        tool, ctx = self.resolve(task)
        thread = get_or_create_thread(
            self.state_db_path,
            agent_id=profile.agent_id,
            issue_id=task.issue_id,
            name=task.issue_id or profile.name,
        )
        run = create_run(
            self.state_db_path,
            thread_id=thread.id,
            agent_id=profile.agent_id,
            contract=self._contract(profile, task, tool, context=thread.id).as_dict(),
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
            contract=self._contract(profile, task, tool, context=thread.id),
            agent_id=profile.agent_id,
            thread_id=thread.id,
            run_id=run.id,
            tool=tool,
            ctx=ctx,
        )

    async def run(self, work: AgentTask | PreparedRun) -> AsyncIterator[AgentEvent]:
        prepared = work if isinstance(work, PreparedRun) else self.begin(work)
        task = prepared.task
        contract = prepared.contract

        if contract.resume is None:
            prior = self.registry.get(task.role, task.issue_id, prepared.agent_id)
            if prior:
                contract = contract.with_updates(resume=prior)
                prepared = replace(prepared, contract=contract)

        # Prepend compiled history from prior included turns (client-owned context, D5).
        history = _compile_history(self.state_db_path, prepared.thread_id, prepared.run_id)
        ctx = prepared.ctx
        if history:
            ctx = replace(ctx, system_prompt=history + "\n\n" + ctx.system_prompt if ctx.system_prompt else history)
            prepared = replace(prepared, ctx=ctx)

        runner = self.runners[provider_key(prepared.tool)]
        lock = self._locks.setdefault(prepared.agent_id, asyncio.Lock())
        usage = None
        actual_model = contract.actual_model

        async with lock:
            try:
                async for event in runner.run(contract, prepared.ctx):
                    if event.kind == "result" and event.raw and event.raw.get("session_id"):
                        self.registry.set(
                            task.role,
                            task.issue_id,
                            event.raw["session_id"],
                            prepared.agent_id,
                        )
                    if event.kind == "result" and event.raw:
                        usage = event.raw.get("usage")
                        actual_model = event.raw.get("actual_model", actual_model)

                    # Persist content (text/thinking/error) and tool calls; skip empty
                    # lifecycle envelopes (system/result) so they don't pollute the
                    # transcript or the compiled context fed to the next run.
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
                            agent_id=prepared.agent_id,
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
                finish_run(
                    self.state_db_path,
                    prepared.run_id,
                    status="done",
                    usage=usage,
                    contract=final_contract.as_dict(),
                )
                self._evaluate_governance(prepared, final_contract)

    def _resolve_profile(self, task: AgentTask) -> Profile:
        profiles = list_profiles(self.state_db_path)
        if task.agent_id:
            for profile in profiles:
                if profile.agent_id == task.agent_id:
                    return profile
            raise KeyError(task.agent_id)

        for profile in profiles:
            if profile.role == task.role.value:
                return profile

        return create_profile(
            self.state_db_path,
            self.root,
            name=task.role.value.replace("-", " ").title(),
            role=task.role.value,
            rules=[],
            model=task.model,
            effort=task.effort,
            working_dir=str(task.cwd) if task.cwd else None,
        )

    def _contract(
        self,
        profile: Profile,
        task: AgentTask,
        tool: Tool | str,
        *,
        context: str,
    ) -> ExecutionContract:
        return ExecutionContract(
            actor=profile.agent_id,
            role=profile.role,
            context=context,
            scope=f"issue:{task.issue_id}" if task.issue_id else "workspace",
            model=task.model or profile.model,
            effort=task.effort or profile.effort,
            tools=[],
            prompt=task.prompt,
            tool=provider_key(tool),
            issue_id=task.issue_id,
            cwd=str(task.cwd) if task.cwd else profile.working_dir,
            resume=task.resume,
        )

    def _evaluate_governance(self, prepared: PreparedRun, contract: ExecutionContract) -> None:
        trace = list_trace_events(self.state_db_path, run_id=prepared.run_id)
        ctx = EvaluationContext(
            okf=build_context(self.root),
            trace=trace,
            contract=contract.as_dict(),
            actor=prepared.agent_id,
            scope=contract.scope,
        )
        violations = run_layer(ALL_GOVERNANCE_RULES, ctx, layer="governance")
        if not violations:
            return
        with connect(self.state_db_path) as db:
            for violation in violations:
                append_violation(
                    db,
                    violation,
                    run_id=prepared.run_id,
                    agent_id=prepared.agent_id,
                    issue_id=contract.issue_id,
                )


def main(argv: list[str] | None = None) -> int:
    import argparse

    from hephaestus.integration.runners import EchoRunner

    p = argparse.ArgumentParser(prog="hephaestus.integration", description="Run a role-routed agent task.")
    p.add_argument("role", choices=[r.value for r in Role])
    p.add_argument("prompt")
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

    service = AgentService(args.root, runners=runners)
    task = AgentTask(
        role=Role(args.role),
        prompt=args.prompt,
        issue_id=args.issue,
        cwd=Path(args.cwd) if args.cwd else None,
        model=args.model,
        effort=args.effort,
    )
    tool, ctx = service.resolve(task)
    print(f"-> role={task.role.value}  tool={tool.value}  context={[p.name for p in ctx.files]}")
    if ctx.missing:
        print(f"  (missing OKF files: {[p.name for p in ctx.missing]})")

    async def go() -> None:
        async for ev in service.run(task):
            print(f"[{ev.kind}] {ev.text}")

    asyncio.run(go())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
