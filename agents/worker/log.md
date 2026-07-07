## 2026-07-07

- Built issue `#28` node authoring without expanding scope: added DAL `update_node`, widened the desktop bridge and JS API to the full `Node` contract, and added shared desktop create/edit forms in the coordinator roster and workflow-canvas palette.
- Kept `context_policy` plumbed end-to-end but disabled in the UI per the issue, preserving existing 7-argument node-create callers.
- Verification: test count moved from `211` to `213`; full backend suite passed with `213 passed`. Frontend build command was attempted but blocked because `frontend/node_modules` is missing and `vite` is unavailable in this worktree.

## 2026-07-07

- Built issue `#29` artifact authoring without expanding scope: added the typed artifact DAL at `hephaestus/store/artifacts.py`, added `agents/artifacts/` to the OKF layout, and resolved node `inputs`/`outputs` entries by `artifact_id` before falling back to literal paths.
- Widened the desktop bridge and `frontend/src/api.js` with artifact CRUD, added a first-class artifact catalog/form in the coordinator, and updated node input/output editors to accept either an authored artifact id or a literal path.
- Key decisions: kept the DB row as a thin index only, composed the markdown file as the source of truth, inferred editable heading rules back from `## Predicates`, and preserved existing `#28` literal-path behavior unchanged.
- Verification: targeted red phase failed first with `3` collection errors, targeted green phase passed with `47 passed`, full backend suite passed with `216 passed`, and the frontend production build passed after `npm --prefix frontend ci`.

## 2026-07-07

- Built issue `#30` without expanding scope: retired the Coordinator view by rehoming the catalog into new `Library.jsx`, rehoming the single-node interaction surface into new `Console.jsx`, updating `App.jsx` nav/default view, and deleting `frontend/src/components/Coordinator.jsx`.
- Kept the reorganization frontend-only: product-code changes stayed inside `frontend/src/**`; no Python, bridge behavior, DAL, or tests were touched.
- Preserved reachability for every moved capability: node CRUD including delete, artifact CRUD including delete, artifact detail pane, node picker, thread list, transcript copy, include/exclude turns, trace panel, spawn card, and message composer.
- Verification: `"/c/Program Files/nodejs/npm.cmd" --prefix frontend ci` and `"/c/Program Files/nodejs/npm.cmd" --prefix frontend run build` both passed; a requested Git commit was attempted but blocked by `index.lock` permission denial in the worktree.
