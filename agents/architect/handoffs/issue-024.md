---
issue_id: issue-024
worker: codex
status: done
created: 2026-07-04
reviewed_by: []
---

## Summary

Implemented the distillation loop so trace-emitted `distillation_candidate` markers are captured into the Correction Box with provenance, human promotion freezes them into scoped rules, and promoted directives appear in later runs through the layered constitution context.

## Changes

- Added trace-marker capture into the corrections store, including source trace/run/node provenance and promotion metadata.
- Added correction promotion into frozen rules with `(topic_key, scope)` supersede behavior, soft-disable history, and confirmer tracking.
- Extended the frozen-rule schema to preserve provenance and supersede chains while keeping only active rules in normal context assembly.
- Hooked run completion to capture distillation candidates automatically from trace markers.
- Limited constitution injection to `directive` rules so `promote_to_rule` stays stored but does not leak into prompt context.
- Added TDD coverage for end-to-end candidate capture/promotion/context injection and for supersede/audit behavior.

## Files Changed

- `hephaestus/handoff.py`
- `hephaestus/integration/context.py`
- `hephaestus/integration/service.py`
- `hephaestus/store/corrections.py`
- `hephaestus/store/db.py`
- `hephaestus/store/frozen_rules.py`
- `tests/test_corrections.py`
- `tests/test_integration.py`

## Verification

- Focused red/green pass:
  `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest tests/test_corrections.py tests/test_integration.py -k "distillation or promote"`
- Affected surface:
  `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest tests/test_corrections.py tests/test_frozen_rules.py tests/test_store.py tests/test_handoff.py tests/test_integration.py`
- Full suite:
  `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe -m pytest`
  Result: `199 passed`

## Notes

- Live `gh issue view 24 --repo zazin-20/hephustus` could not run here because outbound GitHub access is blocked by the sandbox, so implementation followed the provided issue body plus local design docs.
- `git add` / `git commit` were blocked by worktree metadata permissions (`.git/worktrees/issue-024-distillation-loop/index.lock: Permission denied`), so the code is complete in the working tree but not locally committed from this environment.
