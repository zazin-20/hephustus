"""Provider-backed model and effort catalog."""
from __future__ import annotations

from hephaestus.integration.providers import (
    _CODEX_CACHE,
    build_provider_registry,
    provider_registry,
)


def discover_claude() -> dict:
    return build_provider_registry().get("claude").discover_models()


def discover_codex() -> dict:
    return build_provider_registry().get("codex").discover_models()


def catalog() -> dict:
    return provider_registry().catalog()


def provider_for_model(model: str | None) -> str | None:
    return provider_registry().provider_for_model(model)
