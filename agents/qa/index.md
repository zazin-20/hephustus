---
title: QA
role: qa
updated: 2026-07-04
owner: architect
---

# QA

Navigation page for the QA role.

Owns **verification artifacts, tests, bug reports, and evidence**. QA verifies
work the Architect has reviewed, and produces the evidence that lets an issue be
logged as complete.

## Contents

| Path | Holds |
|---|---|
| `claude.md` | The QA directive |
| `readme.md` | QA process notes |
| `evidence/` | Per-issue QA evidence, `evidence/{issue_id}.md` (code-enforced path via `okf_layout.py`) |
| `bug-report/` | Filed bug reports |
| `manual_test_snapshots/` | Manual verification snapshots |
| `playwright/` | Playwright browser tests |
| `tests/security/` | Security tests |
| `tests/integration/` | Integration tests |
| `tests/e2e/` | End-to-end tests |

## Code-enforced path

`evidence/{issue_id}.md` is the OKF tree location resolved by
`hephaestus/okf_layout.py` (`qa_evidence_path`) — do not relocate it. The path
is still code-enforced; the former `S-003 / S-004 / S-005` rules that checked
evidence/log presence and the review gate were removed 2026-06-23 (governance is
now user-authored specs + the G-rules).

## Gate

QA only starts once the handoff has `reviewed_by: architect`. This is a
**process convention** — the former rule `S-005` that enforced it was removed
2026-06-23; no code checks `reviewed_by` today.

See [../index.md](../index.md) for the full pipeline.
