"""Role definitions and default provider routing."""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ORCHESTRATOR = "orchestrator"
    PRODUCT_MANAGER = "product-manager"
    ARCHITECT = "architect"
    WORKER = "worker"
    QA = "qa"
    DESIGNER = "design-system"
    DEVOPS = "devops"


class Tool(str, Enum):
    """Compatibility enum for built-in providers."""

    CLAUDE = "claude"
    CODEX = "codex"


# Directive file per role, relative to the agents/ tree (from index.md registry).
ROLE_DIRECTIVE: dict[Role, str] = {
    Role.ORCHESTRATOR: "orchestrator/claude.md",
    Role.PRODUCT_MANAGER: "product-manager/claude.md",
    Role.ARCHITECT: "architect/architect.md",
    Role.WORKER: "worker/claude.md",
    Role.QA: "qa/claude.md",
    Role.DESIGNER: "design-system/claude.md",
    Role.DEVOPS: "devops/index.md",
}


def tool_for(role: Role | str, *, registry=None) -> Tool | str:
    from hephaestus.integration.providers import provider_registry

    provider = (registry or provider_registry()).provider_for_role(role)
    try:
        return Tool(provider)
    except ValueError:
        return provider
