"""Agent runner backends (spec/architecture.md §5.1, §5.2).

Three runners behind one interface:
  - ClaudeRunner — claude-agent-sdk (guarded import)
  - CodexRunner  — `codex exec` subprocess, streaming JSONL events
  - EchoRunner   — deterministic, offline; used by tests and `--echo`

Runner I/O is intentionally thin. The context assembly and routing that decide
*what* to run live in routing.py / context.py and are unit-tested there.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Protocol, runtime_checkable

from hephaestus.contract import ExecutionContract
from hephaestus.integration.adapters import codex_flags
from hephaestus.integration.context import SessionContext
from hephaestus.integration.routing import Role, Tool
from hephaestus.integration.turns import turn_payload

try:
    import claude_agent_sdk as claude_sdk

    HAS_CLAUDE_SDK = True
except ImportError:  # pragma: no cover
    claude_sdk = None  # type: ignore[assignment]
    HAS_CLAUDE_SDK = False


ProviderEvent = "AgentEvent | list[AgentEvent]"


@dataclass(frozen=True)
class AgentTask:
    role: Role
    prompt: str
    issue_id: str | None = None
    agent_id: str | None = None
    cwd: Path | None = None
    model: str | None = None
    effort: str | None = None
    resume: str | None = None


@dataclass(frozen=True)
class AgentEvent:
    kind: str
    text: str
    raw: dict | None = None
    category: str | None = None
    persist: bool | None = None
    transcript_role: str | None = None
    label: str | None = None
    conversation: bool | None = None

    def __post_init__(self) -> None:
        payload = turn_payload(self.kind, text=self.text)
        if self.category is None:
            object.__setattr__(self, "category", payload["category"])
        if self.persist is None:
            object.__setattr__(self, "persist", payload["persist"])
        if self.transcript_role is None:
            object.__setattr__(self, "transcript_role", payload["transcript_role"])
        if self.label is None:
            object.__setattr__(self, "label", payload["label"])
        if self.conversation is None:
            object.__setattr__(self, "conversation", payload["conversation"])


@runtime_checkable
class AgentRunner(Protocol):
    tool: Tool | str

    def run(self, contract: ExecutionContract, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        ...


class EchoRunner:
    """Deterministic runner that reports what *would* be sent. No external calls."""

    def __init__(self, tool: Tool | str = Tool.CLAUDE):
        self.tool = tool

    async def run(self, contract: ExecutionContract, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        tool = getattr(self.tool, "value", self.tool)
        yield AgentEvent("system", f"[echo:{tool}] role={contract.role} issue={contract.issue_id}")
        if contract.model or contract.effort:
            yield AgentEvent("system", f"model={contract.model} effort={contract.effort}")
        if contract.resume:
            yield AgentEvent("system", f"resume={contract.resume}")
        yield AgentEvent("system", f"context files: {[p.name for p in ctx.files]}")
        if ctx.missing:
            yield AgentEvent("system", f"missing: {[p.name for p in ctx.missing]}")
        yield AgentEvent("text", contract.prompt)
        yield AgentEvent("result", "ok", raw={"actual_model": contract.model})


def _build_claude_options(
    ctx: SessionContext,
    contract: ExecutionContract,
    flag_resolver: Callable[[ExecutionContract], dict],
):
    """Build ClaudeAgentOptions, passing only fields the installed SDK supports."""
    fields = set(getattr(claude_sdk.ClaudeAgentOptions, "__dataclass_fields__", {}))
    kwargs: dict[str, Any] = {}
    if "system_prompt" in fields and ctx.system_prompt:
        kwargs["system_prompt"] = {
            "type": "preset",
            "preset": "claude_code",
            "append": ctx.system_prompt,
        }
    if "setting_sources" in fields:
        kwargs["setting_sources"] = ["project"]
    flags = flag_resolver(contract)
    for field_name, value in (
        ("cwd", flags.get("cwd")),
        ("permission_mode", flags.get("permission_mode")),
        ("allowed_tools", flags.get("allowed_tools")),
        ("disallowed_tools", flags.get("disallowed_tools")),
        ("model", contract.model),
        ("effort", contract.effort),
        ("resume", contract.resume),
    ):
        if field_name in fields and value not in (None, [], ""):
            kwargs[field_name] = value
    return claude_sdk.ClaudeAgentOptions(**kwargs)


class ClaudeRunner:
    tool = Tool.CLAUDE

    def __init__(
        self,
        *,
        normalize_event: Callable[[Any], ProviderEvent] | None = None,
        flag_resolver: Callable[[ExecutionContract], dict] | None = None,
    ) -> None:
        if normalize_event is None or flag_resolver is None:
            from hephaestus.integration.providers import _claude_flags, _claude_normalize_event

            normalize_event = normalize_event or _claude_normalize_event
            flag_resolver = flag_resolver or _claude_flags
        self._normalize_event = normalize_event
        self._flag_resolver = flag_resolver

    def build_options(self, ctx: SessionContext, contract: ExecutionContract):
        return _build_claude_options(ctx, contract, self._flag_resolver)

    async def run(self, contract: ExecutionContract, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        if not HAS_CLAUDE_SDK:
            raise RuntimeError("claude-agent-sdk not installed; run: pip install -e .[agents]")
        options = self.build_options(ctx, contract)
        async for msg in claude_sdk.query(prompt=contract.prompt, options=options):
            result = self._normalize_event(msg)
            if isinstance(result, list):
                for event in result:
                    yield event
            else:
                yield result


def build_codex_argv(
    contract: ExecutionContract,
    *,
    output_file: str | None = None,
    jsonl: bool = True,
) -> list[str]:
    """Pure: the `codex` args (without the executable prefix). Easy to unit-test."""
    flags = codex_flags(contract)
    argv = ["exec", "--skip-git-repo-check"]
    if jsonl:
        argv.append("--json")
    if output_file:
        argv += ["-o", output_file]
    if flags.get("working_dir"):
        argv += ["-C", str(flags["working_dir"])]
    if contract.model:
        argv += ["-m", contract.model]
    if contract.effort:
        argv += ["-c", f'model_reasoning_effort="{contract.effort}"']
    argv += ["-c", f'sandbox_mode="{"workspace-write" if flags.get("sandbox", True) else "danger-full-access"}"']
    argv += ["-c", f'approval_policy="{flags.get("approval_policy", "auto")}"']
    argv.append(contract.prompt)
    return argv


def _codex_command() -> list[str]:
    exe = shutil.which("codex")
    if exe is None:
        raise RuntimeError("codex CLI not found on PATH")
    low = exe.lower()
    if sys.platform == "win32" and low.endswith((".cmd", ".bat")):
        return ["cmd", "/c", "codex"]
    if sys.platform == "win32" and low.endswith(".ps1"):
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", exe]
    return [exe]


def _extract_target_path(input_dict: dict) -> str | None:
    """Derive a human-readable target path from a tool input dict."""
    for key in ("file_path", "path", "cmd", "command"):
        value = input_dict.get(key)
        if value is not None:
            return str(value)
    return None


def _decode_jsonl_line(
    raw_line: bytes,
    normalize_event: Callable[[dict], AgentEvent],
) -> AgentEvent | None:
    """Parse one JSONL line into an event (None for blank lines)."""
    text = raw_line.decode("utf-8", "replace").strip()
    if not text:
        return None
    try:
        return normalize_event(json.loads(text))
    except json.JSONDecodeError:
        return AgentEvent("text", text)


class CodexRunner:
    tool = Tool.CODEX

    def __init__(
        self,
        *,
        normalize_event: Callable[[dict], AgentEvent] | None = None,
        flag_resolver: Callable[[ExecutionContract], dict] | None = None,
    ) -> None:
        if normalize_event is None or flag_resolver is None:
            from hephaestus.integration.providers import _codex_flags, _codex_normalize_event

            normalize_event = normalize_event or _codex_normalize_event
            flag_resolver = flag_resolver or _codex_flags
        self._normalize_event = normalize_event
        self._flag_resolver = flag_resolver

    def decode_event_line(self, raw_line: bytes) -> AgentEvent | None:
        return _decode_jsonl_line(raw_line, self._normalize_event)

    def build_argv(
        self,
        contract: ExecutionContract,
        *,
        output_file: str | None = None,
        jsonl: bool = True,
    ) -> list[str]:
        flags = self._flag_resolver(contract)
        argv = ["exec", "--skip-git-repo-check"]
        if jsonl:
            argv.append("--json")
        if output_file:
            argv += ["-o", output_file]
        if flags.get("working_dir"):
            argv += ["-C", str(flags["working_dir"])]
        if contract.model:
            argv += ["-m", contract.model]
        if contract.effort:
            argv += ["-c", f'model_reasoning_effort="{contract.effort}"']
        argv += ["-c", f'sandbox_mode="{"workspace-write" if flags.get("sandbox", True) else "danger-full-access"}"']
        argv += ["-c", f'approval_policy="{flags.get("approval_policy", "auto")}"']
        argv.append(contract.prompt)
        return argv

    async def run(self, contract: ExecutionContract, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        cmd = _codex_command() + self.build_argv(contract)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        if proc.stdin is not None:
            if ctx.system_prompt:
                proc.stdin.write(ctx.system_prompt.encode("utf-8"))
            proc.stdin.close()

        assert proc.stdout is not None
        buffer = b""
        while True:
            chunk = await proc.stdout.read(65536)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                raw_line, buffer = buffer.split(b"\n", 1)
                event = self.decode_event_line(raw_line)
                if event is not None:
                    if event.kind == "result":
                        raw = dict(event.raw or {})
                        raw.setdefault("actual_model", contract.model)
                        event = AgentEvent(event.kind, event.text, raw=raw)
                    yield event
        event = self.decode_event_line(buffer)
        if event is not None:
            if event.kind == "result":
                raw = dict(event.raw or {})
                raw.setdefault("actual_model", contract.model)
                event = AgentEvent(event.kind, event.text, raw=raw)
            yield event

        await proc.wait()
        if proc.returncode:
            err = ""
            if proc.stderr is not None:
                err = (await proc.stderr.read()).decode("utf-8", "replace").strip()
            yield AgentEvent("error", err or f"codex exited with code {proc.returncode}")
