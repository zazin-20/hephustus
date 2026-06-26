"""Provider adapters — translate ExecutionContract to native runner flags."""
from __future__ import annotations

from hephaestus.contract import ExecutionContract

_EFFORT_PERMISSION = {
    "low": "default",
    "medium": "default",
    "high": "bypassPermissions",
}

_EFFORT_SANDBOX = {
    "low": True,
    "medium": True,
    "high": False,
}

_EFFORT_APPROVAL = {
    "low": "auto",
    "medium": "auto",
    "high": "manual",
}


def claude_flags(contract: ExecutionContract) -> dict:
    flags: dict = {
        "permission_mode": _EFFORT_PERMISSION.get(contract.effort, "default"),
        "cwd": contract.cwd or _scope_to_cwd(contract.scope),
    }
    if contract.tools:
        flags["allowed_tools"] = list(contract.tools)
    if contract.disallowed_tools:
        flags["disallowed_tools"] = list(contract.disallowed_tools)
    return flags


def codex_flags(contract: ExecutionContract) -> dict:
    return {
        "sandbox": _EFFORT_SANDBOX.get(contract.effort, True),
        "approval_policy": _EFFORT_APPROVAL.get(contract.effort, "auto"),
        "working_dir": contract.cwd or _scope_to_cwd(contract.scope),
    }


def _scope_to_cwd(scope: str) -> str:
    # "issue:007" -> current working dir (no sub-navigation at MVP)
    return "."
