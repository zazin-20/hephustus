"""Agent integration layer (spec/architecture.md §5)."""
from hephaestus.contract import ExecutionContract
from hephaestus.integration.routing import (
    TAG_DIRECTIVE,
    PROVIDER_TOOL,
    Tool,
    tool_for_provider,
)
from hephaestus.integration.context import SessionContext, build_session_context
from hephaestus.integration.runners import (
    AgentEvent,
    AgentRunner,
    AgentTask,
    ClaudeRunner,
    CodexRunner,
    EchoRunner,
    build_codex_argv,
)
from hephaestus.integration.service import AgentService, default_runners

__all__ = [
    "Tool", "tool_for_provider", "PROVIDER_TOOL", "TAG_DIRECTIVE",
    "ExecutionContract",
    "SessionContext", "build_session_context",
    "AgentTask", "AgentEvent", "AgentRunner",
    "EchoRunner", "ClaudeRunner", "CodexRunner", "build_codex_argv",
    "AgentService", "default_runners",
]
