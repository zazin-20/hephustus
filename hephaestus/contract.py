"""ExecutionContract — the governed spec for a single agent run."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace


@dataclass(frozen=True)
class ExecutionContract:
    actor: str
    context: str
    scope: str
    model: str | None
    effort: str | None
    tools: list[str]
    prompt: str = ""
    role: str = ""
    tool: str = ""
    issue_id: str | None = None
    cwd: str | None = None
    resume: str | None = None
    allowed_paths: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    actual_model: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)

    def with_updates(self, **changes) -> "ExecutionContract":
        return replace(self, **changes)
