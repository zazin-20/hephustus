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
from typing import AsyncIterator, Protocol, runtime_checkable

from hephaestus.contract import ExecutionContract
from hephaestus.integration.adapters import claude_flags, codex_flags
from hephaestus.integration.context import SessionContext
from hephaestus.integration.routing import Role, Tool
from hephaestus.integration.turns import turn_payload

try:
    import claude_agent_sdk as claude_sdk

    HAS_CLAUDE_SDK = True
except ImportError:  # pragma: no cover
    claude_sdk = None  # type: ignore[assignment]
    HAS_CLAUDE_SDK = False


@dataclass(frozen=True)
class AgentTask:
    role: Role
    prompt: str
    issue_id: str | None = None
    agent_id: str | None = None
    cwd: Path | None = None
    model: str | None = None
    effort: str | None = None    # reasoning effort (low|medium|high|xhigh|max)
    resume: str | None = None    # prior session id to resume (spec §5.1)


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
    tool: Tool

    def run(self, contract: ExecutionContract, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        ...


# --------------------------------------------------------------------------- #
# Echo (offline)
# --------------------------------------------------------------------------- #

class EchoRunner:
    """Deterministic runner that reports what *would* be sent. No external calls."""

    def __init__(self, tool: Tool = Tool.CLAUDE):
        self.tool = tool

    async def run(self, contract: ExecutionContract, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        yield AgentEvent("system", f"[echo:{self.tool.value}] role={contract.role} issue={contract.issue_id}")
        if contract.model or contract.effort:
            yield AgentEvent("system", f"model={contract.model} effort={contract.effort}")
        if contract.resume:
            yield AgentEvent("system", f"resume={contract.resume}")
        yield AgentEvent("system", f"context files: {[p.name for p in ctx.files]}")
        if ctx.missing:
            yield AgentEvent("system", f"missing: {[p.name for p in ctx.missing]}")
        yield AgentEvent("text", contract.prompt)
        yield AgentEvent("result", "ok", raw={"actual_model": contract.model})


# --------------------------------------------------------------------------- #
# Claude (claude-agent-sdk)
# --------------------------------------------------------------------------- #

def _claude_options(ctx: SessionContext, contract: ExecutionContract):
    """Build ClaudeAgentOptions, passing only fields the installed SDK supports.

    The OKF directive/context is injected via `system_prompt` using the
    preset+append form, which keeps Claude Code's default behavior and appends our
    context (the old `append_system_prompt` field was removed from the SDK).
    """
    fields = set(getattr(claude_sdk.ClaudeAgentOptions, "__dataclass_fields__", {}))
    kwargs: dict = {}
    if "system_prompt" in fields and ctx.system_prompt:
        kwargs["system_prompt"] = {
            "type": "preset",
            "preset": "claude_code",
            "append": ctx.system_prompt,
        }
    if "setting_sources" in fields:
        kwargs["setting_sources"] = ["project"]
    adapter_flags = claude_flags(contract)
    for field_name, value in (
        ("cwd", adapter_flags.get("cwd")),
        ("permission_mode", adapter_flags.get("permission_mode")),
        ("allowed_tools", adapter_flags.get("allowed_tools")),
        ("disallowed_tools", adapter_flags.get("disallowed_tools")),
        ("model", contract.model),
        ("effort", contract.effort),
        ("resume", contract.resume),
    ):
        if field_name in fields and value not in (None, [], ""):
            kwargs[field_name] = value
    return claude_sdk.ClaudeAgentOptions(**kwargs)


def _claude_event(msg) -> AgentEvent | list[AgentEvent]:
    """Map a claude-agent-sdk message to one or more AgentEvents.

    AssistantMessage content may contain both text blocks and ToolUseBlocks;
    we emit a separate tool_call event for each tool use so the trace layer
    can record it independently.
    """
    name = type(msg).__name__
    text_parts = []
    thinking_parts = []
    tool_events: list[AgentEvent] = []

    content = getattr(msg, "content", None)
    if isinstance(content, list):
        for block in content:
            block_type = getattr(block, "type", None) or type(block).__name__
            # ToolUseBlock
            if block_type in ("tool_use", "ToolUseBlock") or hasattr(block, "input"):
                tool_name = getattr(block, "name", "") or ""
                tool_input = getattr(block, "input", {}) or {}
                if isinstance(tool_input, dict):
                    tool_events.append(AgentEvent(
                        kind="tool_call",
                        text=tool_name,
                        raw={"action": tool_name, "input": tool_input},
                    ))
            # ThinkingBlock — agent reasoning. Capture it; never drop it.
            elif block_type in ("thinking", "ThinkingBlock") or hasattr(block, "thinking"):
                th = getattr(block, "thinking", None)
                if th:
                    thinking_parts.append(th)
            else:
                t = getattr(block, "text", None)
                if t:
                    text_parts.append(t)
    elif isinstance(content, str):
        text_parts.append(content)

    # Emit thinking first, then text, then tool calls — preserving everything.
    events: list[AgentEvent] = []
    if thinking_parts:
        events.append(AgentEvent(kind="thinking", text="".join(thinking_parts)))
    if text_parts:
        events.append(AgentEvent(kind="text", text="".join(text_parts)))
    events.extend(tool_events)
    if events:
        return events if len(events) > 1 else events[0]

    # No content blocks: a lifecycle envelope (system init / result). Carry
    # session_id + usage in raw, but NOT msg.result as text — the spoken reply
    # already arrived via AssistantMessage events, so echoing it here duplicated
    # the whole response as a stray "result" turn.
    kind = {"AssistantMessage": "text", "ResultMessage": "result"}.get(name, "system")
    raw = {}
    sid = getattr(msg, "session_id", None)
    if sid:
        raw["session_id"] = sid
    usage = getattr(msg, "usage", None)
    if usage is not None:
        raw["usage"] = usage
    return AgentEvent(kind=kind, text="", raw=raw or None)


class ClaudeRunner:
    tool = Tool.CLAUDE

    async def run(self, contract: ExecutionContract, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        if not HAS_CLAUDE_SDK:
            raise RuntimeError("claude-agent-sdk not installed; run: pip install -e .[agents]")
        options = _claude_options(ctx, contract)
        async for msg in claude_sdk.query(prompt=contract.prompt, options=options):
            result = _claude_event(msg)
            if isinstance(result, list):
                for ev in result:
                    yield ev
            else:
                yield result


# --------------------------------------------------------------------------- #
# Codex (`codex exec`)
# --------------------------------------------------------------------------- #

def build_codex_argv(contract: ExecutionContract, *, output_file: str | None = None, jsonl: bool = True) -> list[str]:
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
        # `codex exec -c key=value` overrides config.toml; value is parsed as TOML.
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
        val = input_dict.get(key)
        if val is not None:
            return str(val)
    return None


def _codex_args(arguments) -> dict:
    """Normalize a codex item's arguments (dict, JSON string, or None) to a dict."""
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            value = json.loads(arguments)
        except json.JSONDecodeError:
            return {"arguments": arguments}
        return value if isinstance(value, dict) else {"arguments": value}
    return {}


def _codex_event(raw: dict) -> AgentEvent:
    """Map a `codex exec --json` JSONL event to an AgentEvent.

    Observed schema (codex-cli 0.130.0) — tool calls arrive as items, reported on
    both `item.started` and `item.completed`; we act on completion so each is
    emitted once:
      {"type":"thread.started",...} / {"type":"turn.started"}
      {"type":"item.completed","item":{"type":"agent_message","text":"..."}}
      {"type":"item.completed","item":{"type":"command_execution","command":"...","exit_code":0}}
      {"type":"item.completed","item":{"type":"function_call","name":"...","arguments":"{...}"}}
      {"type":"turn.completed","usage":{...}}
    """
    raw_kind = raw.get("type") or raw.get("kind") or "event"
    item = raw.get("item") if isinstance(raw.get("item"), dict) else None
    msg = raw.get("msg") if isinstance(raw.get("msg"), dict) else None

    # Tool calls + reasoning are reported as items; act on completion (item.started
    # carries the same item and would double-emit otherwise).
    if item is not None and raw_kind == "item.completed":
        itype = item.get("type")
        if itype == "command_execution":
            return AgentEvent(
                "tool_call",
                "shell",
                raw={
                    "action": "shell",
                    "input": {"command": item.get("command", "")},
                    "output": item.get("aggregated_output") or item.get("output") or "",
                    "exit_code": item.get("exit_code"),
                },
            )
        if itype == "function_call":
            name = item.get("name", "") or "function"
            return AgentEvent("tool_call", name, raw={"action": name, "input": _codex_args(item.get("arguments"))})
        if itype in ("mcp_tool_call", "tool_call"):
            name = str(item.get("name") or item.get("tool") or "tool")
            args = _codex_args(item.get("arguments") if item.get("arguments") is not None else item.get("input"))
            return AgentEvent("tool_call", name, raw={"action": name, "input": args})
        if itype in ("file_change", "patch_apply", "apply_patch"):
            return AgentEvent("tool_call", itype, raw={"action": itype, "input": {"path": item.get("path", "")}})
        if itype in ("reasoning", "agent_reasoning"):
            th = item.get("text") or item.get("summary") or item.get("content") or ""
            return AgentEvent("thinking", str(th), raw=raw)
        # agent_message and anything else fall through to the text path below.

    text = raw.get("text") or raw.get("message") or raw.get("delta") or ""
    if not text and item:
        text = item.get("text") or item.get("message") or ""
    if not text and msg:
        text = msg.get("text") or msg.get("message") or ""

    kind = raw_kind
    if item and item.get("type") == "agent_message":
        kind = "text"
    elif raw_kind == "turn.completed":
        kind = "result"

    return AgentEvent(kind=str(kind), text=str(text), raw=raw)


def _decode_codex_line(raw_line: bytes) -> AgentEvent | None:
    """Parse one codex JSONL line into an event (None for blank lines)."""
    text = raw_line.decode("utf-8", "replace").strip()
    if not text:
        return None
    try:
        return _codex_event(json.loads(text))
    except json.JSONDecodeError:
        return AgentEvent("text", text)


class CodexRunner:
    tool = Tool.CODEX

    async def run(self, contract: ExecutionContract, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        cmd = _codex_command() + build_codex_argv(contract)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Inject the OKF context as a piped <stdin> block (appended by codex exec).
        if proc.stdin is not None:
            if ctx.system_prompt:
                proc.stdin.write(ctx.system_prompt.encode("utf-8"))
            proc.stdin.close()

        assert proc.stdout is not None
        # Read raw chunks and split on newlines ourselves. `async for line in
        # proc.stdout` uses readline(), which caps a single line at asyncio's 64 KB
        # StreamReader limit and raises LimitOverrunError ("Separator is not found,
        # and chunk exceed the limit") when codex emits a long JSONL line. read()
        # has no such cap.
        buffer = b""
        while True:
            chunk = await proc.stdout.read(65536)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                raw_line, buffer = buffer.split(b"\n", 1)
                event = _decode_codex_line(raw_line)
                if event is not None:
                    if event.kind == "result":
                        raw = dict(event.raw or {})
                        raw.setdefault("actual_model", contract.model)
                        event = AgentEvent(event.kind, event.text, raw=raw)
                    yield event
        event = _decode_codex_line(buffer)
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
