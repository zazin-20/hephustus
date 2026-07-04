---
title: Architect Log
updated: 2026-07-04
owner: architect
---

# Architect Log

Architect-local change history: design decisions, spec/handoff events, and rule
changes that are narrower than the system-level rollup in
[../log.md](../log.md).

---

## 2026-07-03 — Workspace restructure

Architect artifacts consolidated under `agents/architect/`:

- `architecture.md`, `architecture-coordinator.md` moved in from repo root.
- `prd-coordinator.md` moved to `prds/`.
- `structural.md` moved to `rules/`.
- `issue-dag.md` moved in from `agents/`.
- Added `briefs/`, `discussion/`, `plans/`, `research/`, and
  `issues/completed/`, `handoffs/completed/`.

---

## 2026-07-03 — Wave 1 landed to main; DAG + S-001 wording updated

- Fast-forwarded local `main` to `integration/wave1-014-015-016-017-018`
  (`7d2b8d6`) — #14-18 (glossary, ArtifactSpec checker, marker parser, node
  model, provider registry), already verified 180 tests + frontend green in
  T-008. No re-merge needed; identical tree.
- Closed GitHub issues #14-18 with the merge commit referenced.
- `issue-dag.md` rewritten: #10-18 marked done; #19-25 (governance-engine-revised
  wave 2) added with real `## Blocked by` edges pulled live from GitHub. Open
  wave now is `#19` + `#20` (parallel); `#25` flagged held-for-human (no
  ready-for-agent/AFK label).
- `architect.md` responsibility #2 (Issue specs) rewritten per T-002's
  resolution: the GitHub issue is the spec of record (its body sections are
  the `issues/{id}.md` equivalent); local spec files are now supplementary,
  not required, closing the S-001 process tension T-001 flagged.

---

## 2026-07-04 — Restored after being dropped uncommitted

This entire subtree (this file included) existed only as **uncommitted**
changes on `chore/agents-workspace-restructure` — staged/modified but never
committed — while that branch itself sat 5 waves behind `main`. The
Orchestrator stashed it, later judged the stash "not required" without
separating novel content from stale renames, and dropped it. It was recovered
from the not-yet-garbage-collected stash commit
(`652c80b87c7094d8c0b40c97f7a9315d2f11c45a`) and committed properly this time.
See `agents/orchestrator/spawn-environment.md` and the Orchestrator's
postmortem for the full account.

---

## 2026-07-04 — Doc drift reconciled: S-001..S-006 → governance model

QA's full-surface survey flagged design/README docs still describing the removed
hardcoded `S-001..S-006` structural rule library and a stale test count.
Reconciled against the code (`hephaestus/rules/{base,registry,governance,__init__}.py`,
`index.py`, `dashboard.py`) and `docs/design/governance-engine.md`. Confirmed there is
no `hephaestus/rules/structural.py` and no `S-0xx` IDs remain in product code (the only
`S-00` hit under `hephaestus/` is registry.py's docstring recording the removal). Real
suite size observed: **211 passed** (shared `agents/.venv`).

- **`README.md`** — rewrote the intro to point at `docs/design/governance-engine.md` as
  canonical; fixed the `rules/` tree (`base.py` interface, `governance.py`
  G-001/G-002/G-003 + `ALL_GOVERNANCE_RULES`, `registry.py` generic runner with no
  built-in set); dropped the hardcoded `# 27 tests` count; replaced the
  `Structural rules S-001..S-006 ✅` Status row with the governance model.
- **`structural.md`** — rewrote from the S-001..S-006 rule-library doc into the current
  governance model: `HephaestusRule` interface (now `EvaluationContext`), the generic
  `registry` runner, the three run-time governance rules, and user-authored artifact-spec
  predicates; kept a compact honest **History** section recording the removed six rules.
- **`architecture.md`** — added a "partly superseded" banner (points to governance-engine,
  flags the removed S-rules and the superseded §6.2 posture); rewrote §4's built-in rule
  table/interface to the governance rules; fixed §3.3 link, §6.3 Tier-2 wording, and §7
  Phase-1 scope; bumped frontmatter to v0.2.2 / 2026-07-04.

Product code untouched (docs only). Out-of-scope residual S-rule references remain in the
role docs (`agents/architect/architect.md` + `index.md`, `agents/worker/`, `agents/qa/`)
and other spec docs (`architecture-coordinator.md`, `prd-coordinator.md`, `log.md`) — noted
to the Orchestrator for a follow-up pass.

---

## 2026-07-04 — Follow-up pass: S-rules reconciled across role + coordinator docs

Continued the reconciliation above into the role docs and coordinator specs the
first pass flagged as out of scope. Verified each reference against code
(`hephaestus/rules/{base,registry,governance}.py`, `hephaestus/okf_layout.py`,
`hephaestus/handoff.py`) and `docs/design/governance-engine.md` before rewriting —
no blind deletes.

**Ground truth confirmed:**
- `reviewed_by: architect` is **not code-enforced** — grep found no `reviewed_by`
  in any `.py`. It (was `S-005`) is now a **process convention**.
- The OKF *paths* (`issue_path` / `issues_index_path` / `handoff_path` /
  `qa_evidence_path` / `log_entry_path`) are **still code-enforced** by
  `okf_layout.py`; only the `S-0xx` rule IDs that checked their presence/content
  are gone. Rewrote every path reference to say that accurately.
- Live rules are `G-001`/`G-002`/`G-003` (`governance.py`), run by the generic
  `registry.py` (no built-in set).

**Files reconciled:**
- `agents/architect/architect.md` — resp. #2 (S-001 → convention), #4 (S-005 gate
  → convention; handoff path still code-enforced), #6 (rules → governance model +
  G-rules), References + `updated`.
- `agents/architect/index.md` — `rules/` row + "Code-enforced paths" (paths via
  `okf_layout.py`, S-00x checks removed).
- `agents/worker/claude.md`, `agents/worker/index.md` — S-001 spec-of-record and
  S-002 handoff → conventions; handoff path still code-enforced.
- `agents/qa/claude.md`, `agents/qa/index.md` — S-005 review gate + S-003/S-004
  evidence/log → conventions; evidence path still code-enforced via
  `qa_evidence_path`.
- `architecture-coordinator.md` — §5 module map: `structural.py`/`S-001..S-006`
  line struck through + superseded note; `governance.py` set = G-001..G-003.
- `prd-coordinator.md` — §"Per-profile exit rules": removed the false
  "structural rules unchanged and continue to run" claim + added a superseded
  note; corrections-example `violation` changed from the dead `S-002` to a live
  `G-001`.
- `log.md` (repo root) — historical entries left intact (accurate point-in-time
  history); added a 2026-06-23 removal entry so the log reflects the current
  governance model; bumped `updated`.

`agents/qa/readme.md` left unchanged — its `reviewed_by: architect` mention is an
accurate flow step, not a rule claim.

**Left for the Orchestrator (explicitly out of scope this pass):** stale S-rule
references in `agents/qa/test-plan.md` (line 143 "rule S-003 consumer", line 373
"QA rule S-005"), `agents/orchestrator/tasks/*`, `sample/agents/`, and the
`governance-engine-revised.md` duplicate.

Documentation only — no `.py` touched.

---

## 2026-07-04 — Link-fix pass: structural.md references repointed to repo root

`structural.md` was rewritten into the governance model and lives only at the repo
root; several docs still linked to it via non-existent paths (`rules/structural.md`,
`../architect/rules/structural.md`, `spec/rules/structural.md`). Repointed each
broken link at the real file and verified resolution:

- `agents/architect/architect.md` — resp. #6 inline `rules/structural.md` →
  `../../structural.md`; References bullet `[rules/structural.md](rules/structural.md)`
  → `[structural.md](../../structural.md)`.
- `agents/qa/claude.md` — References `[../architect/rules/structural.md](...)` →
  `[structural.md](../../structural.md)`.
- `index.md` (repo root) — Related Documents `[spec/rules/structural.md](../spec/rules/structural.md)`
  → `[structural.md](structural.md)`; description reworded from "built-in compliance
  rules" to the governance model (user-authored artifact-spec predicates + run-time
  governance G-rules; hardcoded S-001..S-006 removed 2026-06-23).

Left untouched: `log.md` (repo root) line ~31 `spec/rules/structural.md` — inside a
dated historical entry, accurate as point-in-time history. Remaining
`rules/structural.md`/`spec/rules/structural.md` strings now live only in dated
history. Documentation only — no `.py` touched.
