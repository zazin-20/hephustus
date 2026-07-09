---
task: T-prd-to-issues
role: architect
status: completed
created: 2026-07-09
owner: orchestrator
---

# Task: Ground the 3 PRDs against the codebase and decompose into issues

## Goal
Architect reads the three approved PRDs (integration order per
`agents/architect/prds/index.md`):

1. `PRD-01-canvas-runtime-command-center.md` — canvas as primary runtime
   surface; console folds into graph-native run controls + node drill-in
2. `PRD-02-artifact-flow-preflight-context.md` — artifact movement, graph
   validity (preflight), compiled context inspectability
3. `PRD-03-learning-library-and-secondary-runtime.md` — correction/learning
   surfaces, structured inventory/templates, secondary ad-hoc runtime

…compares each against the current state of the codebase (`hephaestus/` core,
`frontend/src/`), and runs `/to-issues` to decompose into
independently-grabbable tracer-bullet issues on the GitHub tracker
(`zazin-20/hephustus`).

## Context the Architect must reconcile
- `agents/architect/issues/DRAFT-graph-runtime-convergence.md` — two flags
  filed after #30 (Console → drill-in per ADR-0003 §7.9; spawn-card vs graph
  gatekeeper contradiction) that overlap PRD-01 scope.
- #30 already rehomed Coordinator into Library + Console (peer tab) — PRD-01
  supersedes the Console-as-peer-tab arrangement.
- Design language + canonical component library exist at
  `agents/design-system/` (component-library.html, 42 units) — issues touching
  UI should reference it as the implementation guide, not re-design.
- Known-deferred structural items NOT to fold in silently: T-dynamic-fanout
  (runtime-variable fan-out), T-prompt-compression (context_policy adapter).

## Dispatch
- 2026-07-09: spawned Architect-role agent (subagent_type `claude`, fresh
  context) with role directive `agents/architect/architect.md`, the PRD set,
  comparison mandate, and /to-issues instruction. Environment guardrails from
  `spawn-environment.md` included (PowerShell for bare git/gh; no bare
  python).
- 2026-07-09: agent hit the API session limit after completing ground-truthing
  but BEFORE cutting any issues (last note: tracker-state check pending to
  avoid duplicate numbering). No tracker writes occurred.
- 2026-07-09: resumed the SAME agent via SendMessage (context intact — gap
  analysis preserved) with instructions to check tracker state, run
  /to-issues in PRD integration order, honor deferred-scope exclusions, and
  log to `agents/architect/log.md`.

## Done when
- Issues exist on the tracker in integration order with PRD traceability.
- Architect has logged its slice to `agents/architect/log.md`.
- Orchestrator moves this file to `tasks/completed/`.
