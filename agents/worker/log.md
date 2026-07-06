## 2026-07-07

- Built issue `#28` node authoring without expanding scope: added DAL `update_node`, widened the desktop bridge and JS API to the full `Node` contract, and added shared desktop create/edit forms in the coordinator roster and workflow-canvas palette.
- Kept `context_policy` plumbed end-to-end but disabled in the UI per the issue, preserving existing 7-argument node-create callers.
- Verification: test count moved from `211` to `213`; full backend suite passed with `213 passed`. Frontend build command was attempted but blocked because `frontend/node_modules` is missing and `vite` is unavailable in this worktree.
