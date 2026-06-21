"""Agent integration layer (spec/architecture.md §5).

Role-based static routing (§5.3) to two backends:
  - Claude Code via `claude-agent-sdk`  (Orchestrator, PM, Architect, QA, Designer, DevOps)
  - Codex via `codex exec` subprocess   (Worker)

The pure parts — routing, OKF context assembly, the session registry — are
testable without any external dependency. The runner backends are thin, guarded
adapters; an EchoRunner exercises the whole path offline.
"""
from hephaestus.integration.routing import (
    ROLE_DIRECTIVE,
    ROLE_TOOL,
    Role,
    Tool,
    tool_for,
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
from hephaestus.integration.service import AgentService, SessionRegistry, default_runners

__all__ = [
    "Role", "Tool", "tool_for", "ROLE_TOOL", "ROLE_DIRECTIVE",
    "SessionContext", "build_session_context",
    "AgentTask", "AgentEvent", "AgentRunner",
    "EchoRunner", "ClaudeRunner", "CodexRunner", "build_codex_argv",
    "AgentService", "SessionRegistry", "default_runners",
]
