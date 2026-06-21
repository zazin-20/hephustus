"""ExecutionContract — the governed spec for a single agent run."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExecutionContract:
    actor: str
    context: str
    scope: str
    model: str
    effort: str
    tools: list[str]
    allowed_paths: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
