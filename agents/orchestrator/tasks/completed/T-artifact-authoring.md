---
task: T-artifact-authoring
role: worker
status: completed
created: 2026-07-07
owner: orchestrator
---

# Task: Artifact authoring — author an artifact definition + connect it to a node

Follow-on to #28. PM framed → Architect grilled + spec'd → Worker implements.

**Issue:** [#29](https://github.com/zazin-20/hephustus/issues/29) (opened
2026-07-07). Spec of record: `agents/architect/issues/DRAFT-artifact-authoring.md`.
Grill record: `agents/product-manager/todo/artifact-spec-authoring.md`.

**Dispatch:** one `codex:codex-rescue` Worker in worktree
`.claude/worktrees/issue-029-artifact-authoring` on branch
`feat/029-artifact-authoring` (off main `a850c72`).

**Scope (3 layers):** `store/artifacts.py` (thin `artifact_id → path` index) +
`okf_layout.artifacts_dir()` → id-resolution seam in `context.py`/
`workflow_runtime.py` (backward-compat with #28 paths) + Bridge/`api.js` CRUD →
Create/Edit Artifact UI + catalog + node-form artifact picker. **No gatekeeper
change** — runtime already injects (`context.py:187`) + checks (`WF-OUT-*`).

**v1 acceptance:** author an artifact and connect it to a node. Deferred:
`matches`/`has_field` predicates, live preview, external sanity-checkers.

**Guardrails:** TDD; product code only in the named surfaces; no close/merge/push
without user confirm. Status stays open until built + Architect-reviewed + (QA).

**DONE 2026-07-07** — Worker implemented (216 backend tests, +3; vite build green,
52 modules), Architect handoff review APPROVED (`0eb566e`; Coordinator +364 confirmed
additive, id-resolution fallback test-proven, no gating change). Impl committed
`d833d4a`. Non-blocking carry-forward: `Bridge._coerce_artifact_headings` forwards
`min_items` verbatim (DAL clamps <1 but not a stray string) — future hardening, no
live path hits it.
