---
title: Architect
role: architect
updated: 2026-07-04
owner: architect
---

# Architect

Navigation page for the Architect role.

The Architect owns **system design, issue specs, handoffs, architecture
invariants, and final PRD storage**. It turns product intent into buildable
issue specs, and reviews worker handoffs before QA.

## Contents

| Path | Holds |
|---|---|
| `architect.md` | The Architect directive (behavior contract) |
| `architecture.md` | System architecture — control plane over AI providers |
| `issue-dag.md` | Issue dependency graph + agent-ownership rules |
| `issues/` | Per-issue specs + `index.md` rollup (`completed/` when closed) |
| `handoffs/` | Worker handoff records (`completed/` when closed) |
| `prds/` | Final PRD storage |
| `briefs/` | Reusable briefs handed to downstream roles |
| `discussion/` | Design discussion notes |
| `plans/` | Implementation / sequencing plans |
| `research/` | Investigations feeding design decisions |
| `log.md` | Architect-local change log |

## Code-enforced paths

These locations are the OKF tree shape resolved by `hephaestus/okf_layout.py`
(`issue_path`, `issues_index_path`, `handoff_path`); do not relocate them. The
paths are code-enforced; the former `S-00x` rules that checked their *contents*
were removed 2026-06-23 (governance is now user-authored specs + the G-rules):

- `issues/{issue_id}.md`, `issues/index.md`
- `handoffs/{issue_id}.md`

See [../index.md](../index.md) for the full pipeline.
