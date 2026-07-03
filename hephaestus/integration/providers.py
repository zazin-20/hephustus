"""Provider registry for pluggable agent backends."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable

from hephaestus.contract import ExecutionContract
from hephaestus.integration.routing import Role

if TYPE_CHECKING:
    from hephaestus.integration.runners import AgentEvent, AgentRunner


ProviderEvent = "AgentEvent | list[AgentEvent]"

_CLAUDE = "claude"
_CODEX = "codex"

_CODEX_CACHE = Path.home() / ".codex" / "models_cache.json"
_CLAUDE_ALIASES = [
    ("opus", "Opus (latest)"),
    ("sonnet", "Sonnet (latest)"),
    ("haiku", "Haiku (latest)"),
    ("fable", "Fable (latest)"),
]
_CLAUDE_ALIAS_IDS = {alias for alias, _ in _CLAUDE_ALIASES}
_CLAUDE_EFFORT_FALLBACK = ["low", "medium", "high", "xhigh", "max"]
_CODEX_MODEL_FALLBACK = [
    {"id": "gpt-5.4", "label": "GPT-5.4", "efforts": ["low", "medium", "high", "xhigh"]},
]

_EFFORT_PERMISSION = {
    "low": "default",
    "medium": "default",
    "high": "bypassPermissions",
}
_EFFORT_SANDBOX = {
    "low": True,
    "medium": True,
    "high": False,
}
_EFFORT_APPROVAL = {
    "low": "auto",
    "medium": "auto",
    "high": "manual",
}


@dataclass
class Provider:
    key: str
    runner: "AgentRunner"
    normalize_event: Callable[[Any], ProviderEvent]
    flags: Callable[[ExecutionContract], dict]
    discover_models: Callable[[], dict]
    owns_model: Callable[[str | None], bool]
    default_roles: set[Role] = field(default_factory=set)


class ProviderRegistry:
    def __init__(self, providers: Iterable[Provider] = ()) -> None:
        self._providers: dict[str, Provider] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: Provider) -> Provider:
        self._providers[provider.key] = provider
        return provider

    def get(self, key: object) -> Provider:
        return self._providers[provider_key(key)]

    def keys(self) -> set[str]:
        return set(self._providers)

    def providers(self) -> list[Provider]:
        return list(self._providers.values())

    def catalog(self) -> dict:
        return {"providers": [provider.discover_models() for provider in self.providers()]}

    def runners(self) -> dict[str, "AgentRunner"]:
        return {provider.key: provider.runner for provider in self.providers()}

    def provider_for_model(self, model: str | None) -> str | None:
        if not model:
            return None
        for provider in self.providers():
            if provider.owns_model(model):
                return provider.key
        return None

    def provider_for_role(self, role: Role | str) -> str:
        wanted = Role(role)
        for provider in reversed(self.providers()):
            if wanted in provider.default_roles:
                return provider.key
        raise KeyError(wanted.value)


def provider_key(value: object) -> str:
    if isinstance(value, str):
        return value
    raw = getattr(value, "value", None)
    if isinstance(raw, str):
        return raw
    raise KeyError(value)


def _scope_to_cwd(scope: str) -> str:
    return "."


def _claude_flags(contract: ExecutionContract) -> dict:
    flags: dict = {
        "permission_mode": _EFFORT_PERMISSION.get(contract.effort, "default"),
        "cwd": contract.cwd or _scope_to_cwd(contract.scope),
    }
    if contract.tools:
        flags["allowed_tools"] = list(contract.tools)
    if contract.disallowed_tools:
        flags["disallowed_tools"] = list(contract.disallowed_tools)
    return flags


def _codex_flags(contract: ExecutionContract) -> dict:
    return {
        "sandbox": _EFFORT_SANDBOX.get(contract.effort, True),
        "approval_policy": _EFFORT_APPROVAL.get(contract.effort, "auto"),
        "working_dir": contract.cwd or _scope_to_cwd(contract.scope),
    }


def _claude_efforts() -> list[str]:
    claude = shutil.which("claude")
    if claude:
        try:
            out = subprocess.run(
                [claude, "--help"], capture_output=True, text=True, timeout=10
            ).stdout
            match = re.search(r"--effort\s+<level>.*?\(([^)]*)\)", out, re.S)
            if match:
                levels = [x.strip() for x in match.group(1).split(",") if x.strip()]
                if levels:
                    return levels
        except Exception:
            pass
    return list(_CLAUDE_EFFORT_FALLBACK)


def _discover_claude() -> dict:
    efforts = _claude_efforts()
    models = [
        {"id": alias, "label": label, "efforts": list(efforts)}
        for alias, label in _CLAUDE_ALIASES
    ]
    return {"provider": _CLAUDE, "models": models}


def _discover_codex() -> dict:
    try:
        data = json.loads(_CODEX_CACHE.read_text(encoding="utf-8"))
        models = []
        for model in data.get("models", []):
            if model.get("visibility") != "list" or not model.get("supported_in_api"):
                continue
            efforts = [
                level["effort"]
                for level in model.get("supported_reasoning_levels", [])
                if level.get("effort")
            ]
            models.append(
                {
                    "id": model["slug"],
                    "label": model.get("display_name") or model["slug"],
                    "efforts": efforts,
                }
            )
        if models:
            return {"provider": _CODEX, "models": models}
    except Exception:
        pass
    return {"provider": _CODEX, "models": list(_CODEX_MODEL_FALLBACK)}


def _claude_owns_model(model: str | None) -> bool:
    return bool(model and (model in _CLAUDE_ALIAS_IDS or model.startswith("claude")))


def _codex_owns_model(model: str | None) -> bool:
    if not model:
        return False
    try:
        data = json.loads(_CODEX_CACHE.read_text(encoding="utf-8"))
        if any(entry.get("slug") == model for entry in data.get("models", [])):
            return True
    except Exception:
        pass
    return model.startswith(("gpt", "o1", "o3", "o4", "codex"))


def _claude_normalize_event(msg) -> ProviderEvent:
    from hephaestus.integration.runners import AgentEvent

    name = type(msg).__name__
    text_parts = []
    thinking_parts = []
    tool_events: list[AgentEvent] = []

    content = getattr(msg, "content", None)
    if isinstance(content, list):
        for block in content:
            block_type = getattr(block, "type", None) or type(block).__name__
            if block_type in ("tool_use", "ToolUseBlock") or hasattr(block, "input"):
                tool_name = getattr(block, "name", "") or ""
                tool_input = getattr(block, "input", {}) or {}
                if isinstance(tool_input, dict):
                    tool_events.append(
                        AgentEvent(
                            kind="tool_call",
                            text=tool_name,
                            raw={"action": tool_name, "input": tool_input},
                        )
                    )
            elif block_type in ("thinking", "ThinkingBlock") or hasattr(block, "thinking"):
                thinking = getattr(block, "thinking", None)
                if thinking:
                    thinking_parts.append(thinking)
            else:
                text = getattr(block, "text", None)
                if text:
                    text_parts.append(text)
    elif isinstance(content, str):
        text_parts.append(content)

    events: list[AgentEvent] = []
    if thinking_parts:
        events.append(AgentEvent(kind="thinking", text="".join(thinking_parts)))
    if text_parts:
        events.append(AgentEvent(kind="text", text="".join(text_parts)))
    events.extend(tool_events)
    if events:
        return events if len(events) > 1 else events[0]

    kind = {"AssistantMessage": "text", "ResultMessage": "result"}.get(name, "system")
    raw = {}
    session_id = getattr(msg, "session_id", None)
    if session_id:
        raw["session_id"] = session_id
    usage = getattr(msg, "usage", None)
    if usage is not None:
        raw["usage"] = usage
    return AgentEvent(kind=kind, text="", raw=raw or None)


def _codex_args(arguments) -> dict:
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            value = json.loads(arguments)
        except json.JSONDecodeError:
            return {"arguments": arguments}
        return value if isinstance(value, dict) else {"arguments": value}
    return {}


def _codex_normalize_event(raw: dict):
    from hephaestus.integration.runners import AgentEvent

    raw_kind = raw.get("type") or raw.get("kind") or "event"
    item = raw.get("item") if isinstance(raw.get("item"), dict) else None
    msg = raw.get("msg") if isinstance(raw.get("msg"), dict) else None

    if item is not None and raw_kind == "item.completed":
        item_type = item.get("type")
        if item_type == "command_execution":
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
        if item_type == "function_call":
            name = item.get("name", "") or "function"
            return AgentEvent("tool_call", name, raw={"action": name, "input": _codex_args(item.get("arguments"))})
        if item_type in ("mcp_tool_call", "tool_call"):
            name = str(item.get("name") or item.get("tool") or "tool")
            args = _codex_args(item.get("arguments") if item.get("arguments") is not None else item.get("input"))
            return AgentEvent("tool_call", name, raw={"action": name, "input": args})
        if item_type in ("file_change", "patch_apply", "apply_patch"):
            return AgentEvent("tool_call", item_type, raw={"action": item_type, "input": {"path": item.get("path", "")}})
        if item_type in ("reasoning", "agent_reasoning"):
            thinking = item.get("text") or item.get("summary") or item.get("content") or ""
            return AgentEvent("thinking", str(thinking), raw=raw)

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


def build_provider_registry() -> ProviderRegistry:
    from hephaestus.integration.runners import ClaudeRunner, CodexRunner

    return ProviderRegistry(
        [
            Provider(
                key=_CLAUDE,
                runner=ClaudeRunner(
                    normalize_event=_claude_normalize_event,
                    flag_resolver=_claude_flags,
                ),
                normalize_event=_claude_normalize_event,
                flags=_claude_flags,
                discover_models=_discover_claude,
                owns_model=_claude_owns_model,
                default_roles={
                    Role.ORCHESTRATOR,
                    Role.PRODUCT_MANAGER,
                    Role.ARCHITECT,
                    Role.QA,
                    Role.DESIGNER,
                    Role.DEVOPS,
                },
            ),
            Provider(
                key=_CODEX,
                runner=CodexRunner(
                    normalize_event=_codex_normalize_event,
                    flag_resolver=_codex_flags,
                ),
                normalize_event=_codex_normalize_event,
                flags=_codex_flags,
                discover_models=_discover_codex,
                owns_model=_codex_owns_model,
                default_roles={Role.WORKER},
            ),
        ]
    )


_DEFAULT_REGISTRY: ProviderRegistry | None = None


def provider_registry() -> ProviderRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = build_provider_registry()
    return _DEFAULT_REGISTRY
