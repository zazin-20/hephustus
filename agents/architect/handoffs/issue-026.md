---
issue_id: issue-026
worker: codex
status: done
created: 2026-07-04
reviewed_by: []
---

## Summary

Implemented the single `ProviderRegistry.resolve_provider()` seam from ADR-0002 and routed the four existing inline provider-resolution copies through it without changing caller-side `None` handling.

## Changes

- Added `ProviderRegistry.resolve_provider(model, *fallbacks)` in `hephaestus/integration/providers.py` with the ADR-specified behavior: prefer the owning provider for a recognized model, otherwise return the first truthy fallback, otherwise `None`.
- Replaced the inline provider-resolution chain in `hephaestus/integration/contract_resolution.py` so the sole `ExecutionContract` constructor now uses the registry seam.
- Replaced the inline provider-resolution chains in `AgentService.begin()`, `AgentService.resolve()`, and `AgentService._resolve_node()` so all four call sites now share the same registry-owned rule.
- Added a focused unit test covering the model-hit path, first-truthy-fallback path, and all-empty-fallback path through the public `ProviderRegistry` API.

## Files Changed

- `hephaestus/integration/providers.py`
- `hephaestus/integration/contract_resolution.py`
- `hephaestus/integration/service.py`
- `tests/test_provider_registry.py`
- `agents/architect/handoffs/issue-026.md`

## Verification

- Focused TDD pass:
  `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest tests/test_provider_registry.py -q`
  Result: `4 passed`
- Full suite:
  `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest`
  Result: `210 passed, 5 warnings`

## Notes

- Live `gh issue view 26 --repo zazin-20/hephustus` could not complete from this sandbox because outbound GitHub access is blocked, so implementation followed the provided issue text plus local ADR-0002.
