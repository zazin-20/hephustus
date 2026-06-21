"""Agent service: route a task to the right runner + track sessions.

Hephaestus is not the orchestrator (spec/architecture.md §1) — this is the
integration *plumbing* the Orchestrator (or a human, or the desktop UI) uses to
run a role-appropriate session with the correct OKF context injected.
"""
from __future__ import annotations

from dataclasses import replace
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


class SessionRegistry:
    """Sessions tagged by role + issue id for resumability (spec §5.1)."""

    def __init__(self):
        self._sessions: dict[str, str] = {}

    @staticmethod
    def key(role: Role | str, issue_id: str | None) -> str:
        r = role.value if isinstance(role, Role) else str(role)
        return f"{r}:{issue_id}" if issue_id else r

    def get(self, role: Role | str, issue_id: str | None = None) -> str | None:
        return self._sessions.get(self.key(role, issue_id))

    def set(self, role: Role | str, issue_id: str | None, session_id: str) -> None:
        self._sessions[self.key(role, issue_id)] = session_id

    def all(self) -> dict[str, str]:
        return dict(self._sessions)


def default_runners() -> dict[Tool, AgentRunner]:
    return {Tool.CLAUDE: ClaudeRunner(), Tool.CODEX: CodexRunner()}


class AgentService:
    def __init__(self, root: str | Path, runners: dict[Tool, AgentRunner] | None = None):
        self.root = Path(root)
        self.runners = runners or default_runners()
        self.registry = SessionRegistry()

    def resolve(self, task: AgentTask) -> tuple[Tool, SessionContext]:
        tool = tool_for(task.role)
        ctx = build_session_context(self.root, task.role, task.issue_id)
        return tool, ctx

    async def run(self, task: AgentTask) -> AsyncIterator[AgentEvent]:
        tool, ctx = self.resolve(task)

        # Resume a prior session for this role:issue if one is known (spec §5.1).
        if task.resume is None:
            prior = self.registry.get(task.role, task.issue_id)
            if prior:
                task = replace(task, resume=prior)

        runner = self.runners[tool]
        async for event in runner.run(task, ctx):
            # Capture the session id from the result so the next call can resume.
            if event.kind == "result" and event.raw and event.raw.get("session_id"):
                self.registry.set(task.role, task.issue_id, event.raw["session_id"])
            yield event


def main(argv: list[str] | None = None) -> int:
    import argparse
    import asyncio

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
