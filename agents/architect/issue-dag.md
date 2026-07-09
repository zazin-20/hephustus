---
title: Issue DAG
updated: 2026-07-09
owner: architect
---

# Issue DAG — PRD decomposition wave (#31–#47)

Dependency graph for the 2026-07-09 wave cut from the three approved PRDs
(`prds/PRD-01…03`). All issues are AFK, labeled `ready-for-agent`, and carry
their own spec sections on GitHub (the issue is the spec of record). One
dedicated owner per issue; respect `Blocked by` before grabbing.

## PRD-01 — Canvas Runtime Command Center

| # | Title (short) | Blocked by |
|---|---|---|
| #31 | Run-session controls (confirm / override / human input inline) | — |
| #32 | Selected-node inspector (stacked rail, pinning, stale) | — |
| #33 | Run-state presentation (state vocabulary, legend, concern filters) | — |
| #34 | Live Run Snapshot vs Current Draft (auto-save, Run Draft) | #31 |
| #35 | Ask-edge rejection + revision attempt lineage | #31, #34 |
| #36 | Dissolve Console into node drill-in; retire role spawn card | #32 |

## PRD-02 — Artifact Flow, Preflight, Context

| # | Title (short) | Blocked by |
|---|---|---|
| #37 | Artifact-identity edges; remove literal-path fallback | — (after PRD-01 wave by integration order) |
| #38 | Artifact flow visuals (capsules, ports, edge inspector) | #37, #32 |
| #39 | Binding invalidation (semantic vs rename) | #37 |
| #40 | Preflight engine + persistent dock | #37, #34 |
| #41 | Compiled context preview (read-first) | #32 |
| #42 | Presentation layer (wire editing, snap, align/distribute) | #38 |

## PRD-03 — Learning, Library, Secondary Runtime

| # | Title (short) | Blocked by |
|---|---|---|
| #43 | Learning surface (candidates → frozen rules) + canvas markers | #33 |
| #44 | Library typed inventory (Skills, Providers/Engines, Frozen Rules) | #43 |
| #45 | Pinned node versions + semantic update review | #33 |
| #46 | Workflow templates (placeholder red-preflight gating) | #40, #44 |
| #47 | Secondary ad-hoc runner (one-node graph) | #31, #36 |

## Open wave

Immediately grabbable (no blockers): **#31, #32, #33, #37** (#37 nominally
after the PRD-01 wave for integration order, but technically independent).

## Deferred boundaries (do not expand into these)

- **Dynamic fan-out** (runtime-variable node instances) — user-deferred;
  #38/#35/#46 carry explicit non-goals.
- **Prompt/context compression** (`context_policy` adapter / Headroom seam) —
  user-deferred; #41 carries the explicit non-goal.
