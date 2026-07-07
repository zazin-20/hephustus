---
title: Artifact-spec authoring UI — open product decisions
role: product-manager
status: resolved
resolved: 2026-07-07
created: 2026-07-07
owner: product-manager
handoff_to: architect
---

# Artifact-spec authoring UI — open decisions

## Problem
Post-#28 a node's `outputs` can bind to an artifact-spec **path** from the UI,
but the spec file itself — the predicate DSL that defines a "healthy" artifact —
is still hand-authored markdown (`## Predicates` with `non_empty(...)`,
`min_items(...)`, `matches(...)`, etc.). The guardrail is **bindable but not
authorable** in-app. Breaks "everything user-authored, nothing static" one layer
below where #28 stopped.

## User (proposed)
The **workflow author** (same persona as #28), not a developer. Wants to express
"the PRD out of this node needs real user stories and ≥2 release criteria"
without writing `min_items("Release Criteria", 2)` in a file.

## Open decisions to grill (for the Architect)
1. **Storage model** — specs as first-class **stored/catalogued/reusable
   objects** (new `store/` DAL + Bridge, like nodes) vs **files-in-tree** the UI
   reads/writes by path. PM lean: stored + reusable (one PRD-spec bound by many
   nodes; mirrors #28's reusable-object thrust). Bigger build.
2. **v1 surface** — full predicate builder (all six predicate types +
   `## Good Looks Like` exemplar) vs an 80% **starter** (sections + non-empty +
   min-items; defer regex/field). PM lean: starter.
3. **Live preview** — form runs `check_artifact` against a sample doc for live
   pass/fail while authoring: in v1 or fast-follow?

## Not being decided here
Whether this is standalone or the first slice of a broader "author the guardrail
layers" push (the **constitution** has the same file-authored gap). PM lean:
scope spec-authoring standalone; let it set the pattern.

## Resolution (grill, 2026-07-07 — Architect)
1. **Storage** → folder-of-markdown = source of truth; thin `store/artifacts.py`
   index (`artifact_id → path, name, tags`); node binds by id (backward-compat
   with #28 literal paths). NOT relational content — user wants md for agent-
   readability, user editing, git diffs, and future external sanity-checkers
   (sphinx-style).
2. **v1 checks** → required headings (`has_section`/`non_empty`) + `min_items`;
   defer `matches`/`has_field`.
3. **Live preview** → deferred (fast-follow).
- **Key finding:** the runtime already does BOTH halves — `context.py:187` injects
  the artifact into the producing node; `WF-OUT-*` checks it on exit. v1 = authoring
  UI + thin index + id-resolution only; **no gatekeeper change.**
- **v1 acceptance:** *can the user author an artifact and connect it to a node.*
- Spec authored → `agents/architect/issues/DRAFT-artifact-authoring.md`; DAG-placed.
  Awaiting user approval to open issue → dispatch one Worker.
