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

from hephaestus.integration.context import SessionContext
from hephaestus.integration.routing import Role, Tool

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
    kind: str            # "system" | "text" | "tool" | "result" | "error"
    text: str
    raw: dict | None = None


@runtime_checkable
class AgentRunner(Protocol):
    tool: Tool

    def run(self, task: AgentTask, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        ...


# --------------------------------------------------------------------------- #
# Echo (offline)
# --------------------------------------------------------------------------- #

class EchoRunner:
    """Deterministic runner that reports what *would* be sent. No external calls."""

    def __init__(self, tool: Tool = Tool.CLAUDE):
        self.tool = tool

    async def run(self, task: AgentTask, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        yield AgentEvent("system", f"[echo:{self.tool.value}] role={task.role.value} issue={task.issue_id}")
        if task.model or task.effort:
            yield AgentEvent("system", f"model={task.model} effort={task.effort}")
        if task.resume:
            yield AgentEvent("system", f"resume={task.resume}")
        yield AgentEvent("system", f"context files: {[p.name for p in ctx.files]}")
        if ctx.missing:
            yield AgentEvent("system", f"missing: {[p.name for p in ctx.missing]}")
        yield AgentEvent("text", task.prompt)
        yield AgentEvent("result", "ok")


# --------------------------------------------------------------------------- #
# Claude (claude-agent-sdk)
# --------------------------------------------------------------------------- #

def _claude_options(ctx: SessionContext, task: AgentTask):
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
    if "cwd" in fields and task.cwd:
        kwargs["cwd"] = str(task.cwd)
    if "model" in fields and task.model:
        kwargs["model"] = task.model
    if "effort" in fields and task.effort:
        kwargs["effort"] = task.effort
    if "resume" in fields and task.resume:
        kwargs["resume"] = task.resume
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

    async def run(self, task: AgentTask, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        if not HAS_CLAUDE_SDK:
            raise RuntimeError("claude-agent-sdk not installed; run: pip install -e .[agents]")
        options = _claude_options(ctx, task)
        async for msg in claude_sdk.query(prompt=task.prompt, options=options):
            result = _claude_event(msg)
            if isinstance(result, list):
                for ev in result:
                    yield ev
            else:
                yield result


# --------------------------------------------------------------------------- #
# Codex (`codex exec`)
# --------------------------------------------------------------------------- #

def build_codex_argv(task: AgentTask, *, output_file: str | None = None, jsonl: bool = True) -> list[str]:
    """Pure: the `codex` args (without the executable prefix). Easy to unit-test."""
    argv = ["exec", "--skip-git-repo-check"]
    if jsonl:
        argv.append("--json")
    if output_file:
        argv += ["-o", output_file]
    if task.cwd:
        argv += ["-C", str(task.cwd)]
    if task.model:
        argv += ["-m", task.model]
    if task.effort:
        # `codex exec -c key=value` overrides config.toml; value is parsed as TOML.
        argv += ["-c", f'model_reasoning_effort="{task.effort}"']
    argv.append(task.prompt)
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


def _codex_event(raw: dict) -> AgentEvent:
    """Map a `codex exec --json` JSONL event to an AgentEvent.

    Observed schema (codex-cli 0.130.0):
      {"type":"thread.started","thread_id":...}
      {"type":"turn.started"}
      {"type":"item.completed","item":{"type":"agent_message","text":"..."}}
      {"type":"item.completed","item":{"type":"function_call","name":"shell","arguments":{...}}}
      {"type":"turn.completed","usage":{...}}
    """
    raw_kind = raw.get("type") or raw.get("kind") or "event"
    item = raw.get("item") if isinstance(raw.get("item"), dict) else None
    msg = raw.get("msg") if isinstance(raw.get("msg"), dict) else None

    # function_call items → tool_call events
    if item and item.get("type") == "function_call":
        name = item.get("name", "")
        arguments = item.get("arguments") or {}
        return AgentEvent(
            kind="tool_call",
            text=name,
            raw={"action": name, "input": arguments},
        )

    # reasoning items → thinking events (agent reasoning; never drop it)
    if item and item.get("type") in ("reasoning", "agent_reasoning"):
        th = item.get("text") or item.get("summary") or item.get("content") or ""
        return AgentEvent(kind="thinking", text=str(th), raw=raw)

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


class CodexRunner:
    tool = Tool.CODEX

    async def run(self, task: AgentTask, ctx: SessionContext) -> AsyncIterator[AgentEvent]:
        cmd = _codex_command() + build_codex_argv(task)
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
        async for line in proc.stdout:
            text = line.decode("utf-8", "replace").strip()
            if not text:
                continue
            try:
                raw = json.loads(text)
            except json.JSONDecodeError:
                yield AgentEvent("text", text)
                continue
            yield _codex_event(raw)

        await proc.wait()
        if proc.returncode:
            err = ""
            if proc.stderr is not None:
                err = (await proc.stderr.read()).decode("utf-8", "replace").strip()
            yield AgentEvent("error", err or f"codex exited with code {proc.returncode}")
