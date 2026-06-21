"""Tests for ExecutionContract and provider adapters (issue #7)."""
from __future__ import annotations

import pytest
from hephaestus.contract import ExecutionContract
from hephaestus.integration.adapters import claude_flags, codex_flags


def _contract(**kwargs) -> ExecutionContract:
    defaults = dict(
        actor="work-001",
        context="thread-abc",
        scope="issue:007",
        model="claude-sonnet-4-6",
        effort="medium",
        tools=[],
    )
    defaults.update(kwargs)
    return ExecutionContract(**defaults)


def test_execution_contract_defaults():
    c = _contract()
    assert c.actor == "work-001"
    assert c.context == "thread-abc"
    assert c.scope == "issue:007"
    assert c.model == "claude-sonnet-4-6"
    assert c.effort == "medium"
    assert c.tools == []
    assert c.allowed_paths == []
    assert c.disallowed_tools == []


def test_execution_contract_with_tools():
    c = _contract(tools=["write_file", "bash"], allowed_paths=["agents/"], disallowed_tools=["browser"])
    assert c.tools == ["write_file", "bash"]
    assert c.allowed_paths == ["agents/"]
    assert c.disallowed_tools == ["browser"]


def test_claude_flags_default_effort():
    c = _contract(effort="medium")
    flags = claude_flags(c)
    assert "permission_mode" in flags
    assert flags["permission_mode"] == "default"


def test_claude_flags_high_effort_bypasses():
    c = _contract(effort="high")
    flags = claude_flags(c)
    assert flags["permission_mode"] == "bypassPermissions"


def test_claude_flags_allowed_tools():
    c = _contract(tools=["write_file", "read_file"])
    flags = claude_flags(c)
    assert flags["allowed_tools"] == ["write_file", "read_file"]


def test_claude_flags_disallowed_tools():
    c = _contract(disallowed_tools=["browser", "web_search"])
    flags = claude_flags(c)
    assert flags["disallowed_tools"] == ["browser", "web_search"]


def test_claude_flags_cwd_from_scope():
    c = _contract(scope="issue:007", actor="work-001")
    flags = claude_flags(c)
    assert "cwd" in flags


def test_codex_flags_default_effort():
    c = _contract(effort="low")
    flags = codex_flags(c)
    assert flags["sandbox"] is True
    assert flags["approval_policy"] == "auto"


def test_codex_flags_high_effort():
    c = _contract(effort="high")
    flags = codex_flags(c)
    assert flags["sandbox"] is False
    assert flags["approval_policy"] == "manual"


def test_codex_flags_medium_effort():
    c = _contract(effort="medium")
    flags = codex_flags(c)
    assert flags["sandbox"] is True
    assert flags["approval_policy"] == "auto"


def test_codex_flags_working_dir():
    c = _contract()
    flags = codex_flags(c)
    assert "working_dir" in flags
