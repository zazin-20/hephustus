---
issue_id: issue-027
worker: codex
status: done
created: 2026-07-04
reviewed_by: []
---

## Summary

Removed the vestigial `Tool` compatibility enum from the integration layer so provider identity is consistently the registry string key, and switched the CLI provider argument to accept the sorted registered provider keys.

## Changes

- Deleted `Tool`, `PROVIDER_TOOL`, and `tool_for_provider` from `hephaestus/integration/routing.py` while leaving `TAG_DIRECTIVE` unchanged.
- Retyped the integration runner/service seams from `Tool | str` to plain `str`: `AgentRunner.tool`, `EchoRunner`, `ClaudeRunner`, `CodexRunner`, `PreparedRun.tool`, and `AgentService.resolve()`.
- Simplified the service display/routing path so provider strings flow through directly, and changed CLI provider `choices` to `sorted(provider_registry().keys())`.
- Removed `Tool` and its compatibility helpers from `hephaestus/integration/__init__.py` public exports.
- Replaced enum-based test usage with string keys across integration, desktop, workflow, catalog, and contract-resolution tests.
- Added a focused regression test proving a registry-only provider key (`gemini_cli`) is accepted by `main()` without any routing-module edits.

## Files Changed

- `hephaestus/integration/__init__.py`
- `hephaestus/integration/routing.py`
- `hephaestus/integration/runners.py`
- `hephaestus/integration/service.py`
- `tests/test_catalog.py`
- `tests/test_contract_resolution.py`
- `tests/test_desktop_agent.py`
- `tests/test_integration.py`
- `tests/test_provider_registry.py`
- `tests/test_workflow_runtime.py`
- `agents/architect/handoffs/issue-027.md`

## Verification

- Focused TDD pass:
  `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest tests/test_provider_registry.py -q`
  Result: `5 passed`
- Full suite:
  `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest`
  Result: `211 passed, 5 warnings`
- Package grep:
  `C:\Program Files\Git\mingw64\bin\git.exe grep -n "\bTool\b" -- hephaestus`
  Result: no matches
