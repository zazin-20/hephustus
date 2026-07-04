"""Agent integration layer (spec/architecture.md §5)."""
from hephaestus.contract import ExecutionContract
from hephaestus.integration.routing import TAG_DIRECTIVE
from hephaestus.integration.context import SessionContext, build_session_context
from hephaestus.integration.contract_resolution import resolve as resolve_execution_contract
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
    "TAG_DIRECTIVE",
    "ExecutionContract",
    "SessionContext", "build_session_context",
    "resolve_execution_contract",
    "AgentTask", "AgentEvent", "AgentRunner",
    "EchoRunner", "ClaudeRunner", "CodexRunner", "build_codex_argv",
    "AgentService", "default_runners",
]
