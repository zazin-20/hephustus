from __future__ import annotations

import asyncio

from hephaestus.contract import ExecutionContract
from hephaestus.integration.providers import (
    Provider,
    ProviderRegistry,
    build_provider_registry,
)
from hephaestus.integration.runners import AgentEvent, AgentTask, EchoRunner
from hephaestus.integration.service import AgentService


def _contract(**kwargs) -> ExecutionContract:
    defaults = dict(
        actor="node-001",
        node_id="node-001",
        provider="codex",
        tags=["worker"],
        context="thread-001",
        scope="node:node-001",
        model="gpt-5.4",
        effort="medium",
        tools=[],
        prompt="go",
    )
    defaults.update(kwargs)
    return ExecutionContract(**defaults)


def test_builtin_providers_are_registered():
    registry = build_provider_registry()

    assert registry.keys() == {"claude", "codex"}
    assert registry.get("claude").discover_models()["provider"] == "claude"
    assert registry.get("codex").discover_models()["provider"] == "codex"


def test_fake_provider_can_register_and_drive_routing_and_catalog(tmp_path):
    registry = build_provider_registry()
    fake = Provider(
        key="gemini_cli",
        runner=EchoRunner("gemini_cli"),
        normalize_event=lambda raw: AgentEvent("text", raw["message"], raw=raw),
        flags=lambda contract: {"cwd": contract.cwd or "."},
        discover_models=lambda: {
            "provider": "gemini_cli",
            "models": [{"id": "gemini-2.5-pro", "label": "Gemini 2.5 Pro", "efforts": ["low", "high"]}],
        },
        owns_model=lambda model: bool(model and model.startswith("gemini-")),
    )
    registry.register(fake)

    # Routing is model-provider-based now (role removed): the registry resolves a
    # model to its owning provider, and that flows through catalog + service.
    assert registry.provider_for_model("gemini-2.5-pro") == "gemini_cli"
    providers = {group["provider"] for group in registry.catalog()["providers"]}
    assert "gemini_cli" in providers

    service = AgentService(tmp_path, registry=registry)
    provider, _ = service.resolve(
        AgentTask(node_id=None, provider="gemini_cli", tags=["design-system"], prompt="x", model="gemini-2.5-pro")
    )
    assert provider == "gemini_cli"

    async def go():
        return [
            event
            async for event in service.run(
                AgentTask(
                    node_id=None,
                    provider="gemini_cli",
                    tags=["design-system"],
                    prompt="sketch",
                    model="gemini-2.5-pro",
                )
            )
        ]

    events = asyncio.run(go())
    # The runner that ran came from the injected registry — proves the seam end to end.
    assert any("echo:gemini_cli" in event.text for event in events)


def test_resolve_provider_prefers_model_owner_then_first_truthy_fallback():
    registry = build_provider_registry()

    assert registry.resolve_provider("gpt-5.4", "claude") == "codex"
    assert registry.resolve_provider("unknown-model", None, "", "claude", "codex") == "claude"
    assert registry.resolve_provider("unknown-model", None, "") is None


def test_provider_interface_owns_flags_and_event_normalization():
    registry = build_provider_registry()

    claude = registry.get("claude")
    codex = registry.get("codex")

    assert claude.flags(_contract(model="opus", effort="high"))["permission_mode"] == "bypassPermissions"
    event = codex.normalize_event(
        {"type": "item.completed", "item": {"type": "reasoning", "text": "thinking"}}
    )
    assert event.kind == "thinking"
    assert event.text == "thinking"
