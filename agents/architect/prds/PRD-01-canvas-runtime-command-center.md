---
title: PRD 01 - Canvas Runtime Command Center
status: ready-for-agent
updated: 2026-07-08
owner: architect
integration_order: 1
---

## Problem Statement

Hephaestus already executes workflows as graphs, but the UI still tells a split
story. The canvas exists without feeling like the command center, while console
behavior still preserves the older "talk to one agent" mental model. Users cannot
stay centered on the graph during execution because the most important runtime
information and actions are fragmented.

## Solution

Make the canvas the primary authored and runtime operating surface. Keep a strong
Author Mode and Run Mode on the same canvas, default live execution to the graph,
and move runtime observation into a serious selected-node inspector plus inline
graph controls. The graph itself becomes the primary story for active,
blocked, waiting-human, awaiting-confirmation, passed-gate, failed-gate, and
revision states.

## User Stories

1. As a workflow author, I want the canvas to be the center of gravity, so that the product communicates that workflows run as graphs.
2. As a workflow author, I want explicit Author Mode and Run Mode, so that editing and operating do not blur into one overloaded surface.
3. As an operator, I want Run Mode to foreground execution state on the graph, so that I can understand a run without leaving the canvas.
4. As an operator, I want the active node to be visually obvious, so that I can track progress at a glance.
5. As an operator, I want blocked nodes to be visually distinct, so that I can quickly locate the point of failure.
6. As an operator, I want waiting-for-human nodes to be visually distinct from blocked nodes, so that I know whether the system needs input or repair.
7. As an operator, I want awaiting-edge-confirmation states to appear directly on the edge, so that control decisions feel native to the graph.
8. As an operator, I want gate pass and fail state visible on the node and inspector, so that compliance status stays tied to execution.
9. As a reviewer, I want produced artifact previews to appear on the graph during a run, so that outputs are legible in the execution path.
10. As an operator, I want resume, pause, confirm, reject, and override actions to appear inline first, so that I do not have to hunt through a side panel for primary controls.
11. As a workflow author, I want the graph to lock while a run is active, so that the live run executes against a stable snapshot.
12. As an operator, I want the UI to distinguish Live Run Snapshot from Current Draft, so that I never confuse the executing graph with in-progress edits.
13. As an operator, I want runtime controls active only on the live snapshot, so that I do not accidentally operate on a draft.
14. As an author, I want draft edits to auto-save continuously, so that preparing the next run does not depend on a publish step.
15. As an author, I want Run Draft to always trigger a fresh preflight, so that every new run starts from validated state.
16. As an operator, I want a selected node to open one serious inspector rail, so that transcript, trace, gates, context, artifacts, and corrections live in one place.
17. As an operator, I want transcript and trace to remain separate inspector sections, so that narrative output and tool evidence do not mix.
18. As an operator, I want violations and corrections inline at the point of failure and summarized in the inspector, so that remediation stays grounded in the failing run state.
19. As an operator, I want the inspector to support pinning, so that I can freeze one node's details while exploring related graph elements.
20. As an operator, I want the inspector to show when pinned content is stale relative to the active run, so that I do not mistake frozen context for live context.
21. As a power user, I want keyboard navigation between related graph elements, so that inspecting graph state is efficient.
22. As a user, I want a compact legend and concern filters, so that markers stay learnable even in dense graphs.
23. As a user, I want filters to dim non-matching elements instead of hiding them, so that I preserve graph context while focusing attention.
24. As a user, I want filter state to persist for my current session, so that repeated inspection is less tedious.
25. As a user, I want the legend to be mode-aware, so that Author Mode and Run Mode each explain only the markers that matter there.
26. As a user, I want the legend to stay visible by default but collapsible, so that learning support is available without permanently occupying space.
27. As a user, I want Author Mode and Run Mode to remember separate viewports, so that switching modes does not disrupt the way I work.
28. As an operator, I want ask-edge rejection to pause the workflow instead of killing it, so that revision loops are first-class.
29. As an operator, I want rejection to require a reason, so that upstream revision has actionable context.
30. As an operator, I want revision attempts grouped under one node run with visible attempt counts, so that retries remain legible instead of exploding the history.

## Implementation Decisions

- Canvas is the primary runtime surface. Console functionality is re-homed into graph-native node drill-in and, later, a clearly secondary ad-hoc runner.
- Author Mode and Run Mode remain explicit, persistent modes on one canvas rather than separate top-level products.
- Run Mode defaults to the live run snapshot.
- Active graph execution runs against a frozen snapshot; the user may continue editing the draft in parallel, but that draft is non-operative until a new run starts.
- Draft editing is auto-saved continuously. There is no separate publish workflow in v1.
- Runtime controls belong inline on nodes and edges first. The inspector provides deeper explanation, history, and rationale capture.
- The selected-node inspector is a single stacked surface, not a tabbed nest. It includes node contract, input artifacts, output artifact specs, assembled context preview, run transcript, trace/tool calls, gate checklist, produced artifacts, and violations/corrections.
- Transcript and trace are distinct sections.
- Violations/corrections are surfaced inline at the failure point and in an inspector summary that foregrounds unresolved items; resolved history is behind reveal.
- Inspector pinning freezes content while graph exploration continues elsewhere.
- Pinned stale/live indication escalates only when the pinned selection has new or blocking significance.
- Ask edges are graph-native controls. Confirm/reject lives on the edge capsule; inspector carries detail.
- Rejecting an ask edge pauses the workflow for upstream revision, requires a structured reason, and may include an optional note.
- Revision attempts nest beneath one node execution lineage. Nodes with revision loops show compact attempt-count markers and escalate visually with repeated retries.
- Excessive retries automatically surface correction candidates.
- Concern filters in v1 are limited to runtime blockers, validation issues, learning candidates, and outdated nodes.
- Filters dim non-matching elements rather than hiding them.
- Legend collapse preference and filter state persist per user session; shareable filter state is out of scope.
- Auto-follow of live execution is explicitly deferred.

## Testing Decisions

- Good tests assert externally visible runtime behavior: mode gating, live-vs-draft protection, inline action availability, inspector stale indicators, and revision loop state transitions.
- Test the graph runtime presentation state as a state machine instead of testing incidental component structure.
- Test the selected-node inspector contract at the section/data level, not CSS specifics.
- Test filter behavior by asserting dimming and persistence semantics, not DOM ordering details.
- Test revision-loop flows end-to-end: reject with required reason, workflow pause, upstream revision attempt creation, attempt counter increment, and resumed execution.
- Prior art should come from existing workflow runtime tests plus current canvas rendering tests, expanding them toward richer run-state coverage.

## Out of Scope

- Auto-follow camera behavior.
- Mixed-type multi-select across nodes, edges, and artifact capsules.
- Shareable or URL-addressable filter state.
- A separate publish/release step for drafts.
- Any return to Console as a peer runtime tab.

## Further Notes

- This PRD intentionally lands before deeper artifact-flow and library work because it establishes the operating model the rest of the UI must plug into.
- The canvas legend, inspector, and run-state vocabulary should use ADR-0003 terminology consistently.
