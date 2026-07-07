# DRAFT — Retire the Coordinator view: rehome its parts into Library + Console

> **OPENED as [#30](https://github.com/zazin-20/hephustus/issues/30)
> (2026-07-07).** The `## What to build` / `## Acceptance criteria` /
> `## Blocked by` sections below were used as the issue body verbatim. GitHub
> issue #30 is the definition of done for the Worker.

**Owner:** one dedicated Worker (see `issue-dag.md`)
**Routing:** Architect spec'd; Worker implements; QA verifies.
**Relates to:** ADR-0003 (the node graph is the spine — "Coordinator" is the
superseded pre-graph concept from ADR-0001). Frontend-only.

## What to build

Retire the **Coordinator** view as a concept and **redistribute its
capabilities** so nothing is lost. Today `Coordinator.jsx` is the app's default
tab and uniquely hosts three jobs; the node-graph paradigm (ADR-0003) has no
"Coordinator" concept, and `docs/design/governance-engine.md` does not mention
one. This is a pure **frontend reorganization** — no backend, no bridge, no DAL
change (every method the moved surfaces call already exists).

Ground truth (verified 2026-07-07):
- `Coordinator.jsx` owns: (a) **node CRUD** (list/create/edit/**delete**),
  (b) **artifact CRUD** — the *only* place `ArtifactForm` is mounted (the #29
  authoring surface), (c) a **single-node console** (threads, transcript, trace,
  include/exclude turns, copy, **spawn card**, message composer).
- `WorkflowCanvas.jsx` can *bind* artifacts (`listArtifacts`) and create/edit
  nodes via the palette, but cannot **author artifacts** or **delete** nodes,
  and has no threaded console. So Coordinator cannot simply be deleted.
- `App.jsx` nav = `['coordinator','canvas','code','agent']`, default view
  `coordinator`.
- Shared, reused as-is: `NodeForm.jsx`, `ArtifactForm.jsx`,
  `ArtifactBindingEditor.jsx`.

Scope, three moves:
1. **New `Library` tab (the new default).** A catalog surface hosting BOTH the
   node catalog and the artifact catalog with full CRUD — create/edit via the
   existing `NodeForm`/`ArtifactForm`, plus **delete**. This is the node/artifact
   Nodes|Artifacts toggle + list + detail currently in the left rail and detail
   pane of `Coordinator.jsx`, lifted into `Library.jsx`.
2. **New `Console` tab.** The single-node interaction surface: node picker +
   threads + Conversation panel (include/exclude, copy) + Trace panel +
   Spawn card + message composer — the right-hand column of `Coordinator.jsx`,
   lifted into `Console.jsx`.
3. **Remove Coordinator.** Delete `Coordinator.jsx`, drop the `coordinator`
   entry from `App.jsx` nav, set the default view to `library`, and remove all
   dead imports/state. `WorkflowCanvas` is unchanged (its palette keeps
   add-to-graph + the "New node" shortcut into `NodeForm`).

### Explicitly out of scope
- No backend / bridge / DAL / Python change whatsoever.
- No change to `WorkflowCanvas` behavior beyond it continuing to work.
- No new capability — this only relocates existing ones.

## Acceptance criteria
- The app nav is `Library · Console · Canvas · Code · Agent`; **Library is the
  default landing tab**. `Coordinator` tab is gone.
- **Library** lets a user list/create/edit/**delete** nodes AND
  list/create/edit/**delete** artifacts (reusing `NodeForm`/`ArtifactForm`),
  with the node-list / artifact-catalog refresh behavior intact.
- **Console** lets a user select a node, view its threads, converse
  (send message), see the transcript + trace, toggle turns in/out of context,
  copy the conversation, and act on the spawn card — identical behavior to the
  old Coordinator right pane.
- **Nothing from Coordinator is lost**: every capability (node CRUD incl. delete,
  artifact CRUD, threaded console, spawn card) is reachable in the new tabs.
- `Coordinator.jsx` is deleted; no dead imports, no unreferenced state, no
  console errors. `NodeForm`/`ArtifactForm`/`ArtifactBindingEditor` are reused,
  not duplicated.
- Preview mode (no bridge) still works for every moved surface (mock fallback).
- `npm --prefix frontend run build` is green; bundle size does not grow by more
  than ~10 kB gzip (pure reorganization). The Python suite is untouched and
  stays green. Product code changed only under `frontend/src/**`.

## Blocked by
- **Nothing.** Pure frontend reorg over already-merged work (#28 node authoring,
  #29 artifact authoring). Independent of dynamic fan-out and compression.
