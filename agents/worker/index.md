---
title: Worker
role: worker
updated: 2026-07-03
owner: architect
---

# Worker

Navigation page for the Worker role.

The Worker is **execution-only**. It consumes an Architect issue spec and
implements it via TDD. It does not invent scope. The Worker runs on **Codex**
(via codex-cc), not Claude Code (see `ROLE_TOOL` in
`hephaestus/integration/routing.py`).

## Contents

| Path | Holds |
|---|---|
| `claude.md` | The Worker directive (routing target for the role) |
| `tdd.md` | TDD playbook (**consumed by `okf_layout.worker_tdd_path()`**) |
| `tests.md` | Test conventions |
| `mock.md` | Mocking / fixture conventions |
| `worker-brief-template.md` | Per-issue brief template, filled before handing to a worker |

## Contract

- One issue spec at a time. Definition of done = the issue's acceptance criteria.
- On completion, leave a handoff at `../architect/handoffs/{issue_id}.md`
  (**rule S-002**).

See [../index.md](../index.md) for the full pipeline.
