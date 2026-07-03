"""Provider routing and known tag directive locations."""
from __future__ import annotations

from enum import Enum


class Tool(str, Enum):
    CLAUDE = "claude"
    CODEX = "codex"


PROVIDER_TOOL: dict[str, Tool] = {
    Tool.CLAUDE.value: Tool.CLAUDE,
    Tool.CODEX.value: Tool.CODEX,
}

TAG_DIRECTIVE: dict[str, str] = {
    "orchestrator": "orchestrator/claude.md",
    "product-manager": "product-manager/claude.md",
    "architect": "architect/architect.md",
    "worker": "worker/claude.md",
    "qa": "qa/claude.md",
    "design-system": "design-system/claude.md",
    "devops": "devops/index.md",
}


def tool_for_provider(provider: str) -> Tool:
    return PROVIDER_TOOL[str(provider)]
