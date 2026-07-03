"""Compatibility wrappers for provider-specific contract flags."""
from __future__ import annotations

from hephaestus.contract import ExecutionContract
from hephaestus.integration.providers import provider_registry


def claude_flags(contract: ExecutionContract) -> dict:
    return provider_registry().get("claude").flags(contract)


def codex_flags(contract: ExecutionContract) -> dict:
    return provider_registry().get("codex").flags(contract)
