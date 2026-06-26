---
issue_id: issue-013
worker: codex
status: done
created: 2026-06-23
reviewed_by: []
---

## Summary

Made `ExecutionContract` the single live run-configuration seam by routing real runs through the contract path, persisting the final resolved contract, and evaluating governance against the actual executed model.

## Changes

- Routed live run execution through `ExecutionContract` instead of the remaining bypass path.
- Persisted the final contract back onto the `runs` row, including `actual_model`.
- Triggered governance evaluation from completed live runs so `G-002` is enforced against real execution results.
- Extended integration and desktop tests to cover the persisted contract and violation path.

## Files Changed

- `hephaestus/contract.py`
- `hephaestus/store/runs.py`
- `hephaestus/integration/adapters.py`
- `hephaestus/integration/runners.py`
- `hephaestus/integration/service.py`
- `hephaestus/integration/__init__.py`
- `tests/test_contract.py`
- `tests/test_integration.py`
- `tests/test_desktop_agent.py`

## Verification

- Covered by the full suite after the issue wave: `173 passed` via `.\venv\Scripts\python.exe -m pytest --basetemp tmp_pytest\full-after-issue11 -o cache_dir=tmp_pytest\cache-full-after-issue11`.

## Notes

- Issue `#13` depends on the service-owned run preparation introduced in issue `#12`, and was completed after that refactor landed.
