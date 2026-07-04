---
title: QA
role: qa
updated: 2026-07-03
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
| `evidence/` | Per-issue QA evidence, `evidence/{issue_id}.md` (**rule S-003**) |
| `bug-report/` | Filed bug reports |
| `manual_test_snapshots/` | Manual verification snapshots |
| `playwright/` | Playwright browser tests |
| `tests/security/` | Security tests |
| `tests/integration/` | Integration tests |
| `tests/e2e/` | End-to-end tests |

## Code-enforced path

`evidence/{issue_id}.md` is consumed by `hephaestus/okf_layout.py` and rules
**S-003 / S-004 / S-005**. Do not relocate it.

## Gate

QA only starts once the handoff has `reviewed_by: architect` (rule **S-005**).

See [../index.md](../index.md) for the full pipeline.
