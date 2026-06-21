"""Agent service: route a task to the right runner and persist the run lifecycle."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from pathlib import Path
from typing import AsyncIterator

from hephaestus.integration.context import SessionContext, build_session_context
from hephaestus.integration.routing import Role, Tool, tool_for
from hephaestus.integration.runners import (
    AgentEvent,
    AgentRunner,
    AgentTask,
    ClaudeRunner,
    CodexRunner,
)
from hephaestus.store.profiles import Profile, create_profile, list_profiles
from hephaestus.store.runs import create_run, finish_run, interrupt_running_runs
from hephaestus.store.threads import append_turn, compile_context, get_or_create_thread
from hephaestus.store.trace import append_trace_event
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
    agent_id: str
    thread_id: str
    run_id: str
    tool: Tool
    ctx: SessionContext


def default_runners() -> dict[Tool, AgentRunner]:
    return {Tool.CLAUDE: ClaudeRunner(), Tool.CODEX: CodexRunner()}


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
    def __init__(self, root: str | Path, runners: dict[Tool, AgentRunner] | None = None):
        self.root = Path(root).resolve()
        self.state_db_path = self.root / ".hephaestus" / "state.db"
        self.runners = runners or default_runners()
        self.registry = SessionRegistry()
        self._locks: dict[str, asyncio.Lock] = {}
        interrupt_running_runs(self.state_db_path)

    def resolve(self, task: AgentTask) -> tuple[Tool, SessionContext]:
        tool = tool_for(task.role)
        ctx = build_session_context(self.root, task.role, task.issue_id)
        return tool, ctx

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
            contract=self._contract(profile, task, tool),
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
            agent_id=profile.agent_id,
            thread_id=thread.id,
            run_id=run.id,
            tool=tool,
            ctx=ctx,
        )

    async def run(self, work: AgentTask | PreparedRun) -> AsyncIterator[AgentEvent]:
        prepared = work if isinstance(work, PreparedRun) else self.begin(work)
        run_task = prepared.task

        if run_task.resume is None:
            prior = self.registry.get(run_task.role, run_task.issue_id, prepared.agent_id)
            if prior:
                run_task = replace(run_task, resume=prior)

        # Prepend compiled history from prior included turns (client-owned context, D5).
        history = _compile_history(self.state_db_path, prepared.thread_id, prepared.run_id)
        ctx = prepared.ctx
        if history:
            ctx = replace(ctx, system_prompt=history + "\n\n" + ctx.system_prompt if ctx.system_prompt else history)
            prepared = replace(prepared, ctx=ctx)

        runner = self.runners[prepared.tool]
        lock = self._locks.setdefault(prepared.agent_id, asyncio.Lock())
        usage = None

        async with lock:
            try:
                async for event in runner.run(run_task, prepared.ctx):
                    if event.kind == "result" and event.raw and event.raw.get("session_id"):
                        self.registry.set(
                            run_task.role,
                            run_task.issue_id,
                            event.raw["session_id"],
                            prepared.agent_id,
                        )
                    if event.kind == "result" and event.raw:
                        usage = event.raw.get("usage")

                    append_turn(
                        self.state_db_path,
                        prepared.thread_id,
                        run_id=prepared.run_id,
                        role="tool" if event.kind in ("tool", "tool_call") else "assistant",
                        kind=event.kind,
                        text=event.text,
                    )
                    if event.kind == "tool_call" and event.raw:
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
                append_turn(
                    self.state_db_path,
                    prepared.thread_id,
                    run_id=prepared.run_id,
                    role="assistant",
                    kind="error",
                    text=str(exc),
                )
                finish_run(self.state_db_path, prepared.run_id, status="error")
                raise
            else:
                finish_run(self.state_db_path, prepared.run_id, status="done", usage=usage)

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
            working_dir=str(task.cwd) if task.cwd else None,
        )

    def _contract(self, profile: Profile, task: AgentTask, tool: Tool) -> dict:
        return {
            "agent_id": profile.agent_id,
            "role": profile.role,
            "tool": tool.value,
            "issue_id": task.issue_id,
            "model": task.model or profile.model,
            "effort": profile.effort,
            "cwd": str(task.cwd) if task.cwd else profile.working_dir,
        }


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
