"""Role-based static routing (spec/architecture.md §5.3) and directive locations.

Routing is intentionally static and role-based, not task-based — simple and
debuggable for the MVP.
"""
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
    CLAUDE = "claude"
    CODEX = "codex"


ROLE_TOOL: dict[Role, Tool] = {
    Role.ORCHESTRATOR: Tool.CLAUDE,
    Role.PRODUCT_MANAGER: Tool.CLAUDE,
    Role.ARCHITECT: Tool.CLAUDE,
    Role.WORKER: Tool.CODEX,
    Role.QA: Tool.CLAUDE,
    Role.DESIGNER: Tool.CLAUDE,
    Role.DEVOPS: Tool.CLAUDE,
}

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


def tool_for(role: Role | str) -> Tool:
    return ROLE_TOOL[Role(role)]
